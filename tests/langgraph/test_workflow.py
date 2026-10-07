from ai.langgraph.workflow import workflow


def run(message: str, customer_id: str = "CUS-1001", order_id: str | None = None) -> dict:
    return workflow.invoke({
        "customer_id": customer_id,
        "session_id": "test",
        "customer_message": message,
        "order_id": order_id,
        "retry_count": 0,
        "errors": [],
        "activity": [],
    })


def test_tracking_uses_verified_order_and_delivery() -> None:
    result = run("Where is order ORD-1001?")
    assert result["intent"] == "ORDER_STATUS"
    assert result["order_data"]["id"] == "ORD-1001"
    assert result["delivery_data"]["tracking_number"] == "PP-884120"
    assert result["validation_result"]["status"] == "VALID"
    assert "2026-10-08" in result["final_response"]


def test_customer_cannot_read_another_customers_order() -> None:
    result = run("Where is order ORD-2001?", customer_id="CUS-1001")
    assert result["order_data"] is None
    assert "couldn’t match" in result["final_response"]


def test_delivered_not_received_uses_policy_and_order_evidence() -> None:
    result = run("My order #ORD-1002 says delivered but I didn't receive it")
    assert result["intent"] == "DELIVERED_NOT_RECEIVED"
    assert result["proposed_resolution"]["action"] == "missing_delivery_investigation"
    assert result["validation_result"]["status"] == "VALID"
    assert [item["source"] for item in result["policy_evidence"]] == ["delivery-and-missing-package.md"]
    assert "building reception" in result["final_response"]


def test_human_request_escalates_without_claiming_resolution() -> None:
    result = run("I want to speak to a human")
    assert result["escalation"]["status"] == "open"
    assert result["proposed_resolution"]["action"] == "human_review"