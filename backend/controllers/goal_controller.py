from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException, status
from backend.repositories.goal_repository import GoalRepository


# =====================================================================
# Request Schemas
# =====================================================================
class CreateGoalRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Description of the financial goal or habit")
    percentage_of_completion: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage")


class EditGoalRequest(BaseModel):
    task: Optional[str] = Field(default=None, description="Updated description of the goal")
    percentage_of_completion: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Updated progress")


# =====================================================================
# Goal Controller: GoalController
# =====================================================================
class GoalController:
    """
    Controller handling business logic for financial habit goals,
    micro-SIP targets, progress updates, and deletions.
    """
    def __init__(self, goal_repo: Optional[GoalRepository] = None):
        self._goal_repo = goal_repo or GoalRepository()

    async def get_user_goals(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves all savings and investment goals established by the user.
        """
        try:
            goals = await self._goal_repo.get_all_goals(user_id)
            return {
                "status": "success",
                "user_id": user_id,
                "count": len(goals),
                "goals": goals
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch user goals: {str(e)}"
            )

    async def create_goal(self, user_id: str, payload: CreateGoalRequest) -> Dict[str, Any]:
        """
        Creates a new goal for the user in the database.
        """
        try:
            goal = await self._goal_repo.create_goal(
                user_id=user_id,
                task=payload.task,
                percentage_of_completion=payload.percentage_of_completion
            )
            return {
                "status": "success",
                "message": "Goal created successfully.",
                "goal": goal
            }
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(ve)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create goal: {str(e)}"
            )

    async def edit_goal(self, user_id: str, goal_id: str, payload: EditGoalRequest) -> Dict[str, Any]:
        """
        Updates the task description and/or progress percentage of an existing user goal.
        """
        try:
            success = await self._goal_repo.edit_goal(
                user_id=user_id,
                goal_id=goal_id,
                task=payload.task,
                percentage_of_completion=payload.percentage_of_completion
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Goal with id '{goal_id}' was not found or no changes were made."
                )
            return {
                "status": "success",
                "message": f"Goal '{goal_id}' updated successfully."
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update goal: {str(e)}"
            )

    async def delete_goal(self, user_id: str, goal_id: str) -> Dict[str, Any]:
        """
        Removes a goal from the user's goals array.
        """
        try:
            success = await self._goal_repo.delete_goal(user_id=user_id, goal_id=goal_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Goal with id '{goal_id}' was not found."
                )
            return {
                "status": "success",
                "message": f"Goal '{goal_id}' deleted successfully."
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete goal: {str(e)}"
            )
