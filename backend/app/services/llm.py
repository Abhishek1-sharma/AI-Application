import json
from typing import Any

from app.config import get_settings


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
    settings = get_settings()
    if not settings.groq_api_key:
        return _fallback_analysis(notes, product)

    try:
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)
        prompt = f"""
You are a life-sciences CRM assistant. Analyze this HCP interaction note.
Return only JSON with keys: summary, sentiment, entities, compliance_flags.
Product: {product}
Notes: {notes}
"""
        completion = client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return json.loads(completion.choices[0].message.content or "{}")
    except Exception:
        return _fallback_analysis(notes, product)
