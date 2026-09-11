from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


def build_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def test_health_readiness_and_request_id_headers():
    with build_client() as client:
        health = client.get("/health", headers={"X-Request-ID": "integration-req-1"})
        assert health.status_code == 200
        assert health.headers["x-request-id"] == "integration-req-1"
        assert health.headers["x-content-type-options"] == "nosniff"

        ready = client.get("/ready")
        assert ready.status_code == 200
        assert ready.json()["database"] == "reachable"


def test_api_water_clarification_then_idempotent_ticket_creation():
    payload = {
        "complaint": "There has been no water supply in our area for three days and nobody is responding.",
        "language": "English",
    }
    with build_client() as client:
        analysis = client.post("/api/v1/complaints/analyze", json=payload)
        assert analysis.status_code == 200
        body = analysis.json()
        assert body["category"] == "Water Supply"
        assert body["priority"] == "HIGH"
        assert "location" in body["missing_information"]

        incomplete = client.post("/api/v1/tickets", json=payload)
        assert incomplete.status_code == 422

        complete = {**payload, "location": "Shivaji Nagar"}
        headers = {"Idempotency-Key": "api-ticket-water-1"}
        first = client.post("/api/v1/tickets", json=complete, headers=headers)
        replay = client.post("/api/v1/tickets", json=complete, headers=headers)
        assert first.status_code == 201
        assert replay.status_code == 201
        assert replay.json()["ticket_code"] == first.json()["ticket_code"]

        changed = client.post("/api/v1/tickets", json={**complete, "location": "Kothrud"}, headers=headers)
        assert changed.status_code == 409


def test_api_rejects_invalid_resolved_transition_and_breach():
    payload = {
        "complaint": "The streetlight outside our building has been broken for two weeks.",
        "language": "English",
        "location": "Aundh",
    }
    with build_client() as client:
        created = client.post("/api/v1/tickets", json=payload).json()
        code = created["ticket_code"]
        resolved = client.patch(
            f"/api/v1/tickets/{code}/status",
            json={"status": "RESOLVED", "note": "Lamp replaced and verified."},
        )
        assert resolved.status_code == 200

        reopen = client.patch(f"/api/v1/tickets/{code}/status", json={"status": "IN_PROGRESS"})
        assert reopen.status_code == 409

        breach = client.post(f"/api/v1/tickets/{code}/simulate-breach")
        assert breach.status_code == 409
