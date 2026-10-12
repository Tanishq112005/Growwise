import json
from typing import Any, List, Optional, Dict
from langchain_core.messages import SystemMessage
from backend.agent.agent_state import GrowwAgentState
from backend.agent.agents_specialized.base_agent import BaseAgentInterface
from backend.agent.agents_specialized.response_style import SIMPLE_LANGUAGE_RULES, SCOPE_GUARDRAIL
from backend.tools.market_data_tools import MARKET_DATA_TOOLS
from backend.tools.web_search_tools import WEB_SEARCH_TOOLS

MARKET_DATA_SYSTEM_PROMPT = """You are the Market Data Agent for Groww GenZ.
You have NO built-in knowledge of share prices, companies, news or market facts. You can only use your tools:
- `get_market_quote` / `get_stock_price`: live share prices. These are the ONLY source of any price or % move you may state.
- `search_financial_web`: live web search. This is the ONLY source of company news, background, or "which shares to look at" ideas.

RULES (strict):
1. ALWAYS call a tool before answering. Never answer from memory, even for very famous companies.
2. Price / quote / today's move of a share, ETF or index: call `get_market_quote` for each symbol
   (several symbols = several calls in the same step). For Indian shares pass the plain NSE ticker like 'RELIANCE' or 'TCS'.
3. News, company background, or "which shares / suggest stocks / top stocks": call `search_financial_web`.
   Describe only what the sources say and mention the sources. NEVER tell the user to buy or sell.
   Do not state any price in that answer unless it came from a quote tool; tell the user they can ask "price of <share>" for a live quote.
4. If a tool fails or is unavailable, say so plainly (e.g. "Live quote for X is unavailable right now") and do not estimate or guess.
5. For quotes, report only fields present in the tool result (price, change, % change, day high/low, previous close,
   market open or closed, timestamp, source). Skip anything the tool did not return. Use `is_market_open` to say whether it is a live
   price or the last close.
6. Never promise returns. Follow SIMPLE LANGUAGE below (very simple words, jargon only when needed).

RESPONSE FORMAT (Markdown, short):
  🎯 **The Bottom Line**: the latest price and % move in 1 sentence (or the key finding from the sources).
  📊 **Key Breakdown**: 2-4 bullets using only tool data. Bold tickers and prices (e.g. **₹2,987.50**, **RELIANCE**).
  💡 **Next Action**: one clear takeaway.
  **Sources**: only when you used web search; lines like "- [Title](url)" taken only from the results, no blank lines between them.
  🔤 **Jargon decoder**: last block, only if you used jargon (for example P/E, market cap, ETF, index).
""" + SIMPLE_LANGUAGE_RULES + SCOPE_GUARDRAIL

class MarketDataAgent(BaseAgentInterface):
    """
    Specialized agent responsible for share data queries.
    Binds Twelve Data market tools (live prices) and Tavily web search (news / share discovery).
    """
    def __init__(self, model: Any, tools: Optional[List[Any]] = None):
        bound_tools = tools if tools is not None else [*MARKET_DATA_TOOLS, *WEB_SEARCH_TOOLS]
        super().__init__(model=model, tools=bound_tools)

    @property
    def system_prompt(self) -> str:
        return MARKET_DATA_SYSTEM_PROMPT

    def execute(self, state: GrowwAgentState) -> Dict[str, Any]:
        """
        Executes share data inquiry with tool calling and strict anti-hallucination guardrails.
        """
        messages = state.get("messages", [])

        prompt_messages = [SystemMessage(content=self.system_prompt)]
        ticker_hint = state.get("detected_ticker")
        if ticker_hint:
            prompt_messages.append(SystemMessage(content=f"Ticker detected in the user's message: {ticker_hint}"))
        search_hint = state.get("search_query")
        if search_hint:
            prompt_messages.append(
                SystemMessage(content=f"If you search the web, a good standalone query is: {search_hint}")
            )
        prompt_messages.extend(messages)

        # Resolves any tool calls automatically (Twelve Data quotes / Tavily search)
        responses = self.invoke_with_tools(prompt_messages)

        # Extract structured stock quotes from tool outputs for Generative UI cards
        stocks_found = []
        for r in responses:
            content = getattr(r, "content", None)
            if content and isinstance(content, str):
                try:
                    data = json.loads(content)
                    if isinstance(data, dict) and data.get("price") and data.get("status") != "error":
                        stocks_found.append({
                            "symbol": str(data.get("symbol", "")).upper(),
                            "company_name": data.get("name") or data.get("symbol", ""),
                            "price": float(data.get("price", 0.0) or 0.0),
                            "change": f"{float(data.get('percent_change', 0.0) or 0.0):+.2f}%",
                            "currency": data.get("currency", "INR"),
                            "exchange": data.get("exchange", "NSE"),
                        })
                except Exception:
                    pass

        action_card = None
        if stocks_found:
            action_card = {
                "card_type": "stock_recommendation_card",
                "title": "Live Market Quote",
                "stocks": stocks_found,
            }

        return {
            "messages": responses,
            "guardrail_passed": True,
            "action_card": action_card,
        }
