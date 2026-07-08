from typing import Any, Literal, TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.models import AgentRun
from app.services.tools import (
    check_compliance_tool,
    edit_interaction_tool,
    log_interaction_tool,
    retrieve_hcp_profile_tool,
    schedule_follow_up_tool,
    suggest_next_best_action_tool,
    summarize_history_tool,
)


class AgentState(TypedDict):
    message: str
    hcp_id: int | None
    interaction_id: int | None
    payload: dict[str, Any]
    selected_tool: str
    result: dict[str, Any]


@tool
def log_interaction(payload: dict[str, Any]) -> str:
    """Capture HCP interaction data and enrich it with LLM summary, sentiment, entities, and compliance flags."""
    return "log_interaction"


@tool
def edit_interaction(interaction_id: int, payload: dict[str, Any]) -> str:
    """Modify an existing HCP interaction and refresh AI-generated fields when notes change."""
    return "edit_interaction"


@tool
def suggest_next_best_action(hcp_id: int) -> str:
    """Recommend the next best sales action based on HCP profile, history, sentiment, and commitments."""
    return "suggest_next_best_action"


@tool
def schedule_follow_up(hcp_id: int, days_from_now: int, purpose: str) -> str:
    """Create a follow-up task with due date, channel, and purpose for the field representative."""
    return "schedule_follow_up"


@tool
def retrieve_hcp_profile(hcp_id: int) -> str:
    """Retrieve HCP profile information and recent interaction context."""
    return "retrieve_hcp_profile"


@tool
def check_compliance(text: str) -> str:
    """Check rep notes for compliance-sensitive language before saving or follow-up."""
    return "check_compliance"


@tool
def summarize_history(hcp_id: int) -> str:
    """Summarize recent HCP interaction history for pre-call planning."""
    return "summarize_history"


AGENT_TOOLS = [
    log_interaction,
    edit_interaction,
    suggest_next_best_action,
    schedule_follow_up,
    retrieve_hcp_profile,
    check_compliance,
    summarize_history,
]


def _route_tool(state: AgentState) -> Literal[
    "log_interaction",
    "edit_interaction",
    "suggest_next_best_action",
    "schedule_follow_up",
    "retrieve_hcp_profile",
    "check_compliance",
    "summarize_history",
]:
    message = state["message"].lower()
    if "edit" in message or "update" in message or state.get("interaction_id"):
        return "edit_interaction"
    if "next best" in message or "recommend" in message or "what should i do" in message:
        return "suggest_next_best_action"
    if "schedule" in message or "follow-up" in message or "follow up" in message:
        return "schedule_follow_up"
    if "profile" in message or "hcp details" in message:
        return "retrieve_hcp_profile"
    if "compliance" in message or "check" in message:
        return "check_compliance"
    if "history" in message or "summarize" in message:
        return "summarize_history"
    return "log_interaction"


def build_agent(db: Session):
    graph = StateGraph(AgentState)

    def router_node(state: AgentState) -> AgentState:
        return {**state, "selected_tool": _route_tool(state)}

    def execute_node(state: AgentState) -> AgentState:
        tool_name = state["selected_tool"]
        payload = state.get("payload") or {}
        hcp_id = state.get("hcp_id") or payload.get("hcp_id") or 1
        interaction_id = state.get("interaction_id") or payload.get("interaction_id")

        if tool_name == "log_interaction":
            result = log_interaction_tool(db, payload)
        elif tool_name == "edit_interaction":
            if not interaction_id:
                raise ValueError("interaction_id is required for edit_interaction")
            result = edit_interaction_tool(db, int(interaction_id), payload)
        elif tool_name == "suggest_next_best_action":
            result = suggest_next_best_action_tool(db, int(hcp_id))
        elif tool_name == "schedule_follow_up":
            result = schedule_follow_up_tool(
                db,
                int(hcp_id),
                int(payload.get("days_from_now", 7)),
                str(payload.get("purpose", "Follow up after HCP discussion")),
            )
        elif tool_name == "retrieve_hcp_profile":
            result = retrieve_hcp_profile_tool(db, int(hcp_id))
        elif tool_name == "check_compliance":
            result = check_compliance_tool(str(payload.get("text") or state["message"]))
        else:
            result = summarize_history_tool(db, int(hcp_id))

        db.add(AgentRun(user_message=state["message"], selected_tool=tool_name, result=result))
        db.commit()
        return {**state, "result": result}

    graph.add_node("router", router_node)
    graph.add_node("execute_tool", execute_node)
    graph.set_entry_point("router")
    graph.add_edge("router", "execute_tool")
    graph.add_edge("execute_tool", END)
    return graph.compile()


def run_agent(db: Session, message: str, payload: dict[str, Any], hcp_id: int | None = None, interaction_id: int | None = None) -> dict[str, Any]:
    agent = build_agent(db)
    state = agent.invoke(
        {
            "message": message,
            "payload": payload,
            "hcp_id": hcp_id,
            "interaction_id": interaction_id,
            "selected_tool": "",
            "result": {},
        }
    )
    return {"selected_tool": state["selected_tool"], "result": state["result"]}
