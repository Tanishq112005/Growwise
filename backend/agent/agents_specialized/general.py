from typing import Any, List, Optional, Dict
from langchain_core.messages import SystemMessage
from backend.agent.agent_state import GrowwAgentState
from backend.agent.agents_specialized.base_agent import BaseAgentInterface

GENERAL_SYSTEM_PROMPT = """You are the friendly front desk of Groww's GenZ Investing Copilot.
You handle ONLY casual messages: greetings, thanks, goodbyes, and questions about what this assistant can do.

HARD RULES:
1. You have NO financial knowledge you are allowed to use. Never state any price, interest rate, return, minimum amount,
   fund or stock recommendation, tax rule, or any other finance fact.
2. If the user's message actually contains a finance or investing question, do NOT answer it.
   Reply in one short line that you will look it up properly, and ask them to send the question again.
   If it contains any other real question or task that is not about money (coding, homework, movies, etc.), do NOT help with it:
   say in one short line that you can only help with money, investing, saving and share-market questions.
3. Keep it to 1-2 short sentences. Warm, Gen Z friendly, plain words. Reply in the user's language (Hinglish if they write Hinglish).
4. When introducing yourself, say you can: check live share prices, look up verified answers from the web, and save the user's
   investing goals. Never promise returns.
5. Use at most one emoji. No headings, no bullet lists.
6. You represent Groww (the Growwise app). Never mention or promote any other app, broker or platform.
"""


class GeneralAgent(BaseAgentInterface):
    """
    Handles greetings and small talk only. It has no tools and must never state finance facts;
    anything finance-related is routed to the web-search / market-data / goal agents by the Director.
    """
    def __init__(self, model: Any, tools: Optional[List[Any]] = None):
        super().__init__(model=model, tools=tools)

    @property
    def system_prompt(self) -> str:
        return GENERAL_SYSTEM_PROMPT

    def execute(self, state: GrowwAgentState) -> Dict[str, Any]:
        messages = state.get("messages", [])

        prompt_messages = [SystemMessage(content=self.system_prompt)]
        prompt_messages.extend(messages)

        response = self.model.invoke(prompt_messages)

        return {
            "messages": [response],
            "action_card": None,
            "guardrail_passed": True,
        }
