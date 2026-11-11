from datetime import UTC, datetime
from time import perf_counter
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy, interrupt
from .providers import generate_draft

from .sources import AGENTS, lookup_carrier_status, lookup_customer_history, lookup_order, lookup_tracking


class State(TypedDict, total=False):
    order_id: str
    customer_id: str
    complaint: str
    context: str
    priority: str
    trace: list[dict]
    order: dict | None
    tracking: list[dict]
    carrier: dict | None
    history: list[dict]
    lookup_status: str
    policy_status: str
    classification: dict
    policies: list[dict]
    resolution: dict
    decision: dict


def lookup(state, order_source=lookup_order, tracking_source=lookup_tracking,
           carrier_source=lookup_carrier_status, support_source=lookup_customer_history):
    order = order_source(state["order_id"])
    if order and state.get("customer_id") and state["customer_id"] != order["customer_id"]:
        order = None
    return {"order": order, "tracking": tracking_source(order) if order else [],
            "carrier": carrier_source(order) if order else None,
            "history": support_source(order) if order else [],
            "lookup_status": "VERIFIED" if order else "NOT_FOUND"}


def classify(state):
    order = state.get("order")
    complaint = state["complaint"].lower()
    untrusted_text = " ".join((complaint, state.get("context", "").lower()))
    evidence = [event["record_id"] for event in state["tracking"]]
    latest = state["tracking"][-1] if evidence else {}
    carrier = state.get("carrier") or {}
    if carrier:
        evidence.append(carrier["record_id"])
    if not order:
        issue, reason, score = "UNKNOWN", "Order could not be verified.", .30
    elif latest.get("status") == "Delivered" and (
            carrier.get("exception") or any(term in complaint for term in ("missing", "not receive", "never arrived"))):
        issue, reason, score = "STATUS_CONFLICT", "Delivered scan conflicts with the carrier update or customer report.", .93
    elif latest.get("status") == "Delivery attempted":
        issue, reason, score = "DELIVERY_FAILED", "Carrier recorded an attempted delivery.", .97
    elif latest.get("status") == "Damage reported":
        issue, reason, score = "DAMAGED", "Tracking contains a damage report.", .96
    elif carrier.get("exception") == "No recent scan":
        issue, reason, score = "LOST_SUSPECTED", "Carrier reports no recent scan. Loss remains unconfirmed.", .82
    elif latest.get("status") == "Delivered":
        issue, reason, score = "ON_TIME", "Tracking contains a delivered scan with no reported contradiction.", .94
    else:
        overdue = (datetime.now(UTC).date() - datetime.fromisoformat(order["expected"]).date()).days
        issue = "MAJOR_DELAY" if overdue > 2 else "MINOR_DELAY" if overdue > 0 else "ON_TIME"
        reason, score = f"Verified delivery commitment is {order['expected']}. Latest scan is {latest['status']}.", .94
    review = issue in {"UNKNOWN", "STATUS_CONFLICT", "MAJOR_DELAY", "LOST_SUSPECTED", "DAMAGED"}
    flags = [tag for tag, terms in {
        "REFUND": ("refund",), "FRAUD": ("ignore previous", "ignore all", "system prompt", "bypass", "fraud")
    }.items() if any(term in untrusted_text for term in terms)]
    return {"classification": dict(issue_type=issue, severity="HIGH" if review or flags else
                                   "MEDIUM" if issue != "ON_TIME" else "LOW", confidence=score,
                                   reasoning=reason, evidence=evidence, flags=flags,
                                   requires_human_review=bool(review or flags or score < .75))}


def handoff(state, model_drafts=True, gateway_token=None):
    classification = state["classification"]
    issue = classification["issue_type"]
    action = {
        "ON_TIME": "Share verified delivery information", "MINOR_DELAY": "Share an updated delivery estimate",
        "MAJOR_DELAY": "Open carrier investigation review", "LOST_SUSPECTED": "Request a carrier trace",
        "DAMAGED": "Request damage evidence", "DELIVERY_FAILED": "Confirm next delivery attempt",
        "STATUS_CONFLICT": "Reconcile delivery evidence", "UNKNOWN": "Request verified order information",
    }[issue]
    if "FRAUD" in classification["flags"]:
        action = "Refer the claim to a support reviewer"
    elif "REFUND" in classification["flags"]:
        action = "Refer refund eligibility to a support reviewer"
    if not state["policies"]:
        action = "Request policy review"
    fallback = ("Thanks for contacting support. " + classification["reasoning"] +
                " Our recommended next step is to " + action[0].lower() + action[1:] + ".")
    draft, draft_source = (generate_draft(action, classification["reasoning"], fallback, gateway_token)
                           if model_drafts else (fallback, "template"))
    return {"resolution": dict(action=action, reason=classification["reasoning"],
                               citations=state["policies"], confidence=classification["confidence"],
                               draft=draft, draft_source=draft_source,
                               priority="Urgent" if classification["severity"] == "HIGH" else state.get("priority", "Normal"),
                               requires_approval=classification["requires_human_review"] or not state["policies"])}


def build_graph(checkpointer, search, order_source=lookup_order, tracking_source=lookup_tracking, *,
                model_drafts=True, gateway_token=None, carrier_source=lookup_carrier_status,
                support_source=lookup_customer_history):
    def retrieve(state):
        classification = state["classification"]
        policies = search(" ".join([classification["issue_type"], *classification["flags"]]))
        return {"policies": policies, "policy_status": "MATCHED" if policies else "POLICY_NOT_FOUND"}

    def traced(index, operation):
        def run(state):
            started = perf_counter()
            result = operation(state)
            if index == 0:
                order = result["order"]
                tools = ["lookup_order"]
                references = []
                if order:
                    tools += ["lookup_tracking", "lookup_carrier_status", "lookup_customer_history"]
                    references = [order["record_id"], result["carrier"]["record_id"],
                                  *(row["record_id"] for row in result["tracking"] + result["history"])]
            elif index == 1:
                tools, references = [], result["classification"]["evidence"]
            elif index == 2:
                tools, references = ["retrieve_policy_passages"], [row["id"] for row in result["policies"]]
            else:
                tools, references = [], [row["id"] for row in result["resolution"]["citations"]]
            return {**result, "trace": [*state.get("trace", []),
                    dict(agent=AGENTS[index], duration_ms=round((perf_counter() - started) * 1000, 2),
                         at=datetime.now(UTC).isoformat(), output=result, status="Completed",
                         tool_calls=tools, references=references)]}
        return run

    graph = StateGraph(State)
    names = ("lookup", "classify", "retrieve", "handoff")
    operations = (lambda state: lookup(state, order_source, tracking_source, carrier_source, support_source),
                  classify, retrieve, lambda state: handoff(state, model_drafts, gateway_token))
    for index, (name, operation) in enumerate(zip(names, operations)):
        graph.add_node(name, traced(index, operation), retry_policy=RetryPolicy(max_attempts=2))
    graph.add_edge(START, "lookup")
    for left, right in zip(names, names[1:]):
        graph.add_edge(left, right)
    graph.add_node("approval", lambda state: {"decision": interrupt(state["resolution"])})
    graph.add_conditional_edges("handoff", lambda state: "approval" if state["resolution"]["requires_approval"] else END,
                                {"approval": "approval", END: END})
    graph.add_edge("approval", END)
    return graph.compile(checkpointer=checkpointer)
