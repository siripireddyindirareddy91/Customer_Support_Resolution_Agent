from typing import Any, NotRequired, TypedDict


class DeliveryState(TypedDict):
    request_id: NotRequired[str]
    trace_id: NotRequired[str]
    customer_id: str
    session_id: str
    conversation_id: NotRequired[str]
    agent_run_id: NotRequired[str]
    current_span_id: NotRequired[str]
    customer_message: str
    order_id: NotRequired[str | None]
    intent: NotRequired[str]
    intent_confidence: NotRequired[float]
    selected_agent: NotRequired[str]
    plan: NotRequired[list[str]]
    order_data: NotRequired[dict[str, Any] | None]
    delivery_data: NotRequired[dict[str, Any] | None]
    policy_evidence: NotRequired[list[dict[str, str]]]
    proposed_resolution: NotRequired[dict[str, Any] | None]
    critic_result: NotRequired[dict[str, Any]]
    validation_result: NotRequired[dict[str, Any]]
    retry_count: NotRequired[int]
    errors: NotRequired[list[str]]
    activity: NotRequired[list[str]]
    final_response: NotRequired[str]
    escalation: NotRequired[dict[str, str] | None]