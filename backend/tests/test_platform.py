from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.services.auth import create_user
import app.platform_routes as platform_routes
import app.services.platform as platform_service

PASSWORD = "StrongPass#123"


def build_client(monkeypatch) -> TestClient:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def override_db():
        with Session(engine) as db:
            yield db

    # Platform metadata must remain deterministic in tests and must not depend on
    # an external geocoder being reachable from CI.
    monkeypatch.setattr(
        platform_service,
        "_location_parts",
        lambda ticket: ("Ward 7", "North Zone", "Pune", 18.6298, 73.7997),
    )
    app.dependency_overrides[get_db] = override_db
    app.state.test_engine = engine
    return TestClient(app)


def signup(client: TestClient, email="platform.citizen@gmail.com"):
    response = client.post("/api/v1/auth/signup", json={"name": "Platform Citizen", "email": email, "password": PASSWORD})
    assert response.status_code == 201
    return response.json()


def seed_officer(client: TestClient):
    with Session(client.app.state.test_engine) as db:
        create_user(db, "Ward Officer", "officer@civicresolve.test", "OfficerPass#123", role="OFFICER")


def seed_admin(client: TestClient):
    with Session(client.app.state.test_engine) as db:
        create_user(db, "Civic Admin", "admin@civicresolve.test", "AdminPass#123", role="ADMIN")


def create_ticket(client: TestClient, complaint="Garbage has not been collected for five days and the smell is severe."):
    response = client.post(
        "/api/v1/tickets",
        json={"complaint": complaint, "location": "Nigdi, Pune", "verify_location": False},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_citizen_can_archive_ticket_without_destroying_accountability(monkeypatch):
    with build_client(monkeypatch) as client:
        signup(client)
        ticket = create_ticket(client)
        before = client.get("/api/v1/platform/tickets/mine")
        assert before.status_code == 200
        assert len(before.json()) == 1
        assert before.json()[0]["meta"]["ward"] == "Ward 7"

        archived = client.delete(f"/api/v1/platform/tickets/{ticket['ticket_code']}")
        assert archived.status_code == 200
        assert archived.json()["meta"]["archived"] is True
        assert client.get("/api/v1/platform/tickets/mine").json() == []

        # The underlying audited ticket still exists and remains owned by the citizen.
        core = client.get(f"/api/v1/tickets/{ticket['ticket_code']}")
        assert core.status_code == 200
        assert any(e["event"] == "TICKET_ARCHIVED" for e in core.json()["audit_events"])


def test_employee_assignment_transfer_resolution_and_citizen_reopen(monkeypatch):
    with build_client(monkeypatch) as client:
        citizen = signup(client, "resolution.owner@gmail.com")
        ticket = create_ticket(client, "There is a large pothole on the road and bikes are nearly falling.")
        code = ticket["ticket_code"]
        client.post("/api/v1/auth/logout")

        seed_officer(client)
        login = client.post(
            "/api/v1/auth/employee-login",
            json={"email": "officer@civicresolve.test", "password": "OfficerPass#123"},
        )
        assert login.status_code == 200

        departments = client.get("/api/v1/platform/staff/departments")
        assert departments.status_code == 200
        assert "Drainage & Sewerage Department" in departments.json()

        assigned = client.post(f"/api/v1/platform/staff/tickets/{code}/assign", json={"officer": "Road Crew A"})
        assert assigned.status_code == 200
        assert assigned.json()["ticket"]["assigned_officer"] == "Road Crew A"
        assert assigned.json()["ticket"]["status"] == "ASSIGNED"

        invalid = client.post(
            f"/api/v1/platform/staff/tickets/{code}/transfer",
            json={"department": "Made Up Department", "reason": "Should not be accepted"},
        )
        assert invalid.status_code == 422

        transferred = client.post(
            f"/api/v1/platform/staff/tickets/{code}/transfer",
            json={"department": "Drainage & Sewerage Department", "reason": "Waterlogging is caused by a blocked storm drain"},
        )
        assert transferred.status_code == 200
        assert transferred.json()["ticket"]["department"] == "Drainage & Sewerage Department"
        assert transferred.json()["ticket"]["assigned_officer"] is None
        assert transferred.json()["ticket"]["status"] == "SUBMITTED"
        transfer_events = [e for e in transferred.json()["ticket"]["audit_events"] if e["event"] == "DEPARTMENT_TRANSFERRED"]
        assert transfer_events
        assert "Ward Officer (OFFICER)" in transfer_events[-1]["detail"]
        assert "Road Crew A" in transfer_events[-1]["detail"]

        resolved = client.post(
            f"/api/v1/platform/staff/tickets/{code}/resolve",
            json={"note": "Pothole filled and road surface compacted; field team verified completion."},
        )
        assert resolved.status_code == 200
        assert resolved.json()["ticket"]["status"] == "RESOLVED"
        assert resolved.json()["meta"]["resolution_note"].startswith("Pothole filled")
        assert resolved.json()["citizen"]["email"] == citizen["email"]

        client.post("/api/v1/auth/logout")
        assert client.post("/api/v1/auth/login", json={"email": citizen["email"], "password": PASSWORD}).status_code == 200
        reopened = client.post(
            f"/api/v1/platform/tickets/{code}/confirm",
            json={"resolved": False, "feedback": "The pothole is still partly open."},
        )
        assert reopened.status_code == 200
        assert reopened.json()["ticket"]["status"] == "IN_PROGRESS"
        assert reopened.json()["meta"]["citizen_confirmation"] == "REOPENED"


def test_staff_translation_available_to_officer_and_admin(monkeypatch):
    with build_client(monkeypatch) as client:
        signup(client, "translation.owner@gmail.com")
        ticket = create_ticket(client, "Garbage has not been collected near the market.")
        code = ticket["ticket_code"]
        client.post("/api/v1/auth/logout")

        monkeypatch.setattr(
            platform_routes,
            "translate_text",
            lambda text, target, source: {
                "original_text": text,
                "translated_text": "बाजाराजवळ कचरा गोळा केलेला नाही.",
                "source_language": "en",
                "target_language": target,
                "target_language_name": "Marathi",
                "provider": "test provider",
            },
        )

        seed_officer(client)
        seed_admin(client)

        officer_login = client.post(
            "/api/v1/auth/employee-login",
            json={"email": "officer@civicresolve.test", "password": "OfficerPass#123"},
        )
        assert officer_login.status_code == 200
        languages = client.get("/api/v1/platform/staff/translation-languages")
        assert languages.status_code == 200
        assert any(item["code"] == "mr" for item in languages.json())
        translated = client.post(f"/api/v1/platform/staff/tickets/{code}/translate", json={"target_language": "mr"})
        assert translated.status_code == 200
        assert translated.json()["target_language_name"] == "Marathi"
        assert "कचरा" in translated.json()["translated_text"]

        client.post("/api/v1/auth/logout")
        admin_login = client.post(
            "/api/v1/auth/employee-login",
            json={"email": "admin@civicresolve.test", "password": "AdminPass#123"},
        )
        assert admin_login.status_code == 200
        admin_translation = client.post(f"/api/v1/platform/staff/tickets/{code}/translate", json={"target_language": "mr"})
        assert admin_translation.status_code == 200


def test_incident_grouping_and_role_aware_assistant(monkeypatch):
    with build_client(monkeypatch) as client:
        signup(client, "incident.owner@gmail.com")
        first = create_ticket(client, "Garbage has not been collected for five days near the market.")
        second = create_ticket(client, "Garbage and waste are still piled up near the market.")

        mine = client.get("/api/v1/platform/tickets/mine").json()
        assert len(mine) == 2
        assert all(item["meta"]["related_reports"] == 2 for item in mine)

        assistant = client.post("/api/v1/platform/assistant", json={"message": f"What is happening with {first['ticket_code']}?"})
        assert assistant.status_code == 200
        assert first["ticket_code"] in assistant.json()["reply"]
        assert assistant.json()["actions"][0]["type"] == "OPEN_TICKET"

        client.post("/api/v1/auth/logout")
        seed_officer(client)
        client.post(
            "/api/v1/auth/employee-login",
            json={"email": "officer@civicresolve.test", "password": "OfficerPass#123"},
        )
        incidents = client.get("/api/v1/platform/incidents")
        assert incidents.status_code == 200
        assert any(item["report_count"] == 2 for item in incidents.json())

        queue = client.post("/api/v1/platform/assistant", json={"message": "Show unresolved queue and incident clusters"})
        assert queue.status_code == 200
        assert queue.json()["actions"][0]["type"] == "OPEN_QUEUE"
