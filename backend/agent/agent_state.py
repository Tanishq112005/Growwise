from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# =====================================================================
# LangGraph Agent State Definition
# =====================================================================
class GrowwAgentState(TypedDict):
    """
    State schema for the Groww GenZ Agentic Graph.
    Uses LangGraph's standard messages list to store HumanMessage, AIMessage,
    SystemMessage, and ToolMessage in sequence.
    """
    # Standard LangGraph message stream (contains HumanMessage, AIMessage, etc.)
    messages: Annotated[List[BaseMessage], add_messages]

    # User and session UUID identifiers
    user_id: str
    session_id: str

    # Contextual GenZ metadata
    user_persona: Optional[str]        # e.g., 'college_student', 'intern', 'first_jobber'
    current_intent: Optional[str]      # e.g., 'micro_sip', 'hype_check', 'fno_warning'
    capital_amount: Optional[float]    # e.g., 200.0, 700.0
    detected_ticker: Optional[str]     # e.g., 'RELIANCE', 'TCS' (set by the Director)
    search_query: Optional[str]        # standalone web-search query written by the Director

    # Research pipeline (gather -> completeness check -> answer). Reset by the Director every turn.
    needs: Optional[List[str]]         # sources to fetch now: 'market', 'web', 'profile'
    tickers: Optional[List[str]]       # share tickers to quote (market source)
    evidence: Optional[Dict[str, Any]] # data collected so far: profile / market quotes / web results
    coverage_attempts: Optional[int]   # how many completeness checks have run this turn
    coverage_incomplete: Optional[bool]# True when the checker wants another gather round
    gaps: Optional[str]                # what the checker says is still not covered

    # Generative UI card for the frontend. MUST be declared here: LangGraph silently
    # drops node outputs whose keys are not part of the state schema.
    action_card: Optional[Dict[str, Any]]

    # Anti-hallucination and SEBI guardrail execution flags
    guardrail_passed: Optional[bool]
    guardrail_details: Optional[Dict[str, Any]]
