from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.config.mongodb import MongoDBManager

# =====================================================================
# Chat Repository: ChatRepository
# =====================================================================
class ChatRepository:
    """
    Repository managing user chat sessions organized by chat_id and user_id.
    Stores turns containing human_response, ai_response, and timestamps.
    """
    def __init__(self):
        self._db_manager = MongoDBManager.get_instance()

    @property
    def _collection(self):
        return self._db_manager.get_database()["users"]

    async def save_chat_turn(
        self,
        user_id: str,
        chat_id: str,
        human_response: str,
        ai_response: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Saves a conversation turn into user_chat_history under the specific chat_id.
        """
        if not user_id or not chat_id:
            raise ValueError("user_id and chat_id are required to save a chat turn.")

        time_val = timestamp or datetime.utcnow().strftime("%I:%M %p")

        turn_entry: Dict[str, Any] = {
            "human_response": human_response,
            "ai_response": ai_response,
            "timestamp": time_val
        }

        # Appends to the array at path: user_chat_history.<chat_id>
        field_path = f"user_chat_history.{chat_id}"
        result = await self._collection.update_one(
            {"user_id": user_id},
            {"$push": {field_path: turn_entry}}
        )
        return result.modified_count > 0

    async def get_all_chats(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves all chat histories for a user across all chat_ids.
        """
        user = await self._collection.find_one(
            {"user_id": user_id},
            {"user_chat_history": 1, "_id": 0}
        )
        if not user:
            return {}
        return user.get("user_chat_history", {})

    async def get_chat_by_id(self, user_id: str, chat_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves message turns for a specific chat_id.
        """
        field_path = f"user_chat_history.{chat_id}"
        user = await self._collection.find_one(
            {"user_id": user_id},
            {field_path: 1, "_id": 0}
        )
        if not user or "user_chat_history" not in user:
            return None
        return user["user_chat_history"].get(chat_id)

    async def delete_chat_by_id(self, user_id: str, chat_id: str) -> bool:
        """
        Deletes a specific chat_id session from user_chat_history.
        """
        field_path = f"user_chat_history.{chat_id}"
        result = await self._collection.update_one(
            {"user_id": user_id},
            {"$unset": {field_path: ""}}
        )
        return result.modified_count > 0
