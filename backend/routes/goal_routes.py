from typing import Dict, Any
from fastapi import APIRouter, status
from backend.controllers.goal_controller import (
    GoalController,
    CreateGoalRequest,
    EditGoalRequest,
)

goal_router = APIRouter(prefix="/goals", tags=["Goals"])
_goal_controller = GoalController()


@goal_router.get("/{user_id}")
async def get_user_goals_route(user_id: str) -> Dict[str, Any]:
    """Route: Retrieves all financial goals established by the user."""
    return await _goal_controller.get_user_goals(user_id)


@goal_router.post("/{user_id}", status_code=status.HTTP_201_CREATED)
async def create_goal_route(user_id: str, payload: CreateGoalRequest) -> Dict[str, Any]:
    """Route: Creates a new financial savings or habit goal."""
    return await _goal_controller.create_goal(user_id, payload)


@goal_router.put("/{user_id}/{goal_id}")
async def edit_goal_route(user_id: str, goal_id: str, payload: EditGoalRequest) -> Dict[str, Any]:
    """Route: Updates task description or completion percentage of an existing goal."""
    return await _goal_controller.edit_goal(user_id, goal_id, payload)


@goal_router.delete("/{user_id}/{goal_id}")
async def delete_goal_route(user_id: str, goal_id: str) -> Dict[str, Any]:
    """Route: Removes a goal from the user's goals array."""
    return await _goal_controller.delete_goal(user_id, goal_id)
