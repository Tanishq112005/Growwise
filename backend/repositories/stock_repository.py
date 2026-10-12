from typing import Dict, Any, List
from backend.config.mongodb import MongoDBManager

# =====================================================================
# Stock Repository: StockRepository
# =====================================================================
class StockRepository:
    """
    Repository managing user stock holdings and recently viewed stocks.
    """
    def __init__(self):
        self._db_manager = MongoDBManager.get_instance()

    @property
    def _collection(self):
        return self._db_manager.get_database()["users"]

    async def get_user_stocks(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the current list of stocks owned by the user.
        """
        user = await self._collection.find_one(
            {"user_id": user_id},
            {"current_list_of_the_stocks": 1, "_id": 0}
        )
        if not user:
            return []
        return user.get("current_list_of_the_stocks", [])

    async def insert_user_stock(self, user_id: str, stock_data: Dict[str, Any]) -> bool:
        """
        Inserts or appends a stock entry into current_list_of_the_stocks.
        If the stock symbol already exists, updates its quantity and current value.
        """
        symbol = stock_data.get("symbol", "").upper()
        if not symbol:
            raise ValueError("Stock data must include a valid 'symbol'.")

        # Ensure volatile current_value is stripped and immutable buy_price is persisted
        clean_stock_data = dict(stock_data)
        clean_stock_data.pop("current_value", None)

        # Ensure user document exists before updating stock holdings
        await self._collection.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {
                "name": "Investor",
                "current_list_of_the_stocks": [],
                "goals": [],
                "user_chat_history": {},
                "recently_veiwed_stock": []
            }},
            upsert=True
        )

        # First, remove existing entry with same symbol if present to prevent duplicates
        await self._collection.update_one(
            {"user_id": user_id},
            {"$pull": {"current_list_of_the_stocks": {"symbol": symbol}}}
        )

        # Append fresh/updated stock entry with buy_price
        result = await self._collection.update_one(
            {"user_id": user_id},
            {"$push": {"current_list_of_the_stocks": clean_stock_data}}
        )
        return result.modified_count > 0

    async def delete_user_stock(self, user_id: str, stock_symbol: str) -> bool:
        """
        Removes a stock from the user's current holdings list.
        """
        clean_symbol = stock_symbol.strip().upper()
        result = await self._collection.update_one(
            {"user_id": user_id},
            {"$pull": {"current_list_of_the_stocks": {"symbol": clean_symbol}}}
        )
        return result.modified_count > 0

    async def add_recently_viewed_stock(self, user_id: str, stock_data: Dict[str, Any]) -> bool:
        """
        Adds or prepends a stock to the user's recently viewed list (capped at 10 items).
        """
        symbol = stock_data.get("symbol", "").upper()
        if not symbol:
            return False

        # Pull existing if already in list to avoid duplicates
        await self._collection.update_one(
            {"user_id": user_id},
            {"$pull": {"recently_veiwed_stock": {"symbol": symbol}}}
        )

        # Push to front of recently viewed array
        result = await self._collection.update_one(
            {"user_id": user_id},
            {"$push": {
                "recently_veiwed_stock": {
                    "$each": [stock_data],
                    "$position": 0,
                    "$slice": 10
                }
            }}
        )
        return result.modified_count > 0

    async def get_recently_viewed_stocks(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the user's recently viewed stocks.
        """
        user = await self._collection.find_one(
            {"user_id": user_id},
            {"recently_veiwed_stock": 1, "_id": 0}
        )
        if not user:
            return []
        return user.get("recently_veiwed_stock", [])
