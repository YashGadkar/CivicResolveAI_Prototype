import re
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..models import AuditEvent, Ticket
from ..schemas import ComplaintAnalysis, DuplicateCandidate, TicketCreateRequest, TicketResponse


SLA_HOURS = {"CRITICAL": 2, "HIGH": 8, "MEDIUM": 24, "LOW": 72}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def add_audit(db: Session, ticket: Ticket, event: str, detail: str) -> None:
    db.add(AuditEvent(ticket_id=ticket.id, event=event, detail=detail))


def ticket_code() -> str:
    date_part = utcnow().strftime("%y%m%d")
    random_part = uuid.uuid4().hex[:6].upper()
    return f"CR-{date_part}-{random_part}"


def sla_deadline(priority: str) -> datetime:
    return utcnow() + timedelta(hours=SLA_HOURS.get(priority, 24))


def compute_sla_state(ticket: Ticket) -> str:
    now = utcnow()
    deadline = ticket.sla_deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if now >= deadline:
        return "BREACHED"
    total_hours = SLA_HOURS.get(ticket.priority, 24)
    remaining = deadline - now
    return "APPROACHING" if remaining <= timedelta(hours=max(1, total_hours * 0.25)) else "SAFE"


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[\w]+", value.casefold(), flags=re.UNICODE))


def text_similarity(left: str, right: str) -> float:
    a, b = _tokens(left), _tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_duplicates(db: Session, analysis: ComplaintAnalysis, complaint: str, limit: int = 3) -> list[DuplicateCandidate]:
    stmt = select(Ticket).where(Ticket.category == analysis.category).order_by(Ticket.created_at.desc()).limit(50)
    tickets = db.scalars(stmt).all()
    candidates: list[DuplicateCandidate] = []
    for ticket in tickets:
        similarity = text_similarity(complaint, ticket.complaint)
        if analysis.location and ticket.location.casefold() == analysis.location.casefold():
            similarity = min(1.0, similarity + 0.18)
        if similarity >= 0.5:
            candidates.append(
                DuplicateCandidate(
                    ticket_code=ticket.ticket_code,
                    summary=f"{ticket.category} complaint in {ticket.location}",
                    similarity=round(similarity, 2),
                )
            )
    candidates.sort(key=lambda item: item.similarity, reverse=True)
    return candidates[:limit]


def create_ticket(db: Session, payload: TicketCreateRequest, analysis: ComplaintAnalysis) -> Ticket:
    if analysis.missing_information:
        raise ValueError("Required clarification is missing before ticket creation.")
    if not analysis.location:
        raise ValueError("Location is required before ticket creation.")

    ticket = Ticket(
        ticket_code=ticket_code(),
        complaint=payload.complaint,
        language=analysis.language,
        location=analysis.location,
        landmark=payload.landmark,
        contact=payload.contact,
        category=analysis.category,
        duration=analysis.duration,
        priority=analysis.priority,
        urgency=analysis.urgency,
        department=analysis.department,
        confidence=analysis.confidence,
        sla_deadline=sla_deadline(analysis.priority),
        sla_state="SAFE",
        resolution_recommendation=analysis.resolution_recommendation,
        citizen_response=analysis.citizen_response,
        reasoning_summary=analysis.reasoning_summary,
        duplicate_of=payload.duplicate_of,
    )
    db.add(ticket)
    db.flush()

    add_audit(db, ticket, "COMPLAINT_SUBMITTED", "Citizen complaint submitted.")
    add_audit(db, ticket, "AI_ANALYZED", f"AI-assisted deterministic analysis classified {analysis.category}.")
    add_audit(db, ticket, "PRIORITY_ASSIGNED", f"Priority assigned: {analysis.priority}.")
    add_audit(db, ticket, "DEPARTMENT_ROUTED", f"Routed to {analysis.department}.")
    add_audit(db, ticket, "TICKET_CREATED", f"Ticket {ticket.ticket_code} created with configurable prototype SLA.")
    if payload.duplicate_of:
        add_audit(db, ticket, "RELATED_TICKET_LINKED", f"Citizen linked possible related ticket {payload.duplicate_of}.")

    db.commit()
    return get_ticket(db, ticket.ticket_code)


def get_ticket(db: Session, code: str) -> Ticket:
    stmt = (
        select(Ticket)
        .where(func.upper(Ticket.ticket_code) == code.upper())
        .options(selectinload(Ticket.audit_events))
    )
    ticket = db.scalar(stmt)
    if not ticket:
        raise LookupError(code)

    new_state = compute_sla_state(ticket)
    if new_state != ticket.sla_state:
        ticket.sla_state = new_state
        if new_state == "BREACHED" and ticket.status != "RESOLVED":
            ticket.status = "ESCALATED"
            add_audit(db, ticket, "SLA_BREACHED", "Configurable prototype SLA breached; ticket escalated automatically.")
            add_audit(db, ticket, "SUPERVISOR_NOTIFIED", "Prototype supervisor notification generated.")
            add_audit(db, ticket, "CITIZEN_NOTIFIED", "Citizen escalation update generated.")
        db.commit()
        return get_ticket(db, code)
    return ticket


def list_tickets(db: Session, limit: int = 100) -> list[Ticket]:
    stmt = select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())


def update_status(
    db: Session,
    ticket: Ticket,
    status: str,
    note: str | None = None,
    assigned_officer: str | None = None,
) -> Ticket:
    previous = ticket.status
    ticket.status = status
    if assigned_officer is not None:
        ticket.assigned_officer = assigned_officer or None
    add_audit(db, ticket, "STATUS_CHANGED", f"{previous} → {status}. {note or ''}".strip())
    if status == "RESOLVED":
        ticket.sla_state = "SAFE" if compute_sla_state(ticket) != "BREACHED" else "BREACHED"
        add_audit(db, ticket, "RESOLVED", note or "Ticket marked resolved.")
    db.commit()
    return get_ticket(db, ticket.ticket_code)


def simulate_breach(db: Session, ticket: Ticket) -> Ticket:
    ticket.sla_deadline = utcnow() - timedelta(minutes=1)
    ticket.sla_state = "BREACHED"
    ticket.status = "ESCALATED"
    add_audit(db, ticket, "SLA_BREACHED", "Hackathon simulation: configurable prototype SLA was forced to BREACHED.")
    add_audit(db, ticket, "AUTO_ESCALATED", "Escalation Agent changed ticket status to ESCALATED.")
    add_audit(db, ticket, "SUPERVISOR_NOTIFIED", "Prototype supervisor notification generated.")
    add_audit(db, ticket, "CITIZEN_NOTIFIED", "Citizen escalation update generated.")
    db.commit()
    return get_ticket(db, ticket.ticket_code)


def to_response(ticket: Ticket) -> TicketResponse:
    return TicketResponse(
        ticket_code=ticket.ticket_code,
        complaint=ticket.complaint,
        language=ticket.language,
        location=ticket.location,
        landmark=ticket.landmark,
        category=ticket.category,
        duration=ticket.duration,
        priority=ticket.priority,
        urgency=ticket.urgency,
        department=ticket.department,
        confidence=ticket.confidence,
        status=ticket.status,
        sla_deadline=ticket.sla_deadline,
        sla_state=ticket.sla_state,
        resolution_recommendation=ticket.resolution_recommendation,
        citizen_response=ticket.citizen_response,
        reasoning_summary=ticket.reasoning_summary,
        assigned_officer=ticket.assigned_officer,
        duplicate_of=ticket.duplicate_of,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        audit_events=[
            {"event": event.event, "detail": event.detail, "created_at": event.created_at}
            for event in ticket.audit_events
        ],
    )


def analytics(db: Session) -> dict:
    tickets = list(db.scalars(select(Ticket)).all())
    total = len(tickets)
    status_counts = Counter(t.status for t in tickets)
    sla_breaches = sum(1 for t in tickets if compute_sla_state(t) == "BREACHED")
    closed_without_breach = sum(1 for t in tickets if t.status == "RESOLVED" and compute_sla_state(t) != "BREACHED")
    resolved = status_counts.get("RESOLVED", 0)
    compliance = (closed_without_breach / resolved * 100) if resolved else 100.0

    return {
        "label": "Synthetic / Demo Data",
        "total": total,
        "pending": status_counts.get("SUBMITTED", 0) + status_counts.get("ASSIGNED", 0),
        "in_progress": status_counts.get("IN_PROGRESS", 0),
        "resolved": resolved,
        "escalated": status_counts.get("ESCALATED", 0),
        "sla_breaches": sla_breaches,
        "sla_compliance": round(compliance, 1),
        "by_category": dict(Counter(t.category for t in tickets)),
        "by_department": dict(Counter(t.department for t in tickets)),
        "by_priority": dict(Counter(t.priority for t in tickets)),
        "by_status": dict(status_counts),
        "by_location": dict(Counter(t.location for t in tickets)),
    }
