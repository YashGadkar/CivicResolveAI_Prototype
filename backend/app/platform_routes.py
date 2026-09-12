from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User
from .platform_schemas import (
    AssistantRequest,
    AssistantResponse,
    AssignmentRequest,
    CitizenResolutionRequest,
    EnrichedTicketResponse,
    PlatformAnalyticsResponse,
    ResolutionRequest,
    TransferRequest,
    TranslationRequest,
    TranslationResponse,
)
from .services.assistant import answer_assistant
from .services.auth import AuthenticationError, decode_session_token
from .services.platform import (
    archive_ticket,
    assign_ticket,
    attachment_path,
    attachment_response,
    civic_departments,
    confirm_resolution,
    ensure_meta,
    get_attachment,
    incidents,
    list_visible_tickets,
    meta_response,
    platform_analytics,
    resolve_with_note,
    restore_ticket,
    save_attachment,
    transfer_ticket,
)
from .services.ticketing import get_ticket, to_response
from .services.translation import TranslationError, available_languages, translate_text

settings = get_settings()
router = APIRouter(prefix=f"{settings.api_prefix}/platform", tags=["Civic platform"])


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Sign in is required.")
    try:
        payload = decode_session_token(token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.") from exc
    user = db.get(User, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="Session user no longer exists.")
    return user


def staff_user(user: User = Depends(current_user)) -> User:
    if user.role not in {"OFFICER", "ADMIN"}:
        raise HTTPException(status_code=403, detail="Employee access is required.")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access is required.")
    return user


def _ticket_for_user(db: Session, code: str, user: User):
    try:
        ticket = get_ticket(db, code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    if user.role not in {"OFFICER", "ADMIN"} and ticket.submitted_by_user_id != user.id:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket


def _enriched(db: Session, ticket, user: User, include_citizen: bool = False) -> EnrichedTicketResponse:
    citizen = None
    if include_citizen and ticket.submitted_by_user_id:
        owner = db.get(User, ticket.submitted_by_user_id)
        if owner:
            citizen = {"name": owner.name, "email": owner.email, "contact": ticket.contact}
    return EnrichedTicketResponse(
        ticket=to_response(ticket).model_dump(mode="json"),
        meta=meta_response(db, ticket),
        attachments=[attachment_response(a) for a in ticket.attachments],
        citizen=citizen,
    )


@router.get("/tickets/mine", response_model=list[EnrichedTicketResponse])
def my_tickets(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role != "CITIZEN":
        raise HTTPException(status_code=403, detail="Citizen account required.")
    return [_enriched(db, t, user) for t in list_visible_tickets(db, user=user)]


@router.get("/tickets/{ticket_code}", response_model=EnrichedTicketResponse)
def ticket_detail(ticket_code: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    ticket = _ticket_for_user(db, ticket_code, user)
    return _enriched(db, ticket, user, include_citizen=user.role in {"OFFICER", "ADMIN"})


@router.get("/staff/tickets", response_model=list[EnrichedTicketResponse])
def staff_tickets(db: Session = Depends(get_db), user: User = Depends(staff_user)):
    return [_enriched(db, t, user, include_citizen=True) for t in list_visible_tickets(db, include_archived=False, staff=True)]


@router.get("/staff/departments", response_model=list[str])
def staff_departments(_user: User = Depends(staff_user)):
    return civic_departments()


@router.get("/staff/translation-languages", response_model=list[dict[str, str]])
def staff_translation_languages(_user: User = Depends(staff_user)):
    return available_languages()


@router.delete("/tickets/{ticket_code}", response_model=EnrichedTicketResponse)
def delete_ticket(ticket_code: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    ticket = _ticket_for_user(db, ticket_code, user)
    if user.role == "CITIZEN" and ticket.status in {"IN_PROGRESS", "ESCALATED"}:
        raise HTTPException(status_code=409, detail="Active work cannot be deleted. You can archive it after resolution or ask an employee for help.")
    archive_ticket(db, ticket, user)
    return _enriched(db, get_ticket(db, ticket_code), user, include_citizen=user.role in {"OFFICER", "ADMIN"})


@router.post("/tickets/{ticket_code}/restore", response_model=EnrichedTicketResponse)
def restore(ticket_code: str, db: Session = Depends(get_db), user: User = Depends(admin_user)):
    ticket = _ticket_for_user(db, ticket_code, user)
    restore_ticket(db, ticket, user)
    return _enriched(db, get_ticket(db, ticket_code), user, include_citizen=True)


@router.post("/tickets/{ticket_code}/confirm", response_model=EnrichedTicketResponse)
def citizen_confirm(ticket_code: str, payload: CitizenResolutionRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    ticket = _ticket_for_user(db, ticket_code, user)
    if user.role != "CITIZEN":
        raise HTTPException(status_code=403, detail="Citizen confirmation is available only to the complaint owner.")
    if ticket.status != "RESOLVED":
        raise HTTPException(status_code=409, detail="Resolution can be confirmed only after an employee marks the ticket resolved.")
    confirm_resolution(db, ticket, payload.resolved, payload.rating, payload.feedback)
    return _enriched(db, get_ticket(db, ticket_code), user)


@router.post("/staff/tickets/{ticket_code}/translate", response_model=TranslationResponse)
def staff_translate(ticket_code: str, payload: TranslationRequest, db: Session = Depends(get_db), user: User = Depends(staff_user)):
    ticket = _ticket_for_user(db, ticket_code, user)
    try:
        return TranslationResponse(**translate_text(ticket.complaint, payload.target_language, ticket.language))
    except TranslationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/staff/tickets/{ticket_code}/resolve", response_model=EnrichedTicketResponse)
def staff_resolve(ticket_code: str, payload: ResolutionRequest, db: Session = Depends(get_db), user: User = Depends(staff_user)):
    ticket = _ticket_for_user(db, ticket_code, user)
    resolve_with_note(db, ticket, payload.note)
    return _enriched(db, get_ticket(db, ticket_code), user, include_citizen=True)


@router.post("/staff/tickets/{ticket_code}/transfer", response_model=EnrichedTicketResponse)
def staff_transfer(ticket_code: str, payload: TransferRequest, db: Session = Depends(get_db), user: User = Depends(staff_user)):
    ticket = _ticket_for_user(db, ticket_code, user)
    try:
        transfer_ticket(db, ticket, payload.department, payload.reason, user)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _enriched(db, get_ticket(db, ticket_code), user, include_citizen=True)


@router.post("/staff/tickets/{ticket_code}/assign", response_model=EnrichedTicketResponse)
def staff_assign(ticket_code: str, payload: AssignmentRequest, db: Session = Depends(get_db), user: User = Depends(staff_user)):
    ticket = _ticket_for_user(db, ticket_code, user)
    assign_ticket(db, ticket, payload.officer)
    return _enriched(db, get_ticket(db, ticket_code), user, include_citizen=True)


@router.post("/tickets/{ticket_code}/evidence", response_model=EnrichedTicketResponse)
async def add_evidence(
    ticket_code: str,
    kind: str = "CITIZEN_EVIDENCE",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    ticket = _ticket_for_user(db, ticket_code, user)
    if user.role == "CITIZEN":
        kind = "CITIZEN_EVIDENCE"
    elif kind not in {"CITIZEN_EVIDENCE", "RESOLUTION_EVIDENCE"}:
        kind = "RESOLUTION_EVIDENCE"
    data = await file.read(10 * 1024 * 1024 + 1)
    try:
        save_attachment(db, ticket, user, file.filename or "evidence", file.content_type or "application/octet-stream", data, kind)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _enriched(db, get_ticket(db, ticket_code), user, include_citizen=user.role in {"OFFICER", "ADMIN"})


@router.get("/attachments/{attachment_id}")
def download_evidence(attachment_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    try:
        attachment = get_attachment(db, attachment_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Evidence not found.") from exc
    ticket = _ticket_for_user(db, get_ticket(db, attachment.ticket.ticket_code).ticket_code, user)
    path = attachment_path(attachment)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Evidence file is unavailable.")
    return FileResponse(path, media_type=attachment.content_type, filename=attachment.original_name)


@router.get("/incidents")
def incident_list(db: Session = Depends(get_db), _user: User = Depends(staff_user)):
    return incidents(db)


@router.get("/analytics", response_model=PlatformAnalyticsResponse)
def analytics(db: Session = Depends(get_db), _user: User = Depends(admin_user)):
    return PlatformAnalyticsResponse(**platform_analytics(db))


@router.post("/assistant", response_model=AssistantResponse)
def assistant(payload: AssistantRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return answer_assistant(db, user, payload.message)
