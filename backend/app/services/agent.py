from typing import Any, TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.models import AgentRun
from app.services.llm import select_agent_tool
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
    forced_tool: str | None
    selected_tool: str
    routing_reason: str
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

AGENT_TOOL_NAMES = {tool.name for tool in AGENT_TOOLS}


def build_agent(db: Session):
    graph = StateGraph(AgentState)

    def router_node(state: AgentState) -> AgentState:
        if state.get("forced_tool"):
            if state["forced_tool"] not in AGENT_TOOL_NAMES:
                raise ValueError(f"Unknown LangGraph tool: {state['forced_tool']}")
            return {
                **state,
                "selected_tool": str(state["forced_tool"]),
                "routing_reason": "Tool was selected directly from the demo panel.",
            }
        selection = select_agent_tool(state["message"])
        if state.get("interaction_id") and selection["tool_name"] == "log_interaction":
            selection = {
                "tool_name": "edit_interaction",
                "routing_reason": "Interaction id was supplied, so LangGraph routed to edit_interaction.",
            }
        return {
            **state,
            "selected_tool": selection["tool_name"],
            "routing_reason": selection["routing_reason"],
        }

    def _run_selected_tool(state: AgentState, expected_tool: str) -> AgentState:
        tool_name = state["selected_tool"]
        if tool_name != expected_tool:
            raise ValueError(f"LangGraph routed to {tool_name}, but node {expected_tool} was invoked")
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

        result = {**result, "routing_reason": state.get("routing_reason", "")}
        db.add(AgentRun(user_message=state["message"], selected_tool=tool_name, result=result))
        db.commit()
        return {**state, "result": result}

    graph.add_node("router", router_node)
    graph.add_node("log_interaction", lambda state: _run_selected_tool(state, "log_interaction"))
    graph.add_node("edit_interaction", lambda state: _run_selected_tool(state, "edit_interaction"))
    graph.add_node("suggest_next_best_action", lambda state: _run_selected_tool(state, "suggest_next_best_action"))
    graph.add_node("schedule_follow_up", lambda state: _run_selected_tool(state, "schedule_follow_up"))
    graph.add_node("retrieve_hcp_profile", lambda state: _run_selected_tool(state, "retrieve_hcp_profile"))
    graph.add_node("check_compliance", lambda state: _run_selected_tool(state, "check_compliance"))
    graph.add_node("summarize_history", lambda state: _run_selected_tool(state, "summarize_history"))
    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        lambda state: state["selected_tool"],
        {
            "log_interaction": "log_interaction",
            "edit_interaction": "edit_interaction",
            "suggest_next_best_action": "suggest_next_best_action",
            "schedule_follow_up": "schedule_follow_up",
            "retrieve_hcp_profile": "retrieve_hcp_profile",
            "check_compliance": "check_compliance",
            "summarize_history": "summarize_history",
        },
    )
    for tool_name in AGENT_TOOL_NAMES:
        graph.add_edge(tool_name, END)
    return graph.compile()


def run_agent(
    db: Session,
    message: str,
    payload: dict[str, Any],
    hcp_id: int | None = None,
    interaction_id: int | None = None,
    forced_tool: str | None = None,
) -> dict[str, Any]:
    agent = build_agent(db)
    state = agent.invoke(
        {
            "message": message,
            "payload": payload,
            "hcp_id": hcp_id,
            "interaction_id": interaction_id,
            "forced_tool": forced_tool,
            "selected_tool": "",
            "routing_reason": "",
            "result": {},
        }
    )
    return {
        "selected_tool": state["selected_tool"],
        "routing_reason": state["routing_reason"],
        "result": state["result"],
    }
