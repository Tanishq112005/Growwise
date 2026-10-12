import os
from typing import Dict, Any, List
from pathlib import Path
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# =====================================================================
# Constants & API Configuration
# =====================================================================
TWELVE_DATA_BASE_URL = "https://api.twelvedata.com"


def _get_twelve_data_api_key() -> str:
    """
    Retrieves the Twelve Data API key from environment variables.
    Checks both TWELEVE_DATA_API_KEY and TWELVE_DATA_API_KEY for compatibility.
    """
    key = os.getenv("TWELEVE_DATA_API_KEY") or os.getenv("TWELVE_DATA_API_KEY")
    return (key or "").strip()


# Common Indian tickers a Gen Z user is likely to type without a suffix.
_INDIAN_DEFAULTS = {
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "WIPRO", "ZOMATO",
    "ETERNAL", "TATAMOTORS", "TATASTEEL", "BAJFINANCE", "LT", "AXISBANK", "KOTAKBANK",
    "TRENT", "NIFTYBEES", "JUNIORBEES", "BANKBEES",
}


def _build_symbol_params(symbol: str) -> Dict[str, str]:
    """
    Normalises a user/LLM symbol into Twelve Data params.
    'RELIANCE.NS' / 'RELIANCE.BO' or a known Indian ticker -> symbol + exchange (NSE/BSE).
    Anything else (AAPL, BTC/USD) is passed through unchanged.
    """
    clean = symbol.strip().upper()
    if clean.endswith(".NS"):
        return {"symbol": clean[:-3], "exchange": "NSE"}
    if clean.endswith(".BO"):
        return {"symbol": clean[:-3], "exchange": "BSE"}
    if clean in _INDIAN_DEFAULTS:
        return {"symbol": clean, "exchange": "NSE"}
    return {"symbol": clean}


# =====================================================================
# Twelve Data Tools
# =====================================================================
@tool
def get_market_quote(symbol: str) -> Dict[str, Any]:
    """
    Fetches real-time market quote metrics for a stock, ETF, or index from Twelve Data.
    Provides open, high, low, close, volume, price change, percentage change, and market status.
    Args:
        symbol: Ticker symbol to look up (e.g., 'AAPL', 'MSFT', 'SPY', 'BTC/USD').
    """
    api_key = _get_twelve_data_api_key()
    if not api_key:
        return {
            "symbol": symbol.upper(),
            "status": "error",
            "message": "Twelve Data API key is not configured. Live quote unavailable.",
            "source": "Twelve Data API"
        }

    clean_symbol = symbol.strip().upper()
    endpoint = f"{TWELVE_DATA_BASE_URL}/quote"
    params = {
        **_build_symbol_params(symbol),
        "apikey": api_key
    }

    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200 or data.get("status") == "error":
            error_msg = data.get("message", f"HTTP Error {response.status_code}")
            return {
                "symbol": clean_symbol,
                "status": "error",
                "message": error_msg,
                "source": "Twelve Data API",
                "note": "Live quote unavailable for this symbol on current feed plan."
            }

        return {
            "symbol": clean_symbol,
            "name": data.get("name"),
            "exchange": data.get("exchange"),
            "currency": data.get("currency"),
            "price": float(data.get("close", 0.0) or 0.0),
            "open": float(data.get("open", 0.0) or 0.0),
            "high": float(data.get("high", 0.0) or 0.0),
            "low": float(data.get("low", 0.0) or 0.0),
            "previous_close": float(data.get("previous_close", 0.0) or 0.0),
            "change": float(data.get("change", 0.0) or 0.0),
            "percent_change": float(data.get("percent_change", 0.0) or 0.0),
            "is_market_open": data.get("is_market_open", False),
            "timestamp": data.get("datetime"),
            "source": "Twelve Data Real-Time Feed"
        }
    except requests.RequestException as e:
        return {
            "symbol": clean_symbol,
            "status": "error",
            "message": f"Network error contacting market data provider: {str(e)}",
            "source": "Twelve Data API"
        }


@tool
def get_stock_price(symbol: str) -> Dict[str, Any]:
    """
    Fetches the latest current market price for a given ticker symbol from Twelve Data.
    Args:
        symbol: Ticker symbol to query (e.g., 'AAPL', 'MSFT', 'GOOGL').
    """
    api_key = _get_twelve_data_api_key()
    if not api_key:
        return {
            "symbol": symbol.upper(),
            "status": "error",
            "message": "Twelve Data API key is not configured.",
            "source": "Twelve Data API"
        }

    clean_symbol = symbol.strip().upper()
    endpoint = f"{TWELVE_DATA_BASE_URL}/price"
    params = {
        **_build_symbol_params(symbol),
        "apikey": api_key
    }

    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200 or data.get("status") == "error":
            error_msg = data.get("message", f"HTTP Error {response.status_code}")
            return {
                "symbol": clean_symbol,
                "status": "error",
                "message": error_msg,
                "source": "Twelve Data API"
            }

        price_val = float(data.get("price", 0.0) or 0.0)
        return {
            "symbol": clean_symbol,
            "price": price_val,
            "source": "Twelve Data Real-Time Price"
        }
    except requests.RequestException as e:
        return {
            "symbol": clean_symbol,
            "status": "error",
            "message": f"Network error contacting market data provider: {str(e)}",
            "source": "Twelve Data API"
        }


MARKET_DATA_TOOLS: List[Any] = [get_market_quote, get_stock_price]
