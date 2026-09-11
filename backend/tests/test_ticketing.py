from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.schemas import TicketCreateRequest
from app.services.pipeline import analyze_complaint
from app.services.ticketing import create_ticket, find_duplicates, simulate_breach


def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def test_ticket_lifecycle_and_escalation():
    db = session()
    payload = TicketCreateRequest(
        complaint="There has been no water supply in Shivaji Nagar for three days.",
        language="English",
        location="Shivaji Nagar",
    )
    analysis = analyze_complaint(payload.complaint, supplied_location=payload.location)
    ticket = create_ticket(db, payload, analysis)

    assert ticket.ticket_code.startswith("CR-")
    assert ticket.status == "SUBMITTED"
    assert ticket.sla_state == "SAFE"
    assert len(ticket.audit_events) >= 5

    escalated = simulate_breach(db, ticket)
    assert escalated.status == "ESCALATED"
    assert escalated.sla_state == "BREACHED"
    assert any(event.event == "SUPERVISOR_NOTIFIED" for event in escalated.audit_events)
    assert any(event.event == "CITIZEN_NOTIFIED" for event in escalated.audit_events)


def test_duplicate_detection_across_same_category():
    db = session()
    first = TicketCreateRequest(
        complaint="Garbage has not been collected on FC Road for five days and it smells.",
        language="English",
        location="FC Road",
    )
    analysis = analyze_complaint(first.complaint, supplied_location=first.location)
    created = create_ticket(db, first, analysis)

    second_text = "Garbage is still not collected on our street at FC Road and it smells badly."
    second_analysis = analyze_complaint(second_text, supplied_location="FC Road")
    matches = find_duplicates(db, second_analysis, second_text)

    assert matches
    assert matches[0].ticket_code == created.ticket_code
