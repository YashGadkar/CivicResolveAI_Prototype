from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.schemas import TicketCreateRequest
from app.services.pipeline import analyze_complaint
from app.services.ticketing import (
    IdempotencyConflict,
    InvalidStatusTransition,
    create_ticket,
    find_duplicates,
    simulate_breach,
    update_status,
)


def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def water_payload(location: str = "Shivaji Nagar") -> TicketCreateRequest:
    return TicketCreateRequest(
        complaint="There has been no water supply in our area for three days and nobody is responding.",
        language="English",
        location=location,
    )


def test_ticket_lifecycle_and_escalation():
    db = session()
    payload = water_payload()
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


def test_idempotent_ticket_creation_replays_same_ticket():
    db = session()
    payload = water_payload()
    analysis = analyze_complaint(payload.complaint, supplied_location=payload.location)

    first = create_ticket(db, payload, analysis, idempotency_key="citizen-submit-001")
    second = create_ticket(db, payload, analysis, idempotency_key="citizen-submit-001")

    assert second.ticket_code == first.ticket_code
    assert len(db.query(type(first)).all()) == 1


def test_idempotency_key_reuse_with_different_payload_fails():
    db = session()
    first_payload = water_payload()
    first_analysis = analyze_complaint(first_payload.complaint, supplied_location=first_payload.location)
    create_ticket(db, first_payload, first_analysis, idempotency_key="citizen-submit-002")

    second_payload = water_payload("Kothrud")
    second_analysis = analyze_complaint(second_payload.complaint, supplied_location=second_payload.location)
    try:
        create_ticket(db, second_payload, second_analysis, idempotency_key="citizen-submit-002")
    except IdempotencyConflict:
        pass
    else:
        raise AssertionError("Expected idempotency conflict")


def test_resolved_ticket_cannot_be_reopened_by_status_patch():
    db = session()
    payload = water_payload()
    analysis = analyze_complaint(payload.complaint, supplied_location=payload.location)
    ticket = create_ticket(db, payload, analysis)
    resolved = update_status(db, ticket, "RESOLVED", note="Repair verified.")

    try:
        update_status(db, resolved, "IN_PROGRESS")
    except InvalidStatusTransition:
        pass
    else:
        raise AssertionError("Resolved ticket must not silently reopen")
