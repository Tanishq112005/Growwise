from typing import Any, List, Optional, Dict
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from backend.agent.agent_state import GrowwAgentState
from backend.agent.agents_specialized.base_agent import BaseAgentInterface
from backend.agent.agents_specialized.response_style import SIMPLE_LANGUAGE_RULES, SCOPE_GUARDRAIL
from backend.tools.web_search_tools import search_financial_web

WEBSEARCH_SYSTEM_PROMPT = """You are the Research Agent for Groww GenZ.
You have NO built-in knowledge about finance, investing, products, rates, minimum amounts, rules or news.
Everything you say MUST come from the WEB SEARCH RESULTS given to you below. Nothing else.

GROUNDING RULES (strict):
1. Use only facts that appear in the search results. If a number (minimum amount, return, fee, date, price, lock-in) is not in the
   results, do NOT state it. Say you could not verify it.
2. If the results are thin or disagree with each other, say so plainly and share what the sources actually say.
3. Never invent URLs, titles, quotes or numbers. Cite only sources that appear in the results.
4. Earlier messages in this chat may contain unverified claims. Do not repeat them unless the current results support them.
5. Educational only: never promise or guarantee returns and never tell the user to buy or sell a specific security.
6. Write for a complete beginner (age 20-26). If the user clearly sounds experienced, skip the basics. Follow SIMPLE LANGUAGE below.

RESPONSE FORMAT (Markdown, keep it under about 150 words before Sources):
  🎯 **The Bottom Line**: 1-2 direct sentences that answer the question using only the results.
  📊 **Key Breakdown**: 2-4 bullets with the key facts. Bold the key amounts and names.
  💡 **Next Action**: one clear next step.
  **Sources**: up to 3 lines, each exactly "- [Title](url)" taken only from the results, with no blank lines between them.
  🔤 **Jargon decoder**: last block, only if you used jargon (see SIMPLE LANGUAGE).
""" + SIMPLE_LANGUAGE_RULES + SCOPE_GUARDRAIL

NO_VERIFIED_ANSWER = (
    "🎯 **I couldn't verify that right now.**\n\n"
    "I only answer money questions from live web sources, and the search didn't return anything reliable "
    "(the search service may be down). I won't guess on money matters.\n\n"
    "💡 **Next Action**: Please try again in a minute, or rephrase your question."
)


def _format_results(result: Dict[str, Any]) -> str:
    blocks: List[str] = []
    for index, item in enumerate(result.get("results", []) or [], start=1):
        content = (item.get("content") or "").strip().replace("\n", " ")[:700]
        blocks.append(f"[{index}] {item.get('title')}\nURL: {item.get('url')}\n{content}")
    return "\n\n".join(blocks)


class WebSearchAgent(BaseAgentInterface):
    """
    Research agent. It ALWAYS runs a live web search first (in code, not left to the model's choice)
    and then answers strictly from the returned results, so it cannot answer from model memory.
    """
    def __init__(self, model: Any, tools: Optional[List[Any]] = None):
        # No tools are bound to the model: the search is executed deterministically in execute().
        super().__init__(model=model, tools=tools or [])

    @property
    def system_prompt(self) -> str:
        return WEBSEARCH_SYSTEM_PROMPT

    @staticmethod
    def _last_user_text(messages: List[Any]) -> str:
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
                return str(msg.content)
        return ""

    @staticmethod
    def _run_search(query: str) -> Dict[str, Any]:
        try:
            return search_financial_web.invoke({"query": query, "max_results": 5})
        except Exception as err:  # never let a search failure crash the chat turn
            print(f"[WebSearchAgent] Search failed: {err}")
            return {"status": "error", "results": [], "message": str(err)}

    def execute(self, state: GrowwAgentState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        query = (state.get("search_query") or self._last_user_text(messages)).strip()

        result = self._run_search(query)
        if result.get("status") != "success" or not result.get("results"):
            return {
                "messages": [AIMessage(content=NO_VERIFIED_ANSWER)],
                "guardrail_passed": True,
            }

        grounded_prompt = (
            f"{self.system_prompt}\n\n"
            f"SEARCH QUERY USED: {query}\n\n"
            f"WEB SEARCH RESULTS:\n{_format_results(result)}"
        )
        prompt_messages = [SystemMessage(content=grounded_prompt)]
        prompt_messages.extend(messages)

        response = self.model.invoke(prompt_messages)

        return {
            "messages": [response],
            "guardrail_passed": True,
        }
