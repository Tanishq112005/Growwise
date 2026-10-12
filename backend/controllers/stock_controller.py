from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException, status
from backend.repositories.stock_repository import StockRepository
from backend.tools.market_data_tools import get_market_quote


# =====================================================================
# Request Schemas
# =====================================================================
class AddStockRequest(BaseModel):
    symbol: str = Field(..., min_length=1, description="Stock ticker symbol (e.g. RELIANCE, TCS, AAPL)")
    company_name: str = Field(..., min_length=1, description="Full name of company")
    quantity: int = Field(default=1, ge=1, description="Quantity of shares held")
    buy_price: float = Field(..., ge=0.0, description="Purchase execution price per share")
    pnl: Optional[str] = Field(default=None, description="Optional P&L label")


class RecentlyViewedRequest(BaseModel):
    symbol: str = Field(..., min_length=1, description="Stock ticker symbol")
    company_name: str = Field(..., min_length=1, description="Company title")
    price: Optional[float] = Field(default=None, description="Last viewed market price")
    change: Optional[str] = Field(default=None, description="Day percent change")


# =====================================================================
# Stock Controller: StockController
# =====================================================================
class StockController:
    """
    Controller handling business logic for portfolio stock holdings,
    recently viewed tracking, and real-time market data quotes.
    """
    def __init__(self, stock_repo: Optional[StockRepository] = None):
        self._stock_repo = stock_repo or StockRepository()

    async def get_user_stocks(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves all portfolio stocks currently held by the user.
        """
        try:
            stocks = await self._stock_repo.get_user_stocks(user_id)
            return {
                "status": "success",
                "user_id": user_id,
                "count": len(stocks),
                "stocks": stocks
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch user stocks: {str(e)}"
            )

    async def get_portfolio_valuation(self, user_id: str) -> Dict[str, Any]:
        """
        Calculates real-time portfolio valuation by querying Twelve Data for each holding,
        computing buy value, current market value, profit & loss, and percentage return.
        """
        try:
            stocks = await self._stock_repo.get_user_stocks(user_id)
            total_portfolio_value = 0.0
            total_invested = 0.0
            total_profit = 0.0
            total_loss = 0.0
            holdings_valuation = []

            for item in stocks:
                symbol = item.get("symbol", "").upper()
                qty = float(item.get("quantity", 1))
                buy_price = float(item.get("buy_price", 0.0))
                invested_item = buy_price * qty
                total_invested += invested_item

                # Fetch live market price from Twelve Data
                live_price = buy_price
                price_change = 0.0
                currency = "INR"
                try:
                    quote = get_market_quote.invoke({"symbol": symbol})
                    if isinstance(quote, dict) and quote.get("status") != "error" and quote.get("price"):
                        live_price = float(quote.get("price"))
                        price_change = float(quote.get("percent_change", 0.0))
                        currency = quote.get("currency", "INR")
                except Exception:
                    pass

                current_item_value = live_price * qty
                item_pnl = current_item_value - invested_item
                item_pnl_percent = ((item_pnl / invested_item) * 100) if invested_item > 0 else 0.0

                if item_pnl > 0:
                    total_profit += item_pnl
                elif item_pnl < 0:
                    total_loss += abs(item_pnl)

                total_portfolio_value += current_item_value

                pnl_str = f"{'+' if item_pnl >= 0 else ''}{round(item_pnl, 2)} ({'+' if item_pnl_percent >= 0 else ''}{round(item_pnl_percent, 1)}%)"

                holdings_valuation.append({
                    "symbol": symbol,
                    "company_name": item.get("company_name", symbol),
                    "quantity": int(qty),
                    "buy_price": round(buy_price, 2),
                    "current_price": round(live_price, 2),
                    "invested_value": round(invested_item, 2),
                    "current_value": round(current_item_value, 2),
                    "pnl": round(item_pnl, 2),
                    "pnl_percent": round(item_pnl_percent, 2),
                    "pnl_display": pnl_str,
                    "currency": currency
                })

            total_pnl = total_portfolio_value - total_invested
            total_pnl_percent = ((total_pnl / total_invested) * 100) if total_invested > 0 else 0.0

            return {
                "status": "success",
                "user_id": user_id,
                "total_portfolio_value": round(total_portfolio_value, 2),
                "total_invested": round(total_invested, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percent": round(total_pnl_percent, 2),
                "total_profit": round(total_profit, 2),
                "total_loss": round(total_loss, 2),
                "holdings_count": len(holdings_valuation),
                "holdings": holdings_valuation
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to calculate portfolio valuation: {str(e)}"
            )

    async def add_user_stock(self, user_id: str, payload: AddStockRequest) -> Dict[str, Any]:
        """
        Adds or updates a stock holding in the user's portfolio.
        Guarantees immutable buy_price persistence.
        """
        try:
            stock_data = {
                "symbol": payload.symbol.strip().upper(),
                "company_name": payload.company_name.strip(),
                "quantity": payload.quantity,
                "buy_price": payload.buy_price,
                "pnl": payload.pnl
            }
            success = await self._stock_repo.insert_user_stock(user_id=user_id, stock_data=stock_data)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to register stock for user '{user_id}'."
                )
            return {
                "status": "success",
                "message": f"Stock '{payload.symbol.upper()}' registered successfully.",
                "stock": stock_data
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to record stock: {str(e)}"
            )

    async def delete_user_stock(self, user_id: str, symbol: str) -> Dict[str, Any]:
        """
        Removes a stock position from the user's holdings list.
        """
        try:
            success = await self._stock_repo.delete_user_stock(user_id=user_id, stock_symbol=symbol)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Stock '{symbol.upper()}' not found in user's portfolio."
                )
            return {
                "status": "success",
                "message": f"Stock '{symbol.upper()}' deleted successfully."
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete stock: {str(e)}"
            )

    async def get_recently_viewed(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves the user's list of recently viewed stocks (capped at 10 items).
        """
        try:
            stocks = await self._stock_repo.get_recently_viewed_stocks(user_id)
            return {
                "status": "success",
                "user_id": user_id,
                "count": len(stocks),
                "recently_viewed": stocks
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch recently viewed stocks: {str(e)}"
            )

    async def add_recently_viewed(self, user_id: str, payload: RecentlyViewedRequest) -> Dict[str, Any]:
        """
        Adds or updates a stock in the user's recently viewed list.
        """
        try:
            stock_data = {
                "symbol": payload.symbol.strip().upper(),
                "company_name": payload.company_name.strip(),
                "price": payload.price,
                "change": payload.change
            }
            await self._stock_repo.add_recently_viewed_stock(user_id=user_id, stock_data=stock_data)
            return {
                "status": "success",
                "message": f"Stock '{payload.symbol.upper()}' added to recently viewed list."
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to record recently viewed stock: {str(e)}"
            )

    def get_live_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieves a live market quote for a stock or ETF via Twelve Data API.
        """
        try:
            quote = get_market_quote.invoke({"symbol": symbol.strip().upper()})
            return {
                "status": "success",
                "quote": quote
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch market quote: {str(e)}"
            )
