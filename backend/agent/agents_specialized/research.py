"""Research pipeline for every finance question: gather -> completeness check -> answer.

Why this exists:
- A question can need several sources at once (live share data AND web results AND the user's own profile).
  `gather` fetches every source the Director asked for, in code, so nothing depends on the model "remembering" to call a tool.
- Before writing the answer, `coverage` shows the collected data to the model and asks:
  "does this cover EVERY part of the question?". If not, it names what is missing and `gather` runs again
  (at most MAX_COVERAGE_ROUNDS times).
- `answer` writes the final reply using ONLY the collected data, so it cannot answer from model memory.
"""
import json
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.agent.agent_state import GrowwAgentState
from backend.agent.agents_specialized.response_style import (
    GROWW_BRAND_RULES,
    SCOPE_GUARDRAIL,
    SIMPLE_LANGUAGE_RULES,
)
from backend.tools.database_tools import (
    get_user_goals_tool,
    get_user_profile_tool,
    get_user_stocks_tool,
)
from backend.tools.market_data_tools import get_market_quote
from backend.tools.web_search_tools import search_financial_web

MAX_COVERAGE_ROUNDS = 2
VALID_SOURCES = ("market", "web", "profile")
_TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-/&]{0,19}$")

RESEARCH_SYSTEM_PROMPT = """You are the Research Agent for Growwise, the Groww GenZ investing assistant.
You have NO built-in knowledge about finance, investing, products, rates, minimum amounts, rules, prices or news.
Everything you say MUST come from the COLLECTED DATA below. It can contain:
- USER PROFILE: the signed-in user's own details, goals and holdings (the only source for anything about the user),
- LIVE MARKET QUOTES: the ONLY source of any share price or % move,
- WEB SEARCH RESULTS: the ONLY source of facts, rules, numbers, news and how-tos.

GROUNDING RULES (strict):
1. Answer EVERY part of the user's question. If a part is not covered by the data (or a tool failed), say plainly which part you could
   not verify. Never guess.
2. Use a number (minimum amount, return, fee, date, price, lock-in) only if it appears in the data.
3. For prices, say whether the market is open (live price) or it is the last close, and give the timestamp when available.
4. Use profile details only when the question needs them, and share only what the user asked about.
   Never show IDs, tokens or anything that was not asked for.
5. Never invent URLs, titles or quotes. Cite only web results you actually used.
6. Earlier messages in this chat may contain unverified claims. Do not repeat them unless the data supports them.
7. Educational only: never promise or guarantee returns and never tell the user to buy or sell a specific security.
8. Write for a complete beginner (age 20-26). If the user clearly sounds experienced, skip the basics.

RESPONSE FORMAT (Markdown, under about 170 words before Sources):
  🎯 **The Bottom Line**: 1-2 direct sentences that answer the question.
  📊 **Key Breakdown**: 2-5 short bullets that cover every part of the question. Bold key amounts, names and tickers.
     Use a small table only to compare 2 or more shares or options.
  💡 **Next Action**: ONE friendly next step on Groww (see GROWW FOCUS).
  **Sources**: only if web results were used. Up to 3 lines, each exactly "- [Title](url)", no blank lines between them.
  🔤 **Jargon decoder**: last block, only if you used jargon (see SIMPLE LANGUAGE).
""" + SIMPLE_LANGUAGE_RULES + GROWW_BRAND_RULES + SCOPE_GUARDRAIL

COVERAGE_SYSTEM_PROMPT = """You are a strict completeness reviewer for a finance assistant.
You get the user's question and the DATA collected so far. Decide whether the data is enough to answer EVERY part of the question.
Judge only from the data shown. Never use outside knowledge.

Sources that can still be asked for (only these exist):
- "market": live quotes for share / ETF / index tickers. Give plain tickers in "extra_tickers" (e.g. RELIANCE, TCS, INFY, AAPL).
- "web": one more web search. Give a standalone English query (at most 12 words) in "extra_search_query".
- "profile": the signed-in user's own profile, goals and holdings.

Return ONLY a JSON object:
{
  "complete": true or false,
  "missing": null or "short description of what is not covered yet",
  "extra_needs": [] or a list of "market" | "web" | "profile",
  "extra_tickers": [],
  "extra_search_query": null or string
}
Rules:
- complete = true when every part of the question can be answered from the data, OR when what is missing cannot be fetched by the
  sources above.
- Do not ask again for something the data already contains, or that already failed (an "unavailable" or "failed" entry means it
  cannot be fetched).
- A question that asks for both share data and news/explanations needs "market" AND "web". A question about the user's own details needs "profile".
- For "top stocks" style questions you may take share names that appear in the web results and request their live quotes.
- Only request what is truly needed.
"""

NO_VERIFIED_ANSWER = (
    "🎯 **I couldn't verify that right now.**\n\n"
    "I only answer money questions from live data (market quotes, web sources and your profile), and I couldn't "
    "collect anything reliable for this one. The data services may be down. I won't guess on money matters.\n\n"
    "💡 **Next Action**: Please try again in a minute, or rephrase your question."
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _last_user_text(messages: List[Any]) -> str:
    for msg in reversed(messages or []):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            return str(msg.content)
    return ""


def _blank_evidence() -> Dict[str, Any]:
    return {"profile": None, "market": {}, "web": []}


def _copy_evidence(raw: Any) -> Dict[str, Any]:
    evidence = _blank_evidence()
    if isinstance(raw, dict):
        evidence["profile"] = raw.get("profile")
        evidence["market"] = dict(raw.get("market") or {})
        evidence["web"] = list(raw.get("web") or [])
    return evidence


def _safe_invoke(tool_obj: Any, args: Dict[str, Any]) -> Dict[str, Any]:
    """Runs a tool and always returns a dict, so one failing source never breaks the whole turn."""
    try:
        result = tool_obj.invoke(args)
        return result if isinstance(result, dict) else {"status": "success", "data": result}
    except Exception as err:
        print(f"[Research] Tool failed: {getattr(tool_obj, 'name', tool_obj)} -> {err}")
        return {"status": "error", "message": str(err)}


def _parse_json(text: Any) -> Dict[str, Any]:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise
        data = json.loads(cleaned[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("Reviewer did not return a JSON object.")
    return data


def _valid_quote(quote: Dict[str, Any]) -> bool:
    return bool(quote.get("price")) and quote.get("status") != "error"


def has_data(evidence: Dict[str, Any]) -> bool:
    profile = evidence.get("profile") or {}
    if (profile.get("profile") or {}).get("status") == "success":
        return True
    if any(_valid_quote(q) for q in (evidence.get("market") or {}).values()):
        return True
    return any(s.get("status") == "success" and s.get("results") for s in (evidence.get("web") or []))


def format_evidence(evidence: Dict[str, Any]) -> str:
    """Turns the collected data into compact text for the reviewer and the answer writer."""
    parts: List[str] = []

    profile = evidence.get("profile")
    if profile:
        parts.append("USER PROFILE (the signed-in user's own data):\n" + json.dumps(profile, default=str)[:3000])

    market = evidence.get("market") or {}
    if market:
        lines: List[str] = []
        for symbol, quote in market.items():
            if not _valid_quote(quote):
                lines.append(f"- {symbol}: UNAVAILABLE ({quote.get('message') or 'no data returned'})")
                continue
            state = "market open (live price)" if quote.get("is_market_open") else "market closed (last close)"
            lines.append(
                f"- {symbol} ({quote.get('name')}, {quote.get('exchange')}): price {quote.get('price')} {quote.get('currency')}, "
                f"change {quote.get('change')} ({quote.get('percent_change')}%), previous close {quote.get('previous_close')}, "
                f"day range {quote.get('low')} to {quote.get('high')}, {state}, time {quote.get('timestamp')}"
            )
        parts.append("LIVE MARKET QUOTES:\n" + "\n".join(lines))

    web = evidence.get("web") or []
    if web:
        blocks: List[str] = []
        seen_urls = set()
        number = 0
        for search in web:
            if search.get("status") != "success":
                blocks.append(f"(web search for '{search.get('query')}' FAILED: {search.get('message') or 'no results'})")
                continue
            for item in search.get("results") or []:
                url = item.get("url")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                number += 1
                content = (item.get("content") or "").strip().replace("\n", " ")[:600]
                blocks.append(f"[{number}] {item.get('title')}\nURL: {url}\n{content}")
        parts.append("WEB SEARCH RESULTS:\n" + "\n\n".join(blocks))

    return "\n\n".join(parts) if parts else "(nothing collected)"


# ---------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------
class ResearchPipeline:
    """Holds the three graph nodes: gather, coverage and answer."""

    def __init__(self, model: Any):
        self.model = model

    # 1) Fetch every source that is needed right now ------------------
    def gather(self, state: GrowwAgentState) -> Dict[str, Any]:
        needs = set(state.get("needs") or [])
        evidence = _copy_evidence(state.get("evidence"))
        user_id = state.get("user_id")

        # The user_id always comes from the system state, never from the model.
        if "profile" in needs and user_id and not evidence["profile"]:
            evidence["profile"] = {
                "profile": _safe_invoke(get_user_profile_tool, {"user_id": user_id}),
                "goals": _safe_invoke(get_user_goals_tool, {"user_id": user_id}),
                "holdings": _safe_invoke(get_user_stocks_tool, {"user_id": user_id}),
            }

        if "market" in needs:
            for raw_symbol in state.get("tickers") or []:
                symbol = str(raw_symbol).strip().upper()
                if not _TICKER_RE.match(symbol) or symbol in evidence["market"]:
                    continue
                evidence["market"][symbol] = _safe_invoke(get_market_quote, {"symbol": symbol})

        if "web" in needs:
            query = (state.get("search_query") or _last_user_text(state.get("messages", []))).strip()
            used_queries = {search.get("query") for search in evidence["web"]}
            if query and query not in used_queries:
                result = _safe_invoke(search_financial_web, {"query": query, "max_results": 5})
                evidence["web"].append({
                    "query": query,
                    "status": result.get("status"),
                    "message": result.get("message"),
                    "results": result.get("results") or [],
                })

        print(f"[Research] gather done. needs={sorted(needs)} market={list(evidence['market'])} web_searches={len(evidence['web'])}")
        return {"evidence": evidence}

    # 2) Ask the model: is every part of the question covered? --------
    def coverage(self, state: GrowwAgentState) -> Dict[str, Any]:
        attempts = int(state.get("coverage_attempts") or 0)
        evidence = _copy_evidence(state.get("evidence"))
        question = _last_user_text(state.get("messages", []))

        result: Dict[str, Any] = {"coverage_attempts": attempts + 1, "coverage_incomplete": False, "gaps": None}

        try:
            response = self.model.invoke([
                SystemMessage(content=COVERAGE_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"USER QUESTION:\n{question}\n\n"
                        f"DATA COLLECTED SO FAR:\n{format_evidence(evidence)}"
                    )
                ),
            ])
            parsed = _parse_json(getattr(response, "content", response))
        except Exception as err:
            # If the reviewer fails we still answer, using what we have.
            print(f"[Research] coverage check failed, continuing: {err}")
            return result

        if parsed.get("complete", True):
            print("[Research] coverage: complete")
            return result

        missing = parsed.get("missing")
        result["gaps"] = str(missing)[:300] if missing else None
        print(f"[Research] coverage: incomplete -> {result['gaps']}")

        # The last round never loops again; the answer will say what could not be verified.
        if attempts + 1 >= MAX_COVERAGE_ROUNDS:
            return result

        extra_needs = [n for n in (parsed.get("extra_needs") or []) if n in VALID_SOURCES]
        new_tickers: List[str] = []
        for raw_symbol in parsed.get("extra_tickers") or []:
            symbol = str(raw_symbol).strip().upper()
            if _TICKER_RE.match(symbol) and symbol not in evidence["market"] and symbol not in new_tickers:
                new_tickers.append(symbol)
        extra_query = str(parsed.get("extra_search_query") or "").strip()
        used_queries = {search.get("query") for search in evidence["web"]}

        actionable: List[str] = []
        if "market" in extra_needs and new_tickers:
            actionable.append("market")
        if "web" in extra_needs and extra_query and extra_query not in used_queries:
            actionable.append("web")
        if "profile" in extra_needs and not evidence.get("profile"):
            actionable.append("profile")
        if not actionable:
            return result

        result.update({
            "coverage_incomplete": True,
            "needs": actionable,
            "tickers": new_tickers[:5],
            "search_query": extra_query or state.get("search_query"),
        })
        return result

    # 3) Write the final answer from the collected data only ----------
    def answer(self, state: GrowwAgentState) -> Dict[str, Any]:
        evidence = _copy_evidence(state.get("evidence"))
        cleared = {"evidence": {}, "needs": [], "tickers": [], "coverage_incomplete": False}

        if not has_data(evidence):
            return {
                "messages": [AIMessage(content=NO_VERIFIED_ANSWER)],
                "action_card": None,
                "guardrail_passed": True,
                **cleared,
            }

        prompt = f"{RESEARCH_SYSTEM_PROMPT}\n\nCOLLECTED DATA:\n{format_evidence(evidence)}"
        gaps = state.get("gaps")
        if gaps:
            prompt += (
                f"\n\nREVIEWER NOTE: this part of the question is still NOT covered by the data: {gaps}\n"
                "Say plainly that you could not verify it. Do not fill the gap from memory."
            )

        messages = state.get("messages", [])
        response = self.model.invoke([SystemMessage(content=prompt), *messages])

        stocks = [
            {
                "symbol": symbol,
                "company_name": quote.get("name") or symbol,
                "price": float(quote.get("price") or 0.0),
                "change": f"{float(quote.get('percent_change') or 0.0):+.2f}%",
                "currency": quote.get("currency", "INR"),
                "exchange": quote.get("exchange", "NSE"),
            }
            for symbol, quote in (evidence.get("market") or {}).items()
            if _valid_quote(quote)
        ]
        action_card: Optional[Dict[str, Any]] = None
        if stocks:
            action_card = {
                "card_type": "stock_recommendation_card",
                "title": "Live Market Quote",
                "stocks": stocks,
            }

        return {
            "messages": [response],
            "action_card": action_card,
            "guardrail_passed": True,
            **cleared,
        }
