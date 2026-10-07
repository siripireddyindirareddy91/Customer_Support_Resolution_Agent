from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=100)
    order_id: str | None = Field(default=None, max_length=50)


class ChatResponse(BaseModel):
    request_id: str | None = None
    trace_id: str | None = None
    session_id: str | None = None
    conversation_id: str | None = None
    agent_run_id: str | None = None
    response: str
    intent: str
    workflow_status: str
    order: dict | None = None
    delivery: dict | None = None
    resolution: dict | None = None
    citations: list[dict] = Field(default_factory=list)
    escalation: dict | None = None
    activity: list[str] = Field(default_factory=list)