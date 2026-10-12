from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

# =====================================================================
# Goal Entry Schema
# =====================================================================
class GoalEntry(BaseModel):
    goal_id: str = Field(..., description="Unique identifier for the goal")
    task: str = Field(..., description="Description of the financial goal or task")
    percentage_of_completion: float = Field(default=0.0, ge=0.0, le=100.0, description="Task progress from 0% to 100%")

# =====================================================================
# Stock Entry Schema
# =====================================================================
class StockEntry(BaseModel):
    symbol: str = Field(..., description="Stock ticker symbol (e.g. RELIANCE, TCS, HDFCBANK)")
    company_name: str = Field(..., description="Full company name")
    quantity: int = Field(default=1, ge=1)
    buy_price: float = Field(..., ge=0.0, description="The purchase execution price per share")
    pnl: Optional[str] = Field(default=None, description="Formatted P&L string, e.g. +₹420 (7.6%)")

# =====================================================================
# Chat Turn Schema
# =====================================================================
class ChatTurn(BaseModel):
    human_response: str = Field(..., description="Message text from the human user")
    ai_response: str = Field(..., description="Response text from the AI copilot")
    timestamp: Optional[str] = Field(default=None)

# =====================================================================
# Complete User Document Schema
# =====================================================================
class UserDocument(BaseModel):
    """
    MongoDB User Document representing a GenZ investor profile,
    their goals, stocks, recently viewed list, and session chat logs.
    """
    user_id: str = Field(..., description="Unique UUID assigned to the user")
    name: str = Field(..., description="Full name of the user")
    phone_number: str = Field(..., description="Mobile contact number")
    refresh_token: Optional[str] = Field(default=None, description="Auth refresh token")
    current_list_of_the_stocks: List[Dict[str, Any]] = Field(default_factory=list)
    goals: List[Dict[str, Any]] = Field(default_factory=list)
    user_chat_history: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    recently_veiwed_stock: List[Dict[str, Any]] = Field(default_factory=list)
