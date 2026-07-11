from datetime import datetime
from pydantic import BaseModel, Field


class HCPOut(BaseModel):
    id: int
    name: str
    specialty: str
    territory: str
    segment: str
    preferred_channel: str
    last_contacted_at: datetime | None

    model_config = {"from_attributes": True}


class InteractionCreate(BaseModel):
    hcp_id: int
    interaction_type: str = Field(..., examples=["Detailing Call"])
    channel: str = Field(..., examples=["In-person"])
    occurred_at: datetime | None = None
    product_discussed: str
    objective: str
    notes: str
    commitment: str = ""
    next_step: str = ""
    follow_up_date: str = ""


class InteractionUpdate(BaseModel):
    interaction_type: str | None = None
    channel: str | None = None
    product_discussed: str | None = None
    objective: str | None = None
    notes: str | None = None
    commitment: str | None = None
    next_step: str | None = None
    follow_up_date: str | None = None


class InteractionOut(BaseModel):
    id: int
    hcp_id: int
    hcp_name: str | None = None
    interaction_type: str
    channel: str
    occurred_at: datetime
    product_discussed: str
    objective: str
    notes: str
    summary: str
    sentiment: str
    commitment: str
    next_step: str
    follow_up_date: str
    compliance_flags: list[str]
    entities: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str
    hcp_id: int | None = None
    interaction_id: int | None = None


class ChatResponse(BaseModel):
    selected_tool: str
    answer: str
    data: dict


class ExtractInteractionRequest(BaseModel):
    message: str
    hcp_id: int | None = None


class ToolDemoRequest(BaseModel):
    tool_name: str
    payload: dict = {}
