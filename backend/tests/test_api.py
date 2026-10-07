from fastapi.testclient import TestClient

from backend.app.config.settings import settings
from backend.app.main import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json()["status"] == "ok"


def test_chat_requires_customer_context() -> None:
    response = client.post("/api/v1/chat", json={"message": "Where is order ORD-1001?"})
    assert response.status_code == 401


def test_chat_returns_tracking_for_customer_order() -> None:
    token = client.post("/api/v1/auth/demo", json={"customer_id": "CUS-1001"}).json()["access_token"]
    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Where is order ORD-1001?"},
    )
    assert response.status_code == 200
    assert response.json()["delivery"]["status"] == "in_transit"
    result = response.json()
    assert result["request_id"]
    assert result["trace_id"]
    assert response.headers["x-trace-id"] == result["trace_id"]

    trace = client.get(f"/api/observability/traces/{result['trace_id']}")
    assert trace.status_code == 200
    assert {span["name"] for span in trace.json()["spans"]} == {"api_request", "langgraph_workflow"}
    assert trace.json()["trace"]["request_id"] == result["request_id"]

    overview = client.get("/api/observability/overview").json()
    assert overview["source"] == "sqlite"
    assert overview["requests"]["total"] >= 1
    metrics = client.get("/api/metrics/requests?limit=10&offset=0").json()
    assert any(item["request_id"] == result["request_id"] for item in metrics["items"])


def test_observability_is_hidden_outside_development(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    response = client.get("/api/traces")
    assert response.status_code == 404