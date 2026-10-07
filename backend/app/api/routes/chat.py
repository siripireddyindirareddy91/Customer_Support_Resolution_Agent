import time

from fastapi import APIRouter, Depends

from ai.langgraph.workflow import workflow
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.security.auth import authenticated_customer
from backend.app.observability.telemetry import new_id, record_agent_run, record_log, request_context

router = APIRouter(prefix="/api/v1", tags=["support"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, customer_id: str = Depends(authenticated_customer)) -> ChatResponse:
    started = time.perf_counter()
    context = request_context.get()
    result = workflow.invoke({
        "request_id": context.get("request_id", new_id()),
        "trace_id": context.get("trace_id", new_id()),
        "customer_id": customer_id,
        "session_id": request.session_id or context.get("session_id", new_id()),
        "conversation_id": context.get("conversation_id", new_id()),
        "agent_run_id": context.get("agent_run_id", new_id()),
        "current_span_id": new_id(),
        "customer_message": request.message,
        "order_id": request.order_id,
        "retry_count": 0,
        "errors": [],
        "activity": [],
    })
    duration_ms = (time.perf_counter() - started) * 1000
    intent = result.get("intent", "UNKNOWN")
    workflow_status = "ESCALATED" if result.get("escalation") else result.get("validation_result", {}).get("status", "NEEDS_INFORMATION")
    record_agent_run(intent, workflow_status, duration_ms, len(result.get("activity", [])))
    record_log("customer_query_processed", metadata={"intent": intent, "workflow_status": workflow_status})
    return ChatResponse(
        request_id=context.get("request_id"),
        trace_id=context.get("trace_id"),
        session_id=context.get("session_id"),
        conversation_id=context.get("conversation_id"),
        agent_run_id=context.get("agent_run_id"),
        response=result.get("final_response", "I’m unable to complete that request right now."),
        intent=intent,
        workflow_status=workflow_status,
        order=result.get("order_data"),
        delivery=result.get("delivery_data"),
        resolution=result.get("proposed_resolution"),
        citations=result.get("policy_evidence", []),
        escalation=result.get("escalation"),
        activity=result.get("activity", []),
    )