from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import HCP, Interaction
from app.services.agent import AGENT_TOOL_NAMES, run_agent
from app.services.tools import (
    check_compliance_tool,
    edit_interaction_tool,
    log_interaction_tool,
    suggest_next_best_action_tool,
)


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = session_factory()
    db.add(
        HCP(
            name="Dr. Test HCP",
            specialty="Cardiology",
            territory="Test Territory",
            segment="A",
            preferred_channel="In-person",
        )
    )
    db.commit()
    return db


def sample_payload(hcp_id: int = 1):
    return {
        "hcp_id": hcp_id,
        "interaction_type": "Detailing Call",
        "channel": "In-person",
        "product_discussed": "CardioGuard",
        "objective": "Discuss appropriate patient profiles",
        "notes": "HCP was interested in safety evidence and requested follow up.",
        "commitment": "Review approved evidence",
        "next_step": "Share clinical deck",
        "follow_up_date": "",
    }


def test_log_interaction_enriches_and_persists_record():
    db = make_session()

    result = log_interaction_tool(db, sample_payload())

    interaction = result["interaction"]
    assert interaction["id"] == 1
    assert interaction["hcp_name"] == "Dr. Test HCP"
    assert interaction["summary"]
    assert interaction["sentiment"] in {"positive", "neutral", "cautious"}
    assert db.query(Interaction).count() == 1


def test_edit_interaction_refreshes_ai_fields():
    db = make_session()
    created = log_interaction_tool(db, sample_payload())["interaction"]

    result = edit_interaction_tool(
        db,
        created["id"],
        {"notes": "Updated note with a safety concern and request for approved evidence."},
    )

    assert result["interaction"]["notes"].startswith("Updated note")
    assert result["interaction"]["summary"]
    assert result["message"] == "Interaction edited and AI analysis refreshed."


def test_compliance_tool_flags_sensitive_language():
    result = check_compliance_tool("The HCP asked about off-label use and a gift.")

    assert result["status"] == "review_required"
    assert result["flags"]


def test_next_best_action_uses_hcp_context():
    db = make_session()

    result = suggest_next_best_action_tool(db, 1)

    assert result["hcp"] == "Dr. Test HCP"
    assert "next_best_action" in result


def test_langgraph_forced_tools_execute_all_registered_nodes():
    db = make_session()
    created = log_interaction_tool(db, sample_payload())["interaction"]

    payloads = {
        "log_interaction": sample_payload(),
        "edit_interaction": {"interaction_id": created["id"], "notes": "Edited through LangGraph."},
        "suggest_next_best_action": {"hcp_id": 1},
        "schedule_follow_up": {"hcp_id": 1, "days_from_now": 3, "purpose": "Evidence follow-up"},
        "retrieve_hcp_profile": {"hcp_id": 1},
        "check_compliance": {"text": "Check off-label wording."},
        "summarize_history": {"hcp_id": 1},
    }

    assert len(AGENT_TOOL_NAMES) >= 5
    for tool_name, payload in payloads.items():
        output = run_agent(
            db,
            f"Demo exact tool {tool_name}",
            payload,
            hcp_id=payload.get("hcp_id"),
            interaction_id=payload.get("interaction_id"),
            forced_tool=tool_name,
        )
        assert output["selected_tool"] == tool_name
        assert output["result"]["routing_reason"]
