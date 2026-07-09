import json
import re
from typing import Any

from app.config import get_settings


TOOL_NAMES = {
    "log_interaction",
    "edit_interaction",
    "suggest_next_best_action",
    "schedule_follow_up",
    "retrieve_hcp_profile",
    "check_compliance",
    "summarize_history",
}


def _call_groq_json(prompt: str) -> dict[str, Any] | None:
    settings = get_settings()
    if not settings.groq_api_key:
        return None

    try:
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)
        completion = client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(completion.choices[0].message.content or "{}")
    except Exception:
        return None


def _fallback_analysis(notes: str, product: str = "") -> dict[str, Any]:
    lowered = notes.lower()
    flags = []
    if "off-label" in lowered or "guarantee" in lowered or "cash" in lowered or "gift" in lowered:
        flags.append("Potential compliance-sensitive language detected")
    sentiment = "positive" if any(word in lowered for word in ["interested", "positive", "agreed", "adopt"]) else "neutral"
    if any(word in lowered for word in ["concern", "barrier", "not convinced", "issue"]):
        sentiment = "cautious"

    return {
        "summary": f"Discussed {product or 'the therapy'} with the HCP. Key notes: {notes[:220]}",
        "sentiment": sentiment,
        "entities": {
            "products": [product] if product else [],
            "objections": [phrase for phrase in ["cost", "efficacy", "safety", "availability"] if phrase in lowered],
            "commitments": [phrase for phrase in ["sample", "follow up", "patient profile", "clinical paper"] if phrase in lowered],
        },
        "compliance_flags": flags,
    }


def analyze_interaction(notes: str, product: str = "") -> dict[str, Any]:
    prompt = f"""
You are a life-sciences CRM assistant. Analyze this HCP interaction note.
Return only JSON with keys: summary, sentiment, entities, compliance_flags.
Product: {product}
Notes: {notes}
"""
    result = _call_groq_json(prompt)
    return result or _fallback_analysis(notes, product)


def select_agent_tool(message: str) -> dict[str, str]:
    prompt = f"""
You are routing a field representative's CRM request to one LangGraph tool.
Allowed tools: {", ".join(sorted(TOOL_NAMES))}.
Return only JSON with keys: tool_name, routing_reason.
Message: {message}
"""
    result = _call_groq_json(prompt)
    if result and result.get("tool_name") in TOOL_NAMES:
        return {
            "tool_name": result["tool_name"],
            "routing_reason": result.get("routing_reason", "Groq selected the most relevant CRM tool."),
        }

    lowered = message.lower()
    if "edit" in lowered or "update" in lowered or "modify" in lowered:
        return {"tool_name": "edit_interaction", "routing_reason": "Fallback matched edit/update intent."}
    if "next best" in lowered or "recommend" in lowered or "what should i do" in lowered:
        return {"tool_name": "suggest_next_best_action", "routing_reason": "Fallback matched next-best-action intent."}
    if "schedule" in lowered or "follow-up" in lowered or "follow up" in lowered:
        return {"tool_name": "schedule_follow_up", "routing_reason": "Fallback matched follow-up scheduling intent."}
    if "profile" in lowered or "hcp details" in lowered:
        return {"tool_name": "retrieve_hcp_profile", "routing_reason": "Fallback matched HCP profile lookup intent."}
    if "compliance" in lowered or "check" in lowered or "off-label" in lowered or "gift" in lowered:
        return {"tool_name": "check_compliance", "routing_reason": "Fallback matched compliance review intent."}
    if "history" in lowered or "summarize" in lowered:
        return {"tool_name": "summarize_history", "routing_reason": "Fallback matched history summary intent."}
    return {"tool_name": "log_interaction", "routing_reason": "Fallback treated the message as a new interaction note."}


def extract_interaction_payload(message: str, hcp_id: int, default_product: str = "CardioGuard") -> dict[str, Any]:
    prompt = f"""
Convert this field-rep chat note into structured CRM interaction JSON.
Return only JSON with keys: interaction_type, channel, product_discussed, objective, notes, commitment, next_step, follow_up_date.
If a field is not explicitly present, infer a practical compliant value.
Message: {message}
"""
    result = _call_groq_json(prompt) or {}
    lowered = message.lower()
    product = result.get("product_discussed") or default_product
    channel = result.get("channel") or ("Email" if "email" in lowered else "Phone" if "call" in lowered else "Chat")
    follow_up = result.get("follow_up_date") or ""
    if not follow_up and "next week" in lowered:
        follow_up = "next week"

    return {
        "hcp_id": hcp_id,
        "interaction_type": result.get("interaction_type") or "Conversational Log",
        "channel": channel,
        "product_discussed": product,
        "objective": result.get("objective") or "Capture HCP interaction from conversational input",
        "notes": result.get("notes") or message,
        "commitment": result.get("commitment") or _extract_commitment(message),
        "next_step": result.get("next_step") or "Review AI summary and complete the planned follow-up",
        "follow_up_date": follow_up,
    }


def _extract_commitment(message: str) -> str:
    match = re.search(r"requested? ([^.]+)", message, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    if "follow" in message.lower():
        return "Follow-up requested"
    return ""
