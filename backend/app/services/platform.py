import hashlib
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..models import Attachment, AuditEvent, Ticket, TicketMeta, User
from ..platform_schemas import AttachmentResponse, IncidentResponse, TicketMetaResponse
from .location import verify_location
from .ticketing import add_audit, get_ticket, to_response

EMERGENCY_TERMS = {
    "open manhole", "live wire", "electrocution", "fire", "collapsed", "collapse", "gas leak",
    "explosion", "flooding", "flood", "tree fallen on road", "danger to life", "accident risk",
    "धोका", "आग", "विद्युत तार", "मॅनहोल", "खुला मैनहोल", "करंट", "बाढ़", "पूर",
}
ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp", "video/mp4", "application/pdf"
}
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
UPLOAD_ROOT = Path("uploads")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _slug(value: str) -> str:
    value = re.sub(r"[^\w]+", "-", value.casefold(), flags=re.UNICODE).strip("-")
    return value[:64] or "unknown"


def incident_key(ticket: Ticket) -> str:
    basis = f"{ticket.category}|{_slug(ticket.location)}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]


def emergency_from_text(text: str) -> bool:
    value = text.casefold()
    return any(term in value for term in EMERGENCY_TERMS)


def _location_parts(ticket: Ticket) -> tuple[str | None, str | None, str | None, float | None, float | None]:
    verification = verify_location(ticket.location)
    if not verification.valid:
        return None, None, None, None, None
    name = verification.canonical_name or ticket.location
    parts = [p.strip() for p in name.split(",") if p.strip()]
    city = parts[-4] if len(parts) >= 4 else (parts[-2] if len(parts) >= 2 else None)
    ward = None
    zone = None
    lower = [p.casefold() for p in parts]
    for idx, part in enumerate(lower):
        if "ward" in part:
            ward = parts[idx]
        if any(token in part for token in ("zone", "taluka", "tehsil", "district")):
            zone = parts[idx]
    return ward, zone, city, verification.latitude, verification.longitude


def ensure_meta(db: Session, ticket: Ticket, commit: bool = True) -> TicketMeta:
    meta = db.scalar(select(TicketMeta).where(TicketMeta.ticket_id == ticket.id))
    if meta:
        return meta
    ward, zone, city, lat, lon = _location_parts(ticket)
    meta = TicketMeta(
        ticket_id=ticket.id,
        ward=ward,
        zone=zone,
        city=city,
        latitude=lat,
        longitude=lon,
        emergency=emergency_from_text(ticket.complaint),
        incident_key=incident_key(ticket),
    )
    db.add(meta)
    add_audit(db, ticket, "CIVIC_CONTEXT_ENRICHED", "Verified location context and incident grouping prepared.")
    if meta.emergency:
        add_audit(db, ticket, "SAFETY_FLAG_RAISED", "Complaint contains a potential immediate safety risk and requires prompt human review.")
    if commit:
        db.commit()
    else:
        db.flush()
    return meta


def related_report_count(db: Session, meta: TicketMeta) -> int:
    if not meta.incident_key:
        return 1
    return int(db.scalar(select(func.count()).select_from(TicketMeta).where(TicketMeta.incident_key == meta.incident_key)) or 1)


def meta_response(db: Session, ticket: Ticket) -> TicketMetaResponse:
    meta = ensure_meta(db, ticket)
    return TicketMetaResponse(
        ward=meta.ward,
        zone=meta.zone,
        city=meta.city,
        latitude=meta.latitude,
        longitude=meta.longitude,
        emergency=meta.emergency,
        incident_key=meta.incident_key,
        related_reports=related_report_count(db, meta),
        archived=meta.archived_at is not None,
        citizen_confirmation=meta.citizen_confirmation,
        rating=meta.rating,
        feedback=meta.feedback,
        resolution_note=meta.resolution_note,
    )


def list_visible_tickets(db: Session, user: User | None = None, include_archived: bool = False, staff: bool = False) -> list[Ticket]:
    stmt = select(Ticket).options(selectinload(Ticket.audit_events), selectinload(Ticket.attachments)).order_by(Ticket.created_at.desc())
    if user and not staff:
        stmt = stmt.where(Ticket.submitted_by_user_id == user.id)
    tickets = list(db.scalars(stmt).all())
    visible: list[Ticket] = []
    for ticket in tickets:
        meta = ensure_meta(db, ticket)
        if include_archived or meta.archived_at is None:
            visible.append(ticket)
    return visible


def archive_ticket(db: Session, ticket: Ticket, actor: User) -> TicketMeta:
    meta = ensure_meta(db, ticket, commit=False)
    if meta.archived_at is None:
        meta.archived_at = utcnow()
        add_audit(db, ticket, "TICKET_ARCHIVED", f"Ticket removed from the active citizen workspace by {actor.role.lower()} account.")
        db.commit()
    return meta


def restore_ticket(db: Session, ticket: Ticket, actor: User) -> TicketMeta:
    meta = ensure_meta(db, ticket, commit=False)
    if meta.archived_at is not None:
        meta.archived_at = None
        add_audit(db, ticket, "TICKET_RESTORED", f"Ticket restored by {actor.role.lower()} account.")
        db.commit()
    return meta


def confirm_resolution(db: Session, ticket: Ticket, resolved: bool, rating: int | None, feedback: str | None) -> TicketMeta:
    meta = ensure_meta(db, ticket, commit=False)
    if resolved:
        meta.citizen_confirmation = "CONFIRMED"
        meta.rating = rating
        meta.feedback = feedback
        add_audit(db, ticket, "CITIZEN_CONFIRMED_RESOLUTION", "Citizen confirmed that the reported issue was resolved.")
    else:
        meta.citizen_confirmation = "REOPENED"
        meta.feedback = feedback
        ticket.status = "IN_PROGRESS"
        add_audit(db, ticket, "CITIZEN_REOPENED_TICKET", "Citizen reported that the issue is not resolved; ticket returned to active work.")
    db.commit()
    return meta


def resolve_with_note(db: Session, ticket: Ticket, note: str) -> TicketMeta:
    meta = ensure_meta(db, ticket, commit=False)
    meta.resolution_note = note.strip()
    meta.citizen_confirmation = "PENDING"
    ticket.status = "RESOLVED"
    add_audit(db, ticket, "RESOLUTION_EVIDENCE_REQUESTED", "Employee marked work complete; citizen confirmation is pending.")
    add_audit(db, ticket, "RESOLUTION_NOTE_ADDED", meta.resolution_note)
    db.commit()
    return meta


def transfer_ticket(db: Session, ticket: Ticket, department: str, reason: str) -> Ticket:
    previous = ticket.department
    ticket.department = department.strip()
    add_audit(db, ticket, "DEPARTMENT_TRANSFERRED", f"{previous} → {ticket.department}. Reason: {reason.strip()}")
    db.commit()
    return get_ticket(db, ticket.ticket_code)


def assign_ticket(db: Session, ticket: Ticket, officer: str | None) -> Ticket:
    ticket.assigned_officer = officer.strip() if officer else None
    if ticket.status == "SUBMITTED" and officer:
        ticket.status = "ASSIGNED"
    add_audit(db, ticket, "OFFICER_ASSIGNMENT_UPDATED", f"Assigned officer: {ticket.assigned_officer or 'unassigned'}.")
    db.commit()
    return get_ticket(db, ticket.ticket_code)


def attachment_response(attachment: Attachment) -> AttachmentResponse:
    return AttachmentResponse(
        id=attachment.id,
        kind=attachment.kind,
        original_name=attachment.original_name,
        content_type=attachment.content_type,
        size_bytes=attachment.size_bytes,
        created_at=attachment.created_at,
    )


def save_attachment(db: Session, ticket: Ticket, user: User, filename: str, content_type: str, data: bytes, kind: str) -> Attachment:
    if content_type not in ALLOWED_MIME:
        raise ValueError("Unsupported evidence type. Use JPEG, PNG, WebP, MP4, or PDF.")
    if not data or len(data) > MAX_ATTACHMENT_BYTES:
        raise ValueError("Evidence must be between 1 byte and 10 MB.")
    safe_ext = Path(filename or "evidence").suffix.lower()[:10]
    stored = f"{ticket.id}-{hashlib.sha256(data).hexdigest()[:24]}{safe_ext}"
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_ROOT / stored
    if not path.exists():
        path.write_bytes(data)
    attachment = Attachment(
        ticket_id=ticket.id,
        uploaded_by_user_id=user.id,
        kind=kind,
        original_name=(filename or "evidence")[:255],
        stored_name=stored,
        content_type=content_type,
        size_bytes=len(data),
    )
    db.add(attachment)
    add_audit(db, ticket, "EVIDENCE_ADDED", f"{kind.replace('_', ' ').title()} uploaded: {attachment.original_name}.")
    db.commit()
    db.refresh(attachment)
    return attachment


def get_attachment(db: Session, attachment_id: str) -> Attachment:
    attachment = db.get(Attachment, attachment_id)
    if not attachment:
        raise LookupError(attachment_id)
    return attachment


def attachment_path(attachment: Attachment) -> Path:
    return UPLOAD_ROOT / attachment.stored_name


def incidents(db: Session) -> list[IncidentResponse]:
    tickets = list_visible_tickets(db, include_archived=False, staff=True)
    groups: dict[str, list[Ticket]] = defaultdict(list)
    for ticket in tickets:
        meta = ensure_meta(db, ticket)
        groups[meta.incident_key or incident_key(ticket)].append(ticket)
    result: list[IncidentResponse] = []
    for key, items in groups.items():
        latest = max(items, key=lambda t: t.created_at)
        active = [t for t in items if t.status != "RESOLVED"]
        rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        priority = max((t.priority for t in items), key=lambda p: rank.get(p, 0))
        result.append(IncidentResponse(
            incident_key=key,
            category=latest.category,
            location=latest.location,
            department=latest.department,
            priority=priority,
            report_count=len(items),
            active_count=len(active),
            latest_ticket=latest.ticket_code,
        ))
    return sorted(result, key=lambda item: (item.active_count, item.report_count), reverse=True)


def platform_analytics(db: Session) -> dict:
    tickets = list(db.scalars(select(Ticket)).all())
    metas = [ensure_meta(db, ticket) for ticket in tickets]
    ratings = [m.rating for m in metas if m.rating is not None]
    return {
        "incidents": [item.model_dump() for item in incidents(db)],
        "satisfaction_average": round(sum(ratings) / len(ratings), 2) if ratings else None,
        "rated_resolutions": len(ratings),
        "archived_tickets": sum(1 for m in metas if m.archived_at is not None),
        "emergency_tickets": sum(1 for m in metas if m.emergency),
        "by_ward": dict(Counter(m.ward for m in metas if m.ward)),
        "by_zone": dict(Counter(m.zone for m in metas if m.zone)),
    }
