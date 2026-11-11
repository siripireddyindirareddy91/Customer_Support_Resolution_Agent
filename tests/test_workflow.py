from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import update

from backend.main import app, engine, fetch, users


def register(client):
    email = f"{uuid4().hex}@example.com"
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "local-test-password"})
    assert response.status_code == 201, response.text
    return email, {"Authorization": "Bearer " + response.json()["token"]}


def test_investigation_requires_review_and_preserves_audit():
    with TestClient(app) as client:
        owner, agent = register(client)
        manager_email, manager = register(client)
        with engine.begin() as connection:
            connection.execute(update(users).where(users.c.id == manager_email).values(
                payload={**fetch(users, manager_email), "role": "SUPPORT_MANAGER"}))
        created = client.post("/api/v1/investigations", headers=agent,
                              json={"complaint": "My order ORD-10452 has not arrived."})
        assert created.status_code == 201, created.text
        identifier = created.json()["id"]
        path = f"/api/v1/investigations/{identifier}"
        assert client.get(path, headers=manager).status_code == 404
        response = client.post(path + "/run", headers=agent)
        assert response.status_code == 200, response.text
        case = response.json()
        assert case["owner"] == owner
        assert case["status"] == "Pending review"
        assert case["classification"]["issue_type"] == "MAJOR_DELAY"
        assert len(case["trace"]) == 4
        assert case["policies"][0]["id"] == "P-01"
        saved = client.patch(f"/api/v1/resolutions/{identifier}", headers=agent,
                             json={"draft": "We are checking your shipment with the carrier."})
        assert saved.status_code == 200, saved.text
        assert saved.json()["resolution"]["draft"].startswith("We are checking")
        decision_path = f"/api/v1/approvals/{identifier}/approve"
        assert client.post(decision_path, headers=agent, json={"notes": "Review complete"}).status_code == 403
        approved = client.post(decision_path, headers=manager, json={"notes": "Evidence reviewed"})
        assert approved.status_code == 200, approved.text
        assert approved.json()["status"] == "Approved"
        assert approved.json()["decision"]["actor"] == manager_email
        assert client.post(decision_path, headers=manager, json={"notes": "Duplicate request"}).status_code == 409
        events = client.get(path + "/events", headers=agent).json()
        assert len(events) == 8


def test_evaluations_and_policy_upload():
    with TestClient(app) as client:
        _, agent = register(client)
        upload = client.post("/api/v1/policies/upload", headers=agent,
                             files={"file": ("test.txt", b"Ask dispatch to check specialized handovers.", "text/plain")})
        assert upload.status_code == 201, upload.text
        matches = client.post("/api/v1/policies/search", headers=agent, json={"query": "handovers"}).json()
        assert matches[0]["id"] == upload.json()["id"]
        evaluation = client.post("/api/v1/evaluations/run", headers=agent)
        assert evaluation.status_code == 200, evaluation.text
        report = evaluation.json()
        assert report["total"] == report["passed"] == 15
        assert report["categories"]["adversarial"] == {"passed": 5, "total": 5}
        assert report["confusion"]["MAJOR_DELAY"]["MAJOR_DELAY"] == 2


def test_review_evidence_can_resume_and_rerun():
    with TestClient(app) as client:
        email, reviewer = register(client)
        with engine.begin() as connection:
            connection.execute(update(users).where(users.c.id == email).values(
                payload={**fetch(users, email), "role": "SUPPORT_MANAGER"}))
        created = client.post("/api/v1/investigations", headers=reviewer,
                              json={"order_id": "ORD-10455", "complaint": "My parcel has not arrived."})
        assert created.status_code == 201
        identifier = created.json()["id"]
        path = f"/api/v1/investigations/{identifier}"
        assert client.post(path + "/run", headers=reviewer).json()["status"] == "Pending review"
        requested = client.post(f"/api/v1/approvals/{identifier}/request-evidence", headers=reviewer,
                                json={"notes": "Verify the last carrier scan."})
        assert requested.status_code == 200, requested.text
        assert requested.json()["status"] == "Evidence requested"
        updated = client.post(path + "/evidence", headers=reviewer, json={"context": "The customer also requested a refund."})
        assert updated.status_code == 200, updated.text
        rerun = client.post(path + "/run", headers=reviewer)
        assert rerun.status_code == 200, rerun.text
        assert rerun.json()["classification"]["flags"] == ["REFUND"]
