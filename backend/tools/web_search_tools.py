import os
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient
from tavily.errors import InvalidAPIKeyError, UsageLimitExceededError

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# =====================================================================
# Constants & API Configuration
# =====================================================================
def _get_tavily_api_key() -> str:
    """Retrieves the Tavily API key from environment."""
    return (os.getenv("TAVILY_API_KEY") or "").strip()


# =====================================================================
# Tavily Web Search Tool
# =====================================================================
@tool
def search_financial_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Searches the live web for verified financial news, market developments, regulatory updates (SEBI circulars),
    or viral financial jargon using the Tavily Search API.
    Args:
        query: Search query string (e.g., 'Nifty 50 record high', 'SEBI new index derivative rules', 'Zudio financial results').
        max_results: Maximum number of search results to retrieve (default: 5).
    """
    api_key = _get_tavily_api_key()
    if not api_key or api_key == "your_tavily_api_key_here":
        return {
            "query": query,
            "status": "unavailable",
            "results": [],
            "message": "Tavily Search API key is not configured or placeholder detected.",
            "note": "Web search is currently unavailable. Do not fabricate news or cite unverified rumors."
        }

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max(1, min(10, max_results)),
            search_depth="basic"
        )

        formatted_results = []
        raw_results = response.get("results", [])
        for item in raw_results:
            formatted_results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content"),
                "score": item.get("score")
            })

        return {
            "query": query,
            "status": "success",
            "results_count": len(formatted_results),
            "results": formatted_results,
            "source": "Tavily Financial Search"
        }
    except InvalidAPIKeyError:
        return {
            "query": query,
            "status": "error",
            "message": "Tavily API key is invalid or unauthorized.",
            "results": [],
            "source": "Tavily Search API"
        }
    except UsageLimitExceededError:
        return {
            "query": query,
            "status": "error",
            "message": "Tavily search rate limit or quota exceeded.",
            "results": [],
            "source": "Tavily Search API"
        }
    except Exception as e:
        return {
            "query": query,
            "status": "error",
            "message": f"Unexpected error executing Tavily search: {str(e)}",
            "results": [],
            "source": "Tavily Search API"
        }


WEB_SEARCH_TOOLS: List[Any] = [search_financial_web]
