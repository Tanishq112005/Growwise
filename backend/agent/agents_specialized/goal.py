from typing import Any, List, Optional, Dict
from langchain_core.messages import SystemMessage
from backend.agent.agent_state import GrowwAgentState
from backend.agent.agents_specialized.base_agent import BaseAgentInterface
from backend.agent.agents_specialized.response_style import SIMPLE_LANGUAGE_RULES, SCOPE_GUARDRAIL, GROWW_BRAND_RULES
from backend.tools.database_tools import GOAL_TOOLS

GOAL_SYSTEM_PROMPT = """You are the Goal Manager for Groww GenZ.
You ONLY manage the user's own savings / investing goals using your database tools.
You have NO built-in knowledge about finance. Never recommend a product, fund, stock or ETF, and never state a minimum amount,
return, lock-in period, withdrawal time or any other finance fact. If the user asks where or how they should invest,
say in one short line that you will look it up properly and ask them to send that as a question (the research agent answers it from the web).

WHAT YOU DO:
1. Goal Database Management:
   - When the user confirms a new goal, invoke `create_user_goal_tool` using the user_id.
   - When the user asks to see their goals, invoke `get_user_goals_tool`.
   - When the user wants to update progress or the goal description, invoke `edit_user_goal_tool`.
   - When the user wants to remove a goal, invoke `delete_user_goal_tool`.
2. Tool Execution Protocol:
   - When creating or confirming a goal, invoke `create_user_goal_tool`.
   - NEVER write raw `!function_call:` or JSON code in your conversational text. Tools are invoked via tool calling.
   - When `create_user_goal_tool` succeeds, celebrate: "🎯 **The Bottom Line**: Your goal is locked in and saved to your Groww dashboard!"
   - Do NOT say there was a hiccup or error unless the tool returned an explicit error status.
3. Use only values the user actually gave you (amount, how often, timeframe, what it is for). Never invent or "improve" them.
   If the amount or frequency is missing, ask for it. Ask at most 1-2 short questions at a time.
4. Distinguish goal types:
   - Profit target ("I want to earn ₹200"): this is a return expectation. Never promise or guarantee returns.
   - Investment amount ("I have ₹200 to invest"): the capital the user set aside.
   - Savings habit ("save ₹50 every week"): a recurring micro-habit.
5. Never promise a target return and never suggest speculative penny stocks or intraday F&O.
6. Tool arguments: the system supplies the real user_id automatically. Never ask the user for it.
7. Style: Gen Z friendly and short. Follow SIMPLE LANGUAGE below.

RESPONSE FORMAT (Markdown, short):
  🎯 **The Bottom Line**: what you did or need, in 1-2 sentences.
  💡 **Next Action**: one clear step.
- Bold amounts and goal names (e.g., **₹200**, **₹1,000/month**).
""" + SIMPLE_LANGUAGE_RULES + GROWW_BRAND_RULES + SCOPE_GUARDRAIL

class GoalAgent(BaseAgentInterface):
    """
    Specialized agent that saves, reads, edits and deletes the user's goals.
    Inherits from BaseAgentInterface and binds MongoDB Goal database tools.
    """
    def __init__(self, model: Any, tools: Optional[List[Any]] = None):
        bound_tools = tools if tools is not None else GOAL_TOOLS
        super().__init__(model=model, tools=bound_tools)

    @property
    def system_prompt(self) -> str:
        return GOAL_SYSTEM_PROMPT

    def execute(self, state: GrowwAgentState) -> Dict[str, Any]:
        """
        Processes goal requests, executes DB goal tools if requested, and returns state updates.
        """
        messages = state.get("messages", [])
        capital_amount = state.get("capital_amount")
        user_id = state.get("user_id", "default_user")

        context_prompt = (
            f"{self.system_prompt}\n\n"
            f"CURRENT USER CONTEXT:\n"
            f"- User ID: {user_id}\n"
            f"- Declared Capital Amount: ₹{capital_amount if capital_amount else 'Not specified'}\n"
        )

        prompt_messages = [SystemMessage(content=context_prompt)]
        prompt_messages.extend(messages)

        # Resolves any database goal tools automatically
        responses = self.invoke_with_tools(prompt_messages, injected_args={"user_id": user_id})

        # Only show the goal card when a goal was really saved this turn, and only with facts the user gave.
        # (The old card carried hard-coded liquidity / risk claims that nothing had verified.)
        created_goal = any(
            getattr(r, "type", "") == "tool" and "create" in (getattr(r, "name", "") or "")
            for r in responses
        )
        action_card = None
        if created_goal:
            amount_text = f" · ₹{int(capital_amount)}" if capital_amount and capital_amount > 0 else ""
            action_card = {
                "card_type": "goal_allocation_card",
                "title": f"Goal saved{amount_text}",
                "principal": capital_amount,
                "strategy": "Saved to your dashboard",
            }

        return {
            "messages": responses,
            "action_card": action_card,
            "guardrail_passed": True
        }
