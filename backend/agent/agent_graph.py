from typing import Any, Dict, AsyncGenerator, Generator, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage

from backend.agent.agent_state import GrowwAgentState
from backend.agent.checkpointer import RedisCheckpointerManager
from backend.config.chat_model import ChatModelManager
from backend.agent.agents_specialized import (
    DirectorAgent,
    GoalAgent,
    GeneralAgent,
    ResearchPipeline,
)
from backend.agent.agents_specialized.response_style import OFF_TOPIC_MESSAGE

# =====================================================================
# Main Agent Graph Class: GrowwAgentGraph
# =====================================================================
class GrowwAgentGraph:
    """
    Core Agent Graph orchestrator for Growwise (Groww GenZ).

        START -> director -> general   -> END      (greetings only)
                          -> off_topic -> END      (guardrail: not about money)
                          -> goal      -> END      (save / edit / delete goals)
                          -> gather -> coverage -> answer -> END      (every finance question)
                              ^           |
                              +-----------+   (coverage asks for more data, at most one extra round)

    `gather` fetches every needed source (live share quotes, web search, the user's profile),
    `coverage` asks the model whether the data covers EVERY part of the question,
    and `answer` writes the reply using only that data.
    """
    def __init__(self, model: Optional[Any] = None):
        self._checkpointer_manager = RedisCheckpointerManager.get_instance()

        # Reuse supplied model or fetch singleton model to prevent duplicate initialization
        self.model = model or ChatModelManager.get_instance().get_chat_model()

        self.director = DirectorAgent(model=self.model)
        self.goal_agent = GoalAgent(model=self.model)
        self.general_agent = GeneralAgent(model=self.model)
        self.research = ResearchPipeline(model=self.model)

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------
    def _director_node(self, state: GrowwAgentState) -> Dict[str, Any]:
        """Routes user intent and plans the data sources using DirectorAgent classification."""
        print("\n[AgentGraph] >>> Step 1: DirectorAgent analyzing query...")
        result = self.director.route(state)
        print(
            f"[AgentGraph] >>> Director routed to: '{result.get('current_intent')}' "
            f"needs={result.get('needs')} tickers={result.get('tickers')}"
        )
        return result

    def _goal_node(self, state: GrowwAgentState) -> Dict[str, Any]:
        """Executes goal create / read / edit / delete logic."""
        print("[AgentGraph] >>> Executing Specialized Agent: GoalAgent")
        return self.goal_agent.execute(state)

    def _general_node(self, state: GrowwAgentState) -> Dict[str, Any]:
        """Handles greetings and small talk only (no finance facts, no tools)."""
        print("[AgentGraph] >>> Executing Specialized Agent: GeneralAgent")
        return self.general_agent.execute(state)

    def _off_topic_node(self, state: GrowwAgentState) -> Dict[str, Any]:
        """Guardrail: non-finance questions get a fixed polite refusal (no model call, no tools)."""
        print("[AgentGraph] >>> Guardrail: off-topic question blocked")
        return {
            "messages": [AIMessage(content=OFF_TOPIC_MESSAGE)],
            "action_card": None,
            "guardrail_passed": False,
        }

    def _gather_node(self, state: GrowwAgentState) -> Dict[str, Any]:
        """Collects live quotes, web results and the user's profile, as planned."""
        print("[AgentGraph] >>> Research: gathering data")
        return self.research.gather(state)

    def _coverage_node(self, state: GrowwAgentState) -> Dict[str, Any]:
        """Asks the model whether the collected data covers every part of the question."""
        print("[AgentGraph] >>> Research: checking coverage")
        return self.research.coverage(state)

    def _answer_node(self, state: GrowwAgentState) -> Dict[str, Any]:
        """Writes the final answer from the collected data only."""
        print("[AgentGraph] >>> Research: writing answer")
        return self.research.answer(state)

    # ------------------------------------------------------------------
    # Routing conditions
    # ------------------------------------------------------------------
    def _route_condition(self, state: GrowwAgentState) -> str:
        """Determines the next node transition based on current_intent in state."""
        intent = state.get("current_intent", "research")
        valid_routes = {"general", "goal", "research", "off_topic"}
        # Unknown intents fall back to the data-grounded research path, never to model memory.
        return intent if intent in valid_routes else "research"

    def _after_coverage(self, state: GrowwAgentState) -> str:
        """Loops back to gather when the completeness check asked for more data."""
        return "gather" if state.get("coverage_incomplete") else "answer"

    def build_graph(self) -> StateGraph:
        """Constructs the LangGraph state machine with nodes and conditional edges."""
        workflow = StateGraph(GrowwAgentState)

        # 1. Register Nodes
        workflow.add_node("director", self._director_node)
        workflow.add_node("general", self._general_node)
        workflow.add_node("off_topic", self._off_topic_node)
        workflow.add_node("goal", self._goal_node)
        workflow.add_node("gather", self._gather_node)
        workflow.add_node("coverage", self._coverage_node)
        workflow.add_node("answer", self._answer_node)

        # 2. Wire Entry Edge
        workflow.add_edge(START, "director")

        # 3. Director decides the path
        workflow.add_conditional_edges(
            "director",
            self._route_condition,
            {
                "general": "general",
                "off_topic": "off_topic",
                "goal": "goal",
                "research": "gather",
            }
        )

        # 4. Research loop: gather -> coverage -> (gather again | answer)
        workflow.add_edge("gather", "coverage")
        workflow.add_conditional_edges(
            "coverage",
            self._after_coverage,
            {"gather": "gather", "answer": "answer"},
        )

        # 5. Terminal Edges
        workflow.add_edge("general", END)
        workflow.add_edge("off_topic", END)
        workflow.add_edge("goal", END)
        workflow.add_edge("answer", END)

        return workflow

    def get_compiled_graph(self, user_id: str) -> Any:
        """
        Compiles and returns the LangGraph workflow with a Redis checkpointer
        dedicated to the provided user UUID.
        """
        if not user_id:
            raise ValueError("user_id (UUID) must be provided to compile the user graph.")

        # The checkpointer is shared and conversations are isolated by thread_id, so the
        # graph only needs to be built and compiled once instead of on every request.
        if getattr(self, "_compiled_graph", None) is None:
            workflow = self.build_graph()
            checkpointer = self._checkpointer_manager.get_checkpointer(user_id=user_id)
            self._compiled_graph = workflow.compile(checkpointer=checkpointer)
        return self._compiled_graph

    async def astream_graph(
        self,
        user_id: str,
        input_state: Dict[str, Any],
        stream_mode: str = "messages"
    ) -> AsyncGenerator[Any, None]:
        """
        Asynchronously streams execution chunks (tokens or state updates) from the compiled graph.
        """
        compiled_graph = self.get_compiled_graph(user_id=user_id)
        config = {"configurable": {"thread_id": user_id}}

        async for chunk in compiled_graph.astream(input_state, config=config, stream_mode=stream_mode):
            yield chunk

    def stream_graph(
        self,
        user_id: str,
        input_state: Dict[str, Any],
        stream_mode: str = "messages"
    ) -> Generator[Any, None, None]:
        """
        Synchronously streams execution chunks from the compiled graph.
        """
        compiled_graph = self.get_compiled_graph(user_id=user_id)
        config = {"configurable": {"thread_id": user_id}}

        for chunk in compiled_graph.stream(input_state, config=config, stream_mode=stream_mode):
            yield chunk
