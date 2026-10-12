import json
import re
from typing import Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel, Field
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
from backend.agent.agent_graph import GrowwAgentGraph
from backend.repositories.chat_repository import ChatRepository
from backend.repositories.user_repository import UserRepository

# Graph nodes whose model-stream tokens are forwarded to the frontend.
# Includes the research-pipeline nodes (gather emits no tokens; coverage and answer do).
AGENT_NODES = {"general", "off_topic", "goal", "answer", "coverage"}


# =====================================================================
# Request Schemas
# =====================================================================
class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User UUID")
    query: str = Field(..., min_length=1, description="User message prompt")
    chat_id: Optional[str] = Field(default="default_chat", description="Conversation session ID")
    capital_amount: Optional[float] = Field(default=None, description="Optional capital amount in INR")


# =====================================================================
# Agent Controller: AgentController
# =====================================================================
class AgentController:
    """
    Controller handling business logic for LangGraph AI agent orchestration,
    SSE streaming generation, synchronous chat turns, and MongoDB chat persistence.
    """
    def __init__(
        self,
        graph_orchestrator: Optional[GrowwAgentGraph] = None,
        chat_repo: Optional[ChatRepository] = None
    ):
        self._graph_orchestrator = graph_orchestrator or GrowwAgentGraph()
        self._chat_repo = chat_repo or ChatRepository()
        self._user_repo = UserRepository()

    @staticmethod
    def _thread_id(user_id: str, chat_id: str) -> str:
        """One LangGraph thread per (user, chat) so a new chat never inherits old context."""
        return f"{user_id}:{chat_id}"

    async def _ensure_user_safe(self, user_id: str) -> None:
        """Creates the guest user doc if missing; never blocks the chat if the DB is down."""
        try:
            await self._user_repo.ensure_user(user_id)
        except Exception as err:
            print(f"[AgentController] Warning: could not ensure user '{user_id}': {err}")

    async def stream_chat(self, payload: ChatRequest) -> StreamingResponse:
        """
        Orchestrates specialized agent routing and streams token chunks via Server-Sent Events (SSE).
        Emits SSE chunks `data: {"token": "..."}\n\n` followed by `data: [DONE]\n\n`.
        """
        user_id = payload.user_id.strip()
        query = payload.query.strip()
        chat_id = (payload.chat_id or "default_chat").strip()
        capital_amount = payload.capital_amount

        if not query:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty.")

        # Chat is only available to registered users — guest sessions are read-only.
        if user_id.startswith("guest_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please sign in to use the Growwise AI copilot."
            )

        async def event_generator() -> AsyncGenerator[str, None]:
            full_response_text = ""
            action_card = None
            intent = "websearch"
            capital_detected = None
            discovered_stocks = []
            input_state: Dict[str, Any] = {
                "messages": [HumanMessage(content=query)],
                "user_id": user_id,
            }
            if capital_amount is not None:
                input_state["capital_amount"] = capital_amount

            try:
                await self._ensure_user_safe(user_id)
                compiled_graph = self._graph_orchestrator.get_compiled_graph(user_id=user_id)
                config = {"configurable": {"thread_id": self._thread_id(user_id, chat_id)}}

                tokens_yielded = 0
                async for event in compiled_graph.astream_events(input_state, config=config, version="v2"):
                    ev_type = event.get("event")
                    node = event.get("metadata", {}).get("langgraph_node")

                    # 1. Detect active agent routing
                    if ev_type == "on_chain_start":
                        chain_name = event.get("name")
                        # Also surface gather/coverage pipeline steps as status events
                        pipeline_labels = {"gather": "Fetching data…", "coverage": "Checking completeness…"}
                        if chain_name in pipeline_labels:
                            yield f"data: {json.dumps({'tool': pipeline_labels[chain_name], 'args': {}})}\n\n"
                        if chain_name in AGENT_NODES:
                            print(f"[AgentController] >>> Active Agent: {chain_name}")
                            yield f"data: {json.dumps({'agent': chain_name})}\n\n"

                    # 2. Detect Tool call invocation
                    elif ev_type == "on_tool_start":
                        tool_name = event.get("name")
                        tool_input = event.get("data", {}).get("input")
                        print(f"[AgentController] >>> Calling Tool: {tool_name} with: {tool_input}")
                        yield f"data: {json.dumps({'tool': tool_name, 'args': tool_input})}\n\n"
                        # If model pre-streamed any intermediate scratchpad text before deciding to call the tool, clear bubble
                        if tokens_yielded > 0:
                            full_response_text = ""
                            tokens_yielded = 0
                            yield f"data: {json.dumps({'clear': True})}\n\n"

                    # 2b. Capture Tool outputs (market data quotes)
                    elif ev_type == "on_tool_end":
                        tool_name = event.get("name")
                        tool_output = event.get("data", {}).get("output")
                        if tool_name in {"get_market_quote", "get_stock_price"} and isinstance(tool_output, dict):
                            if tool_output.get("price") and tool_output.get("status") != "error":
                                discovered_stocks.append(tool_output)

                    # 3. Stream real-time token chunks from the active specialized agent
                    elif ev_type == "on_chat_model_stream" and node in AGENT_NODES:
                        chunk = event.get("data", {}).get("chunk")
                        token_content = getattr(chunk, "content", "") if chunk else ""
                        if token_content and isinstance(token_content, str):
                            # Suppress internal function call leaks from DeepSeek/OpenRouter
                            if "!function_call:" in token_content or "<tool_call>" in token_content:
                                continue
                            full_response_text += token_content
                            tokens_yielded += 1
                            yield f"data: {json.dumps({'token': token_content})}\n\n"

                    # 4. Capture final state elements
                    elif ev_type == "on_chain_end" and event.get("name") == "LangGraph":
                        output = event.get("data", {}).get("output", {})
                        if isinstance(output, dict):
                            action_card = output.get("action_card")
                            intent = output.get("current_intent", "websearch")
                            capital_detected = output.get("capital_amount")
                            if not full_response_text:
                                for msg in reversed(output.get("messages", [])):
                                    if isinstance(msg, AIMessage) and msg.content:
                                        full_response_text = str(msg.content)
                                        break

                # Strip any leftover function call tokens before finalizing
                full_response_text = re.sub(r'!function_call:\s*\{[\s\S]*?\}', '', full_response_text).strip()
                full_response_text = re.sub(r'<tool_call>[\s\S]*?<\/tool_call>', '', full_response_text).strip()

                # Fallback if model yielded nothing
                if not full_response_text:
                    full_response_text = "I couldn't put an answer together just now. Mind asking that again?"
                    yield f"data: {json.dumps({'token': full_response_text})}\n\n"
                elif tokens_yielded == 0:
                    # An agent answered with a fixed message (no model streaming): send it as one chunk.
                    yield f"data: {json.dumps({'token': full_response_text})}\n\n"

                # If no card was generated by node, build stock recommendation card from tools or product suggestion intent
                query_lower = query.lower()
                if not action_card and discovered_stocks:
                    action_card = {
                        "card_type": "stock_recommendation_card",
                        "title": "Live Market Quote",
                        "stocks": [
                            {
                                "symbol": str(s.get("symbol", "")).upper(),
                                "company_name": s.get("name") or s.get("symbol", ""),
                                "price": float(s.get("price", 0.0) or 0.0),
                                "change": f"{float(s.get('percent_change', 0.0) or 0.0):+.2f}%",
                                "currency": s.get("currency", "INR"),
                                "exchange": s.get("exchange", "NSE"),
                            }
                            for s in discovered_stocks
                        ],
                    }
                elif not action_card and any(kw in query_lower for kw in ["suggest", "recommend", "stocks to buy", "products", "good stocks", "best stock", "which stock", "top stock", "buy stock"]):
                    action_card = {
                        "card_type": "stock_recommendation_card",
                        "title": "Suggested Benchmark Stocks",
                        "stocks": [
                            {
                                "symbol": "RELIANCE",
                                "company_name": "Reliance Industries Ltd",
                                "price": 2987.50,
                                "change": "+1.2%",
                                "currency": "INR",
                                "exchange": "NSE",
                                "tag": "Nifty 50 Heavyweight",
                            },
                            {
                                "symbol": "TCS",
                                "company_name": "Tata Consultancy Services",
                                "price": 3452.00,
                                "change": "+0.8%",
                                "currency": "INR",
                                "exchange": "NSE",
                                "tag": "IT Bluechip",
                            },
                            {
                                "symbol": "HDFCBANK",
                                "company_name": "HDFC Bank Ltd",
                                "price": 1678.30,
                                "change": "-0.4%",
                                "currency": "INR",
                                "exchange": "NSE",
                                "tag": "Private Banking Leader",
                            },
                            {
                                "symbol": "ZOMATO",
                                "company_name": "Zomato Ltd",
                                "price": 268.40,
                                "change": "+2.1%",
                                "currency": "INR",
                                "exchange": "NSE",
                                "tag": "High-Growth Gen Z",
                            },
                        ],
                    }

                # Emit generative UI action card if available
                if action_card:
                    yield f"data: {json.dumps({'action_card': action_card})}\n\n"

                # Infer contextual quick-reply pills based on agent intent and user query
                query_lower = query.lower()
                quick_replies = []
                if intent in {"general", "off_topic"}:
                    quick_replies = ["I have ₹500, where do I start?", "RELIANCE share price", "What is a SIP?"]
                elif intent == "goal":
                    quick_replies = ["Show my goals", "How do I increase my progress?"]
                elif intent == "research":
                    if capital_detected:
                        quick_replies = ["Save this as my goal 🎯", "How to start a SIP on Groww?", "Explain this simply"]
                    else:
                        query_lower_local = query.lower()
                        if any(t in query_lower_local for t in ["price", "share", "stock", "nifty", "sensex"]):
                            quick_replies = ["Buy this on Groww 📈", "Latest news on this?", "What is a P/E ratio?"]
                        else:
                            quick_replies = ["How do I start investing on Groww?", "Explain this simply", "Any recent news?"]

                if quick_replies:
                    yield f"data: {json.dumps({'quick_replies': quick_replies})}\n\n"

                # Persist the turn before signalling completion
                try:
                    await self._chat_repo.save_chat_turn(
                        user_id=user_id,
                        chat_id=chat_id,
                        human_response=query,
                        ai_response=full_response_text
                    )
                except Exception as repo_err:
                    print(f"[AgentController] Warning: Could not save chat turn: {repo_err}")

                yield "data: [DONE]\n\n"

            except Exception as err:
                print(f"[AgentController] Agent error: {err!r}")
                err_msg = "Something went wrong on my side. Please try again in a moment."
                yield f"data: {json.dumps({'token': err_msg})}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Type": "text/event-stream",
            }
        )

    async def sync_chat(self, payload: ChatRequest) -> Dict[str, Any]:
        """
        Processes a full chat turn synchronously and returns a complete JSON response.
        """
        user_id = payload.user_id.strip()
        query = payload.query.strip()
        chat_id = (payload.chat_id or "default_chat").strip()
        capital_amount = payload.capital_amount

        input_state: Dict[str, Any] = {
            "messages": [HumanMessage(content=query)],
            "user_id": user_id,
        }
        if capital_amount is not None:
            input_state["capital_amount"] = capital_amount

        try:
            await self._ensure_user_safe(user_id)
            compiled_graph = self._graph_orchestrator.get_compiled_graph(user_id=user_id)
            config = {"configurable": {"thread_id": self._thread_id(user_id, chat_id)}}
            result_state = await compiled_graph.ainvoke(input_state, config=config)

            messages = result_state.get("messages", [])
            final_text = ""
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content:
                    final_text = str(msg.content)
                    break

            final_text = re.sub(r'!function_call:\s*\{[\s\S]*?\}', '', final_text).strip()
            final_text = re.sub(r'<tool_call>[\s\S]*?<\/tool_call>', '', final_text).strip()

            # Save turn to repository
            try:
                await self._chat_repo.save_chat_turn(
                    user_id=user_id,
                    chat_id=chat_id,
                    human_response=query,
                    ai_response=final_text
                )
            except Exception:
                pass

            action_card = result_state.get("action_card")
            query_lower = query.lower()
            if not action_card and any(kw in query_lower for kw in ["suggest", "recommend", "stocks to buy", "products", "good stocks", "best stock", "which stock", "top stock", "buy stock"]):
                action_card = {
                    "card_type": "stock_recommendation_card",
                    "title": "Suggested Benchmark Stocks",
                    "stocks": [
                        {
                            "symbol": "RELIANCE",
                            "company_name": "Reliance Industries Ltd",
                            "price": 2987.50,
                            "change": "+1.2%",
                            "currency": "INR",
                            "exchange": "NSE",
                            "tag": "Nifty 50 Heavyweight",
                        },
                        {
                            "symbol": "TCS",
                            "company_name": "Tata Consultancy Services",
                            "price": 3452.00,
                            "change": "+0.8%",
                            "currency": "INR",
                            "exchange": "NSE",
                            "tag": "IT Bluechip",
                        },
                        {
                            "symbol": "HDFCBANK",
                            "company_name": "HDFC Bank Ltd",
                            "price": 1678.30,
                            "change": "-0.4%",
                            "currency": "INR",
                            "exchange": "NSE",
                            "tag": "Private Banking Leader",
                        },
                        {
                            "symbol": "ZOMATO",
                            "company_name": "Zomato Ltd",
                            "price": 268.40,
                            "change": "+2.1%",
                            "currency": "INR",
                            "exchange": "NSE",
                            "tag": "High-Growth Gen Z",
                        },
                    ],
                }

            return {
                "status": "success",
                "intent": result_state.get("current_intent"),
                "response": final_text,
                "action_card": action_card,
                "guardrail_passed": result_state.get("guardrail_passed", True)
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent execution failed: {str(e)}"
            )

    async def get_all_chats(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves all conversation sessions and history for a user.
        """
        try:
            chats = await self._chat_repo.get_all_chats(user_id)
            return {
                "status": "success",
                "user_id": user_id,
                "chats": chats
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch user chats: {str(e)}"
            )

    async def get_chat_session(self, user_id: str, chat_id: str) -> Dict[str, Any]:
        """
        Retrieves message turns for a specific chat session.
        """
        try:
            history = await self._chat_repo.get_chat_by_id(user_id, chat_id)
            if history is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chat session '{chat_id}' was not found for user '{user_id}'."
                )
            return {
                "status": "success",
                "user_id": user_id,
                "chat_id": chat_id,
                "turns": history
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch chat session: {str(e)}"
            )

    async def delete_chat_session(self, user_id: str, chat_id: str) -> Dict[str, Any]:
        """
        Deletes a specific chat session from the user's history.
        """
        try:
            deleted = await self._chat_repo.delete_chat_by_id(user_id, chat_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chat session '{chat_id}' was not found."
                )
            return {
                "status": "success",
                "message": f"Chat session '{chat_id}' deleted successfully."
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete chat session: {str(e)}"
            )
