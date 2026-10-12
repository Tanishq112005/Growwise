import asyncio
import threading
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from backend.repositories.goal_repository import GoalRepository
from backend.repositories.stock_repository import StockRepository
from backend.repositories.user_repository import UserRepository

# =====================================================================
# Persistent Async Worker for Safe Sync Tool Invocations
# =====================================================================
class _AsyncWorker:
    """
    Dedicated worker running a single persistent background event loop.
    Prevents closed loop collisions across multiple tool invocations in motor.
    """
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coro_fn, *args, **kwargs) -> Any:
        future = asyncio.run_coroutine_threadsafe(coro_fn(*args, **kwargs), self._loop)
        return future.result(timeout=10)


_worker = _AsyncWorker()

# Singleton instances of repositories
_goal_repo = GoalRepository()
_stock_repo = StockRepository()
_user_repo = UserRepository()


# =====================================================================
# Goal Repository Tools
# =====================================================================
@tool
def create_user_goal_tool(
    user_id: str,
    task: str,
    percentage_of_completion: float = 0.0
) -> Dict[str, Any]:
    """
    Creates a new financial savings or habit goal for a user in the database.
    Args:
        user_id: The UUID string of the user.
        task: Description of the goal (e.g. 'Build ₹2,000 emergency buffer', 'Save ₹200 weekly').
        percentage_of_completion: Progress completion percentage from 0.0 to 100.0.
    """
    try:
        result = _worker.run(
            _goal_repo.create_goal,
            user_id=user_id,
            task=task,
            percentage_of_completion=percentage_of_completion
        )
        return {
            "status": "success",
            "message": f"Goal '{task}' created successfully.",
            "goal": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create goal: {str(e)}"
        }


@tool
def get_user_goals_tool(user_id: str) -> Dict[str, Any]:
    """
    Retrieves all financial and habit goals established by a specific user from the database.
    Args:
        user_id: The UUID string of the user.
    """
    try:
        goals = _worker.run(_goal_repo.get_all_goals, user_id=user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "count": len(goals),
            "goals": goals
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve user goals: {str(e)}",
            "goals": []
        }


@tool
def edit_user_goal_tool(
    user_id: str,
    goal_id: str,
    task: Optional[str] = None,
    percentage_of_completion: Optional[float] = None
) -> Dict[str, Any]:
    """
    Updates the description or progress percentage of an existing user goal.
    Args:
        user_id: The UUID string of the user.
        goal_id: The UUID string of the goal to update.
        task: Updated goal description if changed.
        percentage_of_completion: Updated completion percentage (0.0 to 100.0).
    """
    try:
        updated = _worker.run(
            _goal_repo.edit_goal,
            user_id=user_id,
            goal_id=goal_id,
            task=task,
            percentage_of_completion=percentage_of_completion
        )
        if updated:
            return {"status": "success", "message": f"Goal '{goal_id}' updated successfully."}
        return {"status": "not_found", "message": f"Goal '{goal_id}' was not found or not modified."}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update goal: {str(e)}"
        }


@tool
def delete_user_goal_tool(user_id: str, goal_id: str) -> Dict[str, Any]:
    """
    Removes a goal from the user's registered goals in the database.
    Args:
        user_id: The UUID string of the user.
        goal_id: The UUID string of the goal to delete.
    """
    try:
        deleted = _worker.run(_goal_repo.delete_goal, user_id=user_id, goal_id=goal_id)
        if deleted:
            return {"status": "success", "message": f"Goal '{goal_id}' deleted successfully."}
        return {"status": "not_found", "message": f"Goal '{goal_id}' was not found."}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to delete goal: {str(e)}"
        }


# =====================================================================
# Stock Portfolio Repository Tools
# =====================================================================
@tool
def get_user_stocks_tool(user_id: str) -> Dict[str, Any]:
    """
    Retrieves the current portfolio stocks held by a user from the database.
    Args:
        user_id: The UUID string of the user.
    """
    try:
        stocks = _worker.run(_stock_repo.get_user_stocks, user_id=user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "count": len(stocks),
            "stocks": stocks
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to retrieve user stocks: {str(e)}",
            "stocks": []
        }


@tool
def insert_user_stock_tool(
    user_id: str,
    symbol: str,
    quantity: float,
    buy_price: float
) -> Dict[str, Any]:
    """
    Records an investment holding into the user's stock portfolio with immutable buy price.
    Args:
        user_id: The UUID string of the user.
        symbol: Stock or asset ticker symbol (e.g. 'RELIANCE', 'TCS', 'NIFTYBEES').
        quantity: Number of units purchased.
        buy_price: Purchase price per unit at execution time.
    """
    stock_payload = {
        "symbol": symbol.strip().upper(),
        "quantity": float(quantity),
        "buy_price": float(buy_price)
    }
    try:
        inserted = _worker.run(
            _stock_repo.insert_user_stock,
            user_id=user_id,
            stock_data=stock_payload
        )
        if inserted:
            return {
                "status": "success",
                "message": f"Stock '{symbol.upper()}' registered successfully.",
                "stock": stock_payload
            }
        return {"status": "failed", "message": f"Could not record stock for user '{user_id}'."}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to insert stock: {str(e)}"
        }


@tool
def delete_user_stock_tool(user_id: str, symbol: str) -> Dict[str, Any]:
    """
    Removes a stock position from the user's holdings list in the database.
    Args:
        user_id: The UUID string of the user.
        symbol: Stock ticker symbol to remove.
    """
    try:
        deleted = _worker.run(
            _stock_repo.delete_user_stock,
            user_id=user_id,
            stock_symbol=symbol
        )
        if deleted:
            return {"status": "success", "message": f"Stock '{symbol.upper()}' deleted successfully."}
        return {"status": "not_found", "message": f"Stock '{symbol.upper()}' was not found in user portfolio."}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to delete stock: {str(e)}"
        }


# =====================================================================
# User Profile Tool
# =====================================================================
def _mask_phone(phone: Any) -> Optional[str]:
    if not phone:
        return None
    text = str(phone)
    return "*" * max(len(text) - 4, 0) + text[-4:]


@tool
def get_user_profile_tool(user_id: str) -> Dict[str, Any]:
    """
    Reads the signed-in user's own profile from the database: name, email, masked phone number,
    how many goals and stock holdings they have, and their recently viewed shares.
    Never returns passwords, tokens or chat history.
    Args:
        user_id: The UUID string of the user.
    """
    try:
        user = _worker.run(_user_repo.get_user_by_id, user_id=user_id)
        if not user:
            return {"status": "not_found", "message": "No profile found for this user."}
        recent: List[str] = []
        for item in (user.get("recently_veiwed_stock") or [])[:10]:
            symbol = item.get("symbol") if isinstance(item, dict) else str(item)
            if symbol:
                recent.append(symbol)
        return {
            "status": "success",
            "profile": {
                "name": user.get("name"),
                "email": user.get("email"),
                "phone_number_masked": _mask_phone(user.get("phone_number")),
                "goals_count": len(user.get("goals") or []),
                "holdings_count": len(user.get("current_list_of_the_stocks") or []),
                "recently_viewed_symbols": recent,
            },
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to read profile: {str(e)}"}


# =====================================================================
# Tool Group Collections
# =====================================================================
GOAL_TOOLS: List[Any] = [
    create_user_goal_tool,
    get_user_goals_tool,
    edit_user_goal_tool,
    delete_user_goal_tool,
]

STOCK_TOOLS: List[Any] = [
    get_user_stocks_tool,
    insert_user_stock_tool,
    delete_user_stock_tool,
]

# Everything the research pipeline reads when a question is about the user themself.
PROFILE_TOOLS: List[Any] = [get_user_profile_tool, get_user_goals_tool, get_user_stocks_tool]

DATABASE_TOOLS: List[Any] = GOAL_TOOLS + STOCK_TOOLS + [get_user_profile_tool]
