from fastapi import APIRouter
from backend.routes.user_routes import user_router
from backend.routes.stock_routes import stock_router
from backend.routes.goal_routes import goal_router
from backend.routes.agent_routes import agent_router

# =====================================================================
# Centralized API Router
# =====================================================================
api_router = APIRouter(prefix="/api")

api_router.include_router(user_router)
api_router.include_router(stock_router)
api_router.include_router(goal_router)
api_router.include_router(agent_router)

__all__ = [
    "api_router",
    "user_router",
    "stock_router",
    "goal_router",
    "agent_router",
]
