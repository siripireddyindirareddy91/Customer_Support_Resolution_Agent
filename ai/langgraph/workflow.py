import re
from typing import Literal

from langgraph.graph import END, START, StateGraph

from ai.langgraph.state.delivery_state import DeliveryState
from ai.rag.pipeline import retrieve_policy
from ai.tools.support_tools import get_delivery_status, get_order
from backend.app.config.settings import settings

INTENTS = {
    "HUMAN_ESCALATION": ("human", "agent please", "speak to someone", "representative"),
    "DELIVERED_NOT_RECEIVED": ("didn't receive", "did not receive", "not received", "missing delivery"),
    "DAMAGED_ITEM": ("damaged", "broken", "arrived damaged"),
    "WRONG_ITEM": ("wrong item", "incorrect item", "sent the wrong"),
    "MISSING_ITEM": ("missing item", "item is missing"),
    "LATE_DELIVERY": ("late", "delayed", "overdue", "not arrived"),
    "FAILED_DELIVERY": ("failed delivery", "delivery failed", "attempted delivery"),
    "CANCELLATION": ("cancel", "cancellation"),
    "REPLACEMENT": ("replacement", "replace this"),
    "REFUND": ("refund", "money back"),
    "ADDRESS_CHANGE": ("change address", "address change"),
    "DELIVERY_PARTNER": ("delivery driver", "courier", "carrier"),
    "ORDER_STATUS": ("track", "where is", "status", "order #", "order id"),
}


def _push(state: DeliveryState, text: str) -> list[str]:
    return [*state.get("activity", []), text]


def input_guardrail(state: DeliveryState) -> dict:
    message = state["customer_message"]
    if not message.strip() or len(message) > settings.max_message_length:
        return {"errors": ["Message is empty or exceeds the configured limit."], "activity": _push(state, "Request rejected")}
    return {"activity": _push(state, "Request validated")}


def classify_intent(state: DeliveryState) -> dict:
    message = state["customer_message"].lower()
    found_order = re.search(r"\b(ord[- ]?\d{4,})\b", message, re.I)
    order_id = found_order.group(1).upper().replace(" ", "-") if found_order else state.get("order_id")
    for intent, phrases in INTENTS.items():
        if any(phrase in message for phrase in phrases):
            return {"intent": intent, "intent_confidence": 0.92, "order_id": order_id, "activity": _push(state, "Request understood")}
    if settings.openai_api_key:
        try:
            from ai.llm.model_factory import classify_with_llm

            intent = classify_with_llm(state["customer_message"])
            return {"intent": intent, "intent_confidence": 0.7, "order_id": order_id, "activity": _push(state, "Request categorized")}
        except Exception:
            pass
    return {"intent": "GENERAL_POLICY", "intent_confidence": 0.4, "order_id": order_id, "activity": _push(state, "Request categorized")}


def supervise(state: DeliveryState) -> dict:
    if state["intent"] == "HUMAN_ESCALATION":
        escalation = {"reason": "Customer requested a human agent", "priority": "normal", "status": "open"}
        resolution = {"status": "escalated", "action": "human_review", "basis": []}
        return {"escalation": escalation, "proposed_resolution": resolution, "activity": _push(state, "Human support requested")}
    return {"activity": _push(state, "Support workflow coordinated")}


def plan(state: DeliveryState) -> dict:
    steps = ["identify request", "verify customer order", "retrieve applicable policy", "validate resolution"]
    if state.get("order_id"):
        steps.insert(2, "check delivery information")
    return {"plan": steps, "activity": _push(state, "Resolution plan prepared")}


def route(state: DeliveryState) -> dict:
    intent = state["intent"]
    agent = "delivery" if intent in {"ORDER_STATUS", "LATE_DELIVERY", "DELIVERED_NOT_RECEIVED", "FAILED_DELIVERY", "DELIVERY_PARTNER"} else "policy_support"
    return {"selected_agent": agent, "activity": _push(state, f"Routed to {agent} specialist")}


def execute_tools(state: DeliveryState) -> dict:
    order_id = state.get("order_id")
    if not order_id:
        return {"order_data": None, "delivery_data": None, "activity": _push(state, "Order ID needed")}
    order = get_order.invoke({"order_id": order_id, "customer_id": state["customer_id"]})
    delivery = get_delivery_status.invoke({"order_id": order_id, "customer_id": state["customer_id"]}) if order else None
    return {"order_data": order, "delivery_data": delivery, "activity": _push(state, "Order and delivery records checked")}


def retrieve_evidence(state: DeliveryState) -> dict:
    evidence = retrieve_policy(f"{state['intent']} {state['customer_message']}")
    return {"policy_evidence": evidence, "activity": _push(state, "Support policy reviewed")}


def resolve(state: DeliveryState) -> dict:
    intent = state["intent"]
    order, delivery = state.get("order_data"), state.get("delivery_data")
    evidence = state.get("policy_evidence", [])
    resolution = {"status": "needs_information", "action": "ask_for_order", "basis": []}
    if state.get("escalation"):
        resolution = {"status": "escalated", "action": "human_review", "basis": []}
    elif state.get("order_id") and order is None:
        resolution = {"status": "needs_information", "action": "verify_order", "basis": []}
    elif order and delivery and intent == "DELIVERED_NOT_RECEIVED":
        resolution = {"status": "investigation_guidance", "action": "missing_delivery_investigation", "basis": ["order_data", "delivery_data", "policy_evidence"]}
    elif order and delivery and intent in {"ORDER_STATUS", "LATE_DELIVERY", "DELIVERY_PARTNER"}:
        resolution = {"status": "informational", "action": "share_tracking", "basis": ["order_data", "delivery_data"]}
    elif evidence:
        resolution = {"status": "policy_guidance", "action": "explain_policy", "basis": ["policy_evidence"]}
    return {"proposed_resolution": resolution, "activity": _push(state, "Evidence-based resolution drafted")}


def critic(state: DeliveryState) -> dict:
    resolution = state.get("proposed_resolution") or {}
    supported = resolution.get("status") in {"needs_information", "escalated"} or bool(resolution.get("basis"))
    return {"critic_result": {"supported": supported}, "activity": _push(state, "Resolution reviewed")}


def validate(state: DeliveryState) -> dict:
    resolution = state.get("proposed_resolution") or {}
    valid = bool(state.get("critic_result", {}).get("supported"))
    if resolution.get("action") == "share_tracking":
        valid = valid and bool(state.get("order_data")) and bool(state.get("delivery_data"))
    if resolution.get("action") == "explain_policy":
        valid = valid and bool(state.get("policy_evidence"))
    if resolution.get("action") == "missing_delivery_investigation":
        valid = valid and bool(state.get("order_data")) and bool(state.get("delivery_data")) and bool(state.get("policy_evidence"))
    return {"validation_result": {"status": "VALID" if valid else "INVALID", "errors": [] if valid else ["Resolution lacks verified evidence."]}, "activity": _push(state, "Resolution validated" if valid else "Resolution needs another pass")}


def replan(state: DeliveryState) -> dict:
    return {"retry_count": state.get("retry_count", 0) + 1, "proposed_resolution": {"status": "needs_information", "action": "human_review", "basis": []}, "activity": _push(state, "Escalated after validation issue")}


def respond(state: DeliveryState) -> dict:
    resolution = state.get("proposed_resolution") or {}
    order, delivery = state.get("order_data"), state.get("delivery_data")
    if state.get("escalation") or resolution.get("action") == "human_review":
        text = "I’ve flagged this for a support specialist. They’ll review the details and follow up with you."
    elif resolution.get("action") == "verify_order":
        text = "I couldn’t match that order to your account. Please check the order number or contact support so we can verify it securely."
    elif resolution.get("action") == "share_tracking" and order and delivery:
        if delivery["status"] == "delivered":
            text = f"Order {order['id']} is marked delivered. The recorded delivery time is {delivery.get('delivered_at', 'not provided')}. If you can’t locate it, check nearby safe places and let me know so I can guide you through the next steps."
        else:
            eta = delivery.get("estimated_delivery", "not currently available")
            text = f"Order {order['id']} is {delivery['status'].replace('_', ' ')} with {delivery['carrier']}. The current estimated delivery is {eta}."
    elif resolution.get("action") == "missing_delivery_investigation" and order and delivery and state.get("policy_evidence"):
        source = state["policy_evidence"][0]["source"]
        text = f"Order {order['id']} is marked delivered by {delivery['carrier']}. Please check the delivery location, household members, building reception, and nearby safe places. If it is still missing, support should investigate it under our {source} guidance."
    elif resolution.get("action") == "explain_policy" and state.get("policy_evidence"):
        source = state["policy_evidence"][0]
        text = f"Here is the relevant guidance from {source['source']}: {source['excerpt'].splitlines()[-1].strip()} Please share your order number if you’d like me to check how it applies to your order."
    else:
        text = "I can help with that. Please share the order number and a little more detail so I can check the applicable options."
    return {"final_response": text, "activity": _push(state, "Reply ready")}


def _after_guardrail(state: DeliveryState) -> Literal["classify_intent", "response"]:
    return "response" if state.get("errors") else "classify_intent"


def _after_supervisor(state: DeliveryState) -> Literal["response", "planner"]:
    return "response" if state.get("escalation") else "planner"


def _after_validation(state: DeliveryState) -> Literal["response", "replanner"]:
    return "response" if state.get("validation_result", {}).get("status") == "VALID" or state.get("retry_count", 0) else "replanner"


def build_workflow():
    graph = StateGraph(DeliveryState)
    nodes = {
        "input_guardrail": input_guardrail, "classify_intent": classify_intent,
        "supervisor": supervise, "planner": plan, "router": route, "tools": execute_tools,
        "policy": retrieve_evidence, "resolution": resolve, "critic": critic,
        "validator": validate, "replanner": replan, "response": respond,
    }
    for name, node in nodes.items():
        graph.add_node(name, node)
    graph.add_edge(START, "input_guardrail")
    graph.add_conditional_edges("input_guardrail", _after_guardrail)
    graph.add_edge("classify_intent", "supervisor")
    graph.add_conditional_edges("supervisor", _after_supervisor)
    graph.add_edge("planner", "router")
    graph.add_edge("router", "tools")
    graph.add_edge("tools", "policy")
    graph.add_edge("policy", "resolution")
    graph.add_edge("resolution", "critic")
    graph.add_edge("critic", "validator")
    graph.add_conditional_edges("validator", _after_validation)
    graph.add_edge("replanner", "response")
    graph.add_edge("response", END)
    return graph.compile()


workflow = build_workflow()