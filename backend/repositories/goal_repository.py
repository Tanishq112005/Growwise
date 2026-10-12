import uuid
from typing import Dict, Any, List, Optional
from backend.config.mongodb import MongoDBManager

# =====================================================================
# Goal Repository: GoalRepository
# =====================================================================
class GoalRepository:
    """
    Repository managing CRUD operations for user goals (task and percentage_of_completion).
    """
    def __init__(self):
        self._db_manager = MongoDBManager.get_instance()

    @property
    def _collection(self):
        return self._db_manager.get_database()["users"]

    async def create_goal(
        self,
        user_id: str,
        task: str,
        percentage_of_completion: float = 0.0
    ) -> Dict[str, Any]:
        """
        Creates a new goal for a user and appends it to their goals array.
        """
        if not user_id or not task:
            raise ValueError("user_id and task description are required to create a goal.")

        goal_id = str(uuid.uuid4())
        goal_entry: Dict[str, Any] = {
            "goal_id": goal_id,
            "task": task.strip(),
            "percentage_of_completion": max(0.0, min(100.0, float(percentage_of_completion)))
        }

        # Ensure user document exists before appending goals
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

        result = await self._collection.update_one(
            {"user_id": user_id},
            {"$push": {"goals": goal_entry}}
        )

        return goal_entry

    async def edit_goal(
        self,
        user_id: str,
        goal_id: str,
        task: Optional[str] = None,
        percentage_of_completion: Optional[float] = None
    ) -> bool:
        """
        Updates task title and/or progress percentage for a specific goal.
        """
        update_fields: Dict[str, Any] = {}
        if task is not None:
            update_fields["goals.$.task"] = task.strip()
        if percentage_of_completion is not None:
            update_fields["goals.$.percentage_of_completion"] = max(0.0, min(100.0, float(percentage_of_completion)))

        if not update_fields:
            return False

        result = await self._collection.update_one(
            {"user_id": user_id, "goals.goal_id": goal_id},
            {"$set": update_fields}
        )
        return result.modified_count > 0

    async def delete_goal(self, user_id: str, goal_id: str) -> bool:
        """
        Removes a goal from the user's goals array.
        """
        result = await self._collection.update_one(
            {"user_id": user_id},
            {"$pull": {"goals": {"goal_id": goal_id}}}
        )
        return result.modified_count > 0

    async def get_all_goals(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all goals associated with a specific user.
        """
        user = await self._collection.find_one(
            {"user_id": user_id},
            {"goals": 1, "_id": 0}
        )
        if not user:
            return []
        return user.get("goals", [])
