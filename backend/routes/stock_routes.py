from typing import Dict, Any
from fastapi import APIRouter, status
from backend.controllers.stock_controller import (
    StockController,
    AddStockRequest,
    RecentlyViewedRequest,
)

stock_router = APIRouter(prefix="/stocks", tags=["Stocks"])
_stock_controller = StockController()


@stock_router.get("/{user_id}")
async def get_user_stocks_route(user_id: str) -> Dict[str, Any]:
    """Route: Retrieves all portfolio stocks held by the user."""
    return await _stock_controller.get_user_stocks(user_id)


@stock_router.get("/{user_id}/valuation")
async def get_portfolio_valuation_route(user_id: str) -> Dict[str, Any]:
    """Route: Calculates live portfolio valuation, total value, and P&L using Twelve Data."""
    return await _stock_controller.get_portfolio_valuation(user_id)


@stock_router.post("/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_user_stock_route(user_id: str, payload: AddStockRequest) -> Dict[str, Any]:
    """Route: Adds or updates a stock holding with immutable buy_price persistence."""
    return await _stock_controller.add_user_stock(user_id, payload)


@stock_router.delete("/{user_id}/{symbol}")
async def delete_user_stock_route(user_id: str, symbol: str) -> Dict[str, Any]:
    """Route: Removes a stock position from the user's holdings list."""
    return await _stock_controller.delete_user_stock(user_id, symbol)


@stock_router.get("/{user_id}/recently-viewed")
async def get_recently_viewed_route(user_id: str) -> Dict[str, Any]:
    """Route: Retrieves user's list of recently viewed stocks."""
    return await _stock_controller.get_recently_viewed(user_id)


@stock_router.post("/{user_id}/recently-viewed")
async def add_recently_viewed_route(user_id: str, payload: RecentlyViewedRequest) -> Dict[str, Any]:
    """Route: Appends a stock to the user's recently viewed list."""
    return await _stock_controller.add_recently_viewed(user_id, payload)


@stock_router.get("/quote/{symbol}")
def get_live_stock_quote_route(symbol: str) -> Dict[str, Any]:
    """Route: Retrieves live quote metrics via Twelve Data API."""
    return _stock_controller.get_live_quote(symbol)
