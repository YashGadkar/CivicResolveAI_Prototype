from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.services.auth import create_user


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
    app.state.test_engine = engine
    return TestClient(app)


def signup(client: TestClient, email: str = "citizen.test@gmail.com"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"name": "Citizen Test", "email": email, "password": "StrongPass#123"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == email
    return response


def seed_staff(client: TestClient, email: str = "officer@civicresolve.test") -> None:
    with Session(client.app.state.test_engine) as db:
        create_user(db, "Test Officer", email, "OfficerPass#123", role="OFFICER")


def test_health_readiness_and_request_id_headers():
    with build_client() as client:
        health = client.get("/health", headers={"X-Request-ID": "integration-req-1"})
        assert health.status_code == 200
        assert health.headers["x-request-id"] == "integration-req-1"
        ready = client.get("/ready")
        assert ready.status_code == 200


def test_auth_requires_gmail_and_strong_password():
    with build_client() as client:
        non_gmail = client.post(
            "/api/v1/auth/signup",
            json={"name": "Test User", "email": "user@example.com", "password": "StrongPass#123"},
        )
        assert non_gmail.status_code == 422
        weak = client.post(
            "/api/v1/auth/signup",
            json={"name": "Test User", "email": "user@gmail.com", "password": "password"},
        )
        assert weak.status_code == 422
        signup(client, "user@gmail.com")
        me = client.get("/api/v1/auth/me")
        assert me.status_code == 200
        assert me.json()["role"] == "CITIZEN"
        client.post("/api/v1/auth/logout")
        assert client.get("/api/v1/auth/me").status_code == 401


def test_employee_login_requires_staff_role_and_accepts_officer():
    with build_client() as client:
        signup(client, "citizen.employeecheck@gmail.com")
        client.post("/api/v1/auth/logout")
        rejected = client.post(
            "/api/v1/auth/employee-login",
            json={"email": "citizen.employeecheck@gmail.com", "password": "StrongPass#123"},
        )
        assert rejected.status_code == 403

        seed_staff(client)
        accepted = client.post(
            "/api/v1/auth/employee-login",
            json={"email": "officer@civicresolve.test", "password": "OfficerPass#123"},
        )
        assert accepted.status_code == 200
        assert accepted.json()["role"] == "OFFICER"


def test_protected_analysis_requires_login():
    with build_client() as client:
        response = client.post(
            "/api/v1/complaints/analyze",
            json={"complaint": "There is no water supply for three days."},
        )
        assert response.status_code == 401


def test_api_water_clarification_then_idempotent_ticket_creation():
    payload = {"complaint": "There has been no water supply in our area for three days and nobody is responding."}
    with build_client() as client:
        signup(client)
        analysis = client.post("/api/v1/complaints/analyze", json=payload)
        assert analysis.status_code == 200
        body = analysis.json()
        assert body["category"] == "Water Supply"
        assert body["language"] == "English"
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
        mine = client.get("/api/v1/tickets/mine")
        assert mine.status_code == 200
        assert mine.json()[0]["ticket_code"] == first.json()["ticket_code"]


def test_citizen_cannot_use_staff_status_or_breach_controls():
    payload = {
        "complaint": "The streetlight outside our building has been broken for two weeks.",
        "location": "Aundh",
    }
    with build_client() as client:
        signup(client, "second.user@gmail.com")
        created = client.post("/api/v1/tickets", json=payload).json()
        code = created["ticket_code"]
        assert client.patch(f"/api/v1/tickets/{code}/status", json={"status": "RESOLVED"}).status_code == 403
        assert client.post(f"/api/v1/tickets/{code}/simulate-breach").status_code == 403
        assert client.get("/api/v1/tickets").status_code == 403
        assert client.get("/api/v1/analytics").status_code == 403


def test_batch_api_separates_distinct_civic_problems():
    with build_client() as client:
        signup(client, "batch.user@gmail.com")
        response = client.post(
            "/api/v1/complaints/analyze-batch",
            json={
                "complaint": "There is no water supply for three days and garbage has not been collected for five days.",
                "location": "Rahuri",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["issue_count"] == 2
        assert [issue["category"] for issue in body["issues"]] == ["Water Supply", "Garbage Collection"]


def test_employee_can_open_full_ticket_and_citizen_details():
    complaint = "Garbage has not been collected for five days and it is starting to smell."
    with build_client() as client:
        signup(client, "detail.user@gmail.com")
        created = client.post(
            "/api/v1/tickets",
            json={"complaint": complaint, "location": "Aundh", "contact": "+91 9000000000"},
        )
        assert created.status_code == 201
        code = created.json()["ticket_code"]
        client.post("/api/v1/auth/logout")

        seed_staff(client)
        login = client.post(
            "/api/v1/auth/employee-login",
            json={"email": "officer@civicresolve.test", "password": "OfficerPass#123"},
        )
        assert login.status_code == 200

        detail = client.get(f"/api/v1/staff/tickets/{code}")
        assert detail.status_code == 200
        body = detail.json()
        assert body["complaint"] == complaint
        assert body["citizen"]["name"] == "Citizen Test"
        assert body["citizen"]["email"] == "detail.user@gmail.com"
        assert body["citizen"]["contact"] == "+91 9000000000"
