from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import HCP, Interaction
from app.schemas import InteractionCreate, InteractionUpdate
from app.services.llm import analyze_interaction


def interaction_to_dict(interaction: Interaction) -> dict[str, Any]:
    return {
        "id": interaction.id,
        "hcp_id": interaction.hcp_id,
        "hcp_name": interaction.hcp.name if interaction.hcp else None,
        "interaction_type": interaction.interaction_type,
        "channel": interaction.channel,
        "occurred_at": interaction.occurred_at.isoformat(),
        "product_discussed": interaction.product_discussed,
        "objective": interaction.objective,
        "notes": interaction.notes,
        "summary": interaction.summary,
        "sentiment": interaction.sentiment,
        "commitment": interaction.commitment,
        "next_step": interaction.next_step,
        "follow_up_date": interaction.follow_up_date,
        "compliance_flags": interaction.compliance_flags,
        "entities": interaction.entities,
    }


def log_interaction_tool(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    data = InteractionCreate(**payload)
    hcp = db.get(HCP, data.hcp_id)
    if not hcp:
        raise ValueError("HCP not found")

    analysis = analyze_interaction(data.notes, data.product_discussed)
    interaction = Interaction(
        hcp_id=data.hcp_id,
        interaction_type=data.interaction_type,
        channel=data.channel,
        occurred_at=data.occurred_at or datetime.utcnow(),
        product_discussed=data.product_discussed,
        objective=data.objective,
        notes=data.notes,
        summary=analysis.get("summary", ""),
        sentiment=analysis.get("sentiment", "neutral"),
        commitment=data.commitment,
        next_step=data.next_step,
        follow_up_date=data.follow_up_date,
        compliance_flags=analysis.get("compliance_flags", []),
        entities=analysis.get("entities", {}),
    )
    hcp.last_contacted_at = interaction.occurred_at
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return {"message": "Interaction logged with LLM summary and entity extraction.", "interaction": interaction_to_dict(interaction)}


def edit_interaction_tool(db: Session, interaction_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    interaction = db.get(Interaction, interaction_id)
    if not interaction:
        raise ValueError("Interaction not found")

    update = InteractionUpdate(**payload)
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(interaction, field, value)
    if update.notes or update.product_discussed:
        analysis = analyze_interaction(interaction.notes, interaction.product_discussed)
        interaction.summary = analysis.get("summary", interaction.summary)
        interaction.sentiment = analysis.get("sentiment", interaction.sentiment)
        interaction.entities = analysis.get("entities", interaction.entities)
        interaction.compliance_flags = analysis.get("compliance_flags", interaction.compliance_flags)
    interaction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(interaction)
    return {"message": "Interaction edited and AI analysis refreshed.", "interaction": interaction_to_dict(interaction)}


def suggest_next_best_action_tool(db: Session, hcp_id: int) -> dict[str, Any]:
    hcp = db.get(HCP, hcp_id)
    if not hcp:
        raise ValueError("HCP not found")
    latest = (
        db.query(Interaction)
        .filter(Interaction.hcp_id == hcp_id)
        .order_by(Interaction.occurred_at.desc())
        .first()
    )
    if not latest:
        action = f"Schedule an introductory {hcp.preferred_channel.lower()} call focused on unmet needs in {hcp.specialty}."
    elif latest.sentiment == "positive":
        action = f"Send clinical evidence and book a follow-up to convert {hcp.name}'s interest into a clear next commitment."
    elif latest.sentiment == "cautious":
        action = f"Address the recorded objection with approved medical content before the next product discussion."
    else:
        action = f"Follow up through {hcp.preferred_channel} and clarify patient profile fit."
    return {"hcp": hcp.name, "next_best_action": action}


def schedule_follow_up_tool(db: Session, hcp_id: int, days_from_now: int = 7, purpose: str = "Follow up") -> dict[str, Any]:
    hcp = db.get(HCP, hcp_id)
    if not hcp:
        raise ValueError("HCP not found")
    due_date = (datetime.utcnow() + timedelta(days=days_from_now)).date().isoformat()
    return {
        "hcp": hcp.name,
        "due_date": due_date,
        "channel": hcp.preferred_channel,
        "purpose": purpose,
        "message": "Follow-up task created for rep planning.",
    }


def retrieve_hcp_profile_tool(db: Session, hcp_id: int) -> dict[str, Any]:
    hcp = db.get(HCP, hcp_id)
    if not hcp:
        raise ValueError("HCP not found")
    interactions = (
        db.query(Interaction)
        .filter(Interaction.hcp_id == hcp_id)
        .order_by(Interaction.occurred_at.desc())
        .limit(5)
        .all()
    )
    return {
        "id": hcp.id,
        "name": hcp.name,
        "specialty": hcp.specialty,
        "territory": hcp.territory,
        "segment": hcp.segment,
        "preferred_channel": hcp.preferred_channel,
        "recent_interactions": [interaction_to_dict(item) for item in interactions],
    }


def check_compliance_tool(text: str) -> dict[str, Any]:
    analysis = analyze_interaction(text)
    status = "review_required" if analysis.get("compliance_flags") else "clear"
    return {"status": status, "flags": analysis.get("compliance_flags", []), "checked_text": text}


def summarize_history_tool(db: Session, hcp_id: int) -> dict[str, Any]:
    hcp = db.get(HCP, hcp_id)
    if not hcp:
        raise ValueError("HCP not found")
    interactions = (
        db.query(Interaction)
        .filter(Interaction.hcp_id == hcp_id)
        .order_by(Interaction.occurred_at.desc())
        .limit(10)
        .all()
    )
    summaries = [item.summary for item in interactions]
    return {
        "hcp": hcp.name,
        "interaction_count": len(interactions),
        "history_summary": " ".join(summaries) if summaries else "No interactions logged yet.",
    }
