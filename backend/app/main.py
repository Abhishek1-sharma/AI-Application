from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, SessionLocal, engine, get_db
from app.models import HCP, Interaction
from app.schemas import ChatRequest, ChatResponse, InteractionCreate, InteractionOut, ToolDemoRequest
from app.seed import seed_demo_data
from app.services.agent import AGENT_TOOLS, run_agent
from app.services.tools import interaction_to_dict, log_interaction_tool


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "llm_model": settings.groq_model, "agent": "LangGraph"}


@app.get("/api/hcps")
def list_hcps(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": hcp.id,
            "name": hcp.name,
            "specialty": hcp.specialty,
            "territory": hcp.territory,
            "segment": hcp.segment,
            "preferred_channel": hcp.preferred_channel,
            "last_contacted_at": hcp.last_contacted_at,
        }
        for hcp in db.query(HCP).order_by(HCP.name).all()
    ]


@app.get("/api/interactions")
def list_interactions(db: Session = Depends(get_db)) -> list[dict]:
    interactions = db.query(Interaction).order_by(Interaction.occurred_at.desc()).all()
    return [interaction_to_dict(item) for item in interactions]


@app.post("/api/interactions")
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)) -> dict:
    try:
        return log_interaction_tool(db, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/agent/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    payload = _payload_from_message(request)
    try:
        output = run_agent(db, request.message, payload, request.hcp_id, request.interaction_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChatResponse(
        selected_tool=output["selected_tool"],
        answer=f"LangGraph selected {output['selected_tool']} and completed the action.",
        data=output["result"],
    )


@app.get("/api/agent/tools")
def list_agent_tools() -> list[dict]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
        }
        for tool in AGENT_TOOLS
    ]


@app.post("/api/agent/demo")
def demo_tool(request: ToolDemoRequest, db: Session = Depends(get_db)) -> dict:
    try:
        output = run_agent(db, request.tool_name.replace("_", " "), request.payload, request.payload.get("hcp_id"), request.payload.get("interaction_id"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return output


def _payload_from_message(request: ChatRequest) -> dict:
    if request.hcp_id:
        return {
            "hcp_id": request.hcp_id,
            "interaction_type": "Conversational Log",
            "channel": "Chat",
            "product_discussed": "CardioGuard",
            "objective": "Capture field interaction from chat",
            "notes": request.message,
            "commitment": "Parsed from conversation",
            "next_step": "AI recommended follow-up",
            "follow_up_date": "",
        }
    return {"text": request.message}
