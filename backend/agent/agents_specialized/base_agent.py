import json
import uuid
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict
from langchain_core.messages import BaseMessage, ToolMessage
from backend.agent.agent_state import GrowwAgentState

# =====================================================================
# Base Agent Interface: BaseAgentInterface
# =====================================================================
class BaseAgentInterface(ABC):
    """
    Common abstract interface implemented by all specialized agents
    (Goal, MarketData, Education, WebSearch) except the Director agent.
    Provides standard tool binding, prompt injection, automated tool resolution,
    and state execution.
    """
    def __init__(self, model: Any, tools: Optional[List[Any]] = None):
        self.model = model
        self.tools = tools or []
        
        # Bind tools to the model if tools are provided
        if self.tools:
            self.model_with_tools = self.model.bind_tools(self.tools)
        else:
            self.model_with_tools = self.model

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Returns the specific system prompt for this agent."""
        pass

    @staticmethod
    def _extract_text_function_calls(content: str) -> tuple[List[Dict[str, Any]], str]:
        """
        Parses and extracts text-based tool calls emitted by models on OpenRouter
        (e.g., DeepSeek !function_call:{"call": "...", "arguments": {...}}).
        Returns a list of normalized tool calls and the cleaned text content.
        """
        if not isinstance(content, str):
            return [], str(content or "")

        calls: List[Dict[str, Any]] = []
        cleaned_parts: List[str] = []
        idx = 0
        decoder = json.JSONDecoder()

        while idx < len(content):
            pos = content.find("!function_call:", idx)
            if pos == -1:
                cleaned_parts.append(content[idx:])
                break

            cleaned_parts.append(content[idx:pos])
            start = pos + len("!function_call:")
            while start < len(content) and content[start].isspace():
                start += 1

            try:
                obj, end_offset = decoder.raw_decode(content[start:])
                call_name = obj.get("call") or obj.get("name")
                call_args = obj.get("arguments") or obj.get("args") or {}
                if isinstance(call_args, str):
                    try:
                        call_args = json.loads(call_args)
                    except Exception:
                        pass

                if call_name:
                    calls.append({
                        "name": str(call_name),
                        "args": call_args if isinstance(call_args, dict) else {},
                        "id": str(obj.get("id") or f"call_{uuid.uuid4().hex[:8]}")
                    })
                idx = start + end_offset
            except Exception:
                idx = pos + len("!function_call:")

        cleaned_text = "".join(cleaned_parts).strip()
        return calls, cleaned_text

    def invoke_with_tools(
        self,
        prompt_messages: List[BaseMessage],
        injected_args: Optional[Dict[str, Any]] = None,
    ) -> List[BaseMessage]:
        """
        Invokes the model with bound tools and automatically resolves tool calls.
        Executes tools, collects ToolMessages, and re-invokes the model for final synthesis.

        `injected_args` are forced into every tool call whose schema accepts them
        (e.g. {"user_id": ...}). This stops the LLM from guessing or hallucinating
        identifiers and prevents one user's agent from touching another user's data.
        """
        response = self.model_with_tools.invoke(prompt_messages)
        
        # 1. Collect native tool calls
        tool_calls = list(getattr(response, "tool_calls", []) or [])

        # 2. Check and extract text-based function calls (e.g. !function_call:...)
        raw_content = getattr(response, "content", "")
        if isinstance(raw_content, str) and "!function_call:" in raw_content:
            text_calls, cleaned_content = self._extract_text_function_calls(raw_content)
            if text_calls:
                print(f"[BaseAgent] >>> Extracted {len(text_calls)} text-based tool calls from content.")
                tool_calls.extend(text_calls)
                response.content = cleaned_content

        if not tool_calls:
            return [response]

        tool_map = {tool.name: tool for tool in self.tools}
        tool_messages: List[ToolMessage] = []

        for call in tool_calls:
            tool_name = call.get("name")
            tool_args = dict(call.get("args", {}) or {})
            call_id = call.get("id") or str(uuid.uuid4())

            tool_obj = tool_map.get(tool_name)
            if tool_obj and injected_args:
                accepted = set(getattr(tool_obj, "args", {}) or {})
                for key, value in injected_args.items():
                    if key in accepted:
                        tool_args[key] = value
            if tool_obj:
                print(f"[ToolCall] >>> Invoking tool: '{tool_name}' with args: {tool_args}")
                try:
                    result = tool_obj.invoke(tool_args)
                    print(f"[ToolCall] >>> Tool '{tool_name}' completed successfully: {result}")
                except Exception as e:
                    print(f"[ToolCall] >>> Tool '{tool_name}' failed with error: {e}")
                    result = {"error": f"Tool execution failed: {str(e)}"}
            else:
                print(f"[ToolCall] >>> Warning: Tool '{tool_name}' not found in registered tools.")
                result = {"error": f"Tool '{tool_name}' not recognized."}

            tool_messages.append(
                ToolMessage(
                    content=json.dumps(result, default=str),
                    tool_call_id=call_id,
                    name=tool_name or "unknown_tool"
                )
            )

        # Synthesize final user-facing response with tool context
        synthesis_messages = list(prompt_messages) + [response] + tool_messages
        final_response = self.model.invoke(synthesis_messages)

        # Sanitize final response in case model emitted any leftover function call tokens
        if hasattr(final_response, "content") and isinstance(final_response.content, str):
            _, final_cleaned = self._extract_text_function_calls(final_response.content)
            final_response.content = final_cleaned

        return [response, *tool_messages, final_response]

    @abstractmethod
    def execute(self, state: GrowwAgentState) -> Dict[str, Any]:
        """
        Executes the specialized agent logic on the current agent state.
        Returns a dictionary with state updates (e.g. messages, action_card).
        """
        pass
