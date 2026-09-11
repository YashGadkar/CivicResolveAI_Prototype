from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User
from .schemas import (
    AnalyzeComplaintRequest,
    AnalyticsResponse,
    ComplaintAnalysis,
    ComplaintBatchAnalysis,
    LocationVerificationRequest,
    LocationVerificationResponse,
    LoginRequest,
    SignUpRequest,
    StaffCitizenResponse,
    StaffTicketResponse,
    TicketCreateRequest,
    TicketResponse,
    TicketStatusRequest,
    UserResponse,
)
from .services.auth import (
    AuthenticationError,
    EmailAlreadyRegistered,
    authenticate_user,
    create_session_token,
    create_user,
    decode_session_token,
)
from .services.location import verify_location
from .services.pipeline import analyze_complaint, analyze_complaints, detect_language
from .services.ticketing import (
    IdempotencyConflict,
    InvalidStatusTransition,
    analytics,
    create_ticket,
    find_duplicates,
    get_ticket,
    list_tickets,
    list_user_tickets,
    simulate_breach,
    to_response,
    update_status,
)

settings = get_settings()
router = APIRouter(prefix=settings.api_prefix)


def user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, name=user.name, email=user.email, role=user.role, created_at=user.created_at)


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.jwt_exp_hours * 3600,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
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


def require_staff(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {"OFFICER", "ADMIN"}:
        raise HTTPException(status_code=403, detail="Employee access is required.")
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access is required.")
    return current_user


def apply_location_verification(result: ComplaintAnalysis, enabled: bool) -> ComplaintAnalysis:
    if not enabled or not result.location:
        return result
    verification = verify_location(result.location)
    result.location_verified = verification.valid
    result.location_display_name = verification.canonical_name
    result.location_verification_message = verification.message
    if verification.valid and verification.canonical_name:
        result.location = verification.canonical_name
        if "location" in result.missing_information:
            result.missing_information.remove("location")
        result.clarification_questions = [
            q for q in result.clarification_questions
            if "location" not in q.casefold() and "area" not in q.casefold()
        ]
    elif not verification.valid:
        result.location = None
        if "location" not in result.missing_information:
            result.missing_information.insert(0, "location")
        result.clarification_questions.insert(0, verification.message)
        result.citizen_response = verification.message
    return result


def staff_response(db: Session, ticket_code: str) -> StaffTicketResponse:
    current = get_ticket(db, ticket_code)
    citizen = db.get(User, current.submitted_by_user_id) if current.submitted_by_user_id else None
    base = to_response(current).model_dump()
    return StaffTicketResponse(
        **base,
        citizen=StaffCitizenResponse(
            name=citizen.name,
            email=citizen.email,
            contact=current.contact,
        ) if citizen else None,
    )


@router.post("/auth/signup", response_model=UserResponse, status_code=201)
def signup(payload: SignUpRequest, response: Response, db: Session = Depends(get_db)) -> UserResponse:
    try:
        user = create_user(db, payload.name, payload.email, payload.password, role="CITIZEN")
    except EmailAlreadyRegistered as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    set_session_cookie(response, create_session_token(user))
    return user_response(user)


@router.post("/auth/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> UserResponse:
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    set_session_cookie(response, create_session_token(user))
    return user_response(user)


@router.post("/auth/employee-login", response_model=UserResponse)
def employee_login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> UserResponse:
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if user.role not in {"OFFICER", "ADMIN"}:
        raise HTTPException(status_code=403, detail="This account is not registered as a CivicResolve employee account.")
    set_session_cookie(response, create_session_token(user))
    return user_response(user)


@router.post("/auth/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(settings.auth_cookie_name, path="/")


@router.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return user_response(current_user)


@router.post("/locations/verify", response_model=LocationVerificationResponse)
def verify_location_endpoint(payload: LocationVerificationRequest, _current_user: User = Depends(get_current_user)) -> LocationVerificationResponse:
    return verify_location(payload.location)


@router.post("/complaints/analyze", response_model=ComplaintAnalysis)
def analyze(payload: AnalyzeComplaintRequest, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)) -> ComplaintAnalysis:
    result = analyze_complaint(
        complaint=payload.complaint,
        selected_language="Auto",
        supplied_location=payload.location,
        landmark=payload.landmark,
    )
    result = apply_location_verification(result, payload.verify_location)
    result.duplicate_candidates = find_duplicates(db, result, payload.complaint)
    return result


@router.post("/complaints/analyze-batch", response_model=ComplaintBatchAnalysis)
def analyze_batch(payload: AnalyzeComplaintRequest, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)) -> ComplaintBatchAnalysis:
    issues = analyze_complaints(payload.complaint, supplied_location=payload.location, landmark=payload.landmark)
    verified_cache: dict[str, LocationVerificationResponse] = {}
    for issue in issues:
        if payload.verify_location and issue.location:
            key = issue.location.casefold().strip()
            verification = verified_cache.get(key)
            if verification is None:
                verification = verify_location(issue.location)
                verified_cache[key] = verification
            issue.location_verified = verification.valid
            issue.location_display_name = verification.canonical_name
            issue.location_verification_message = verification.message
            if verification.valid and verification.canonical_name:
                issue.location = verification.canonical_name
                if "location" in issue.missing_information:
                    issue.missing_information.remove("location")
            else:
                issue.location = None
                if "location" not in issue.missing_information:
                    issue.missing_information.insert(0, "location")
                issue.clarification_questions.insert(0, verification.message)
                issue.citizen_response = verification.message
        issue.duplicate_candidates = find_duplicates(db, issue, issue.source_text or payload.complaint)
    language, code, _ = detect_language(payload.complaint)
    return ComplaintBatchAnalysis(language=language, language_code=code, issue_count=len(issues), issues=issues)


@router.post("/tickets", response_model=TicketResponse, status_code=201)
def create(
    payload: TicketCreateRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=128),
    current_user: User = Depends(get_current_user),
) -> TicketResponse:
    result = analyze_complaint(
        complaint=payload.complaint,
        selected_language="Auto",
        supplied_location=payload.location,
        landmark=payload.landmark,
    )
    result = apply_location_verification(result, payload.verify_location)
    if result.missing_information:
        raise HTTPException(status_code=422, detail={"message": "Clarification required before ticket creation.", "analysis": result.model_dump()})
    try:
        ticket = create_ticket(db, payload, result, idempotency_key=idempotency_key, submitted_by_user_id=current_user.id)
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return to_response(ticket)


@router.get("/tickets/mine", response_model=list[TicketResponse])
def my_tickets(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[TicketResponse]:
    return [to_response(get_ticket(db, item.ticket_code)) for item in list_user_tickets(db, current_user.id, limit)]


@router.get("/tickets", response_model=list[TicketResponse])
def tickets(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), _current_user: User = Depends(require_staff)) -> list[TicketResponse]:
    return [to_response(get_ticket(db, item.ticket_code)) for item in list_tickets(db, limit)]


@router.get("/tickets/{ticket_code}", response_model=TicketResponse)
def ticket(ticket_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TicketResponse:
    try:
        current = get_ticket(db, ticket_code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    if current_user.role not in {"OFFICER", "ADMIN"} and current.submitted_by_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return to_response(current)


@router.get("/staff/tickets/{ticket_code}", response_model=StaffTicketResponse)
def staff_ticket(ticket_code: str, db: Session = Depends(get_db), _current_user: User = Depends(require_staff)) -> StaffTicketResponse:
    try:
        return staff_response(db, ticket_code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc


@router.patch("/tickets/{ticket_code}/status", response_model=TicketResponse)
def change_status(ticket_code: str, payload: TicketStatusRequest, db: Session = Depends(get_db), _current_user: User = Depends(require_staff)) -> TicketResponse:
    try:
        current = get_ticket(db, ticket_code)
        updated = update_status(db, current, status=payload.status, note=payload.note, assigned_officer=payload.assigned_officer)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_response(updated)


@router.post("/tickets/{ticket_code}/simulate-breach", response_model=TicketResponse)
def breach(ticket_code: str, db: Session = Depends(get_db), _current_user: User = Depends(require_staff)) -> TicketResponse:
    try:
        current = get_ticket(db, ticket_code)
        return to_response(simulate_breach(db, current))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db), _current_user: User = Depends(require_admin)) -> AnalyticsResponse:
    return AnalyticsResponse(**analytics(db))
