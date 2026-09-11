import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, engine, get_db
from .models import User
from .schemas import (
    AnalyzeComplaintRequest,
    AnalyticsResponse,
    ComplaintAnalysis,
    LoginRequest,
    SignUpRequest,
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
from .services.pipeline import analyze_complaint
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
logger = logging.getLogger("civicresolve.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_security()
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.4.0",
    description="Multilingual AI-assisted civic complaint understanding and resolution prototype.",
    lifespan=lifespan,
)

if settings.allowed_host_list != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Idempotency-Key", "X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    supplied_request_id = request.headers.get("X-Request-ID", "").strip()
    request_id = supplied_request_id[:128] if supplied_request_id else str(uuid.uuid4())
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.path.startswith(f"{settings.api_prefix}/auth"):
            response.headers["Cache-Control"] = "no-store"
        return response
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            status_code,
            duration_ms,
        )


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("database_readiness_failed")
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc
    return {"status": "ready", "database": "reachable"}


@app.post(f"{settings.api_prefix}/auth/signup", response_model=UserResponse, status_code=201)
def signup(payload: SignUpRequest, response: Response, db: Session = Depends(get_db)) -> UserResponse:
    try:
        user = create_user(db, payload.name, payload.email, payload.password, role="CITIZEN")
    except EmailAlreadyRegistered as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    set_session_cookie(response, create_session_token(user))
    return user_response(user)


@app.post(f"{settings.api_prefix}/auth/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> UserResponse:
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    set_session_cookie(response, create_session_token(user))
    return user_response(user)


@app.post(f"{settings.api_prefix}/auth/employee-login", response_model=UserResponse)
def employee_login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> UserResponse:
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if user.role not in {"OFFICER", "ADMIN"}:
        raise HTTPException(status_code=403, detail="This account is not registered as a CivicResolve employee account.")
    set_session_cookie(response, create_session_token(user))
    return user_response(user)


@app.post(f"{settings.api_prefix}/auth/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(settings.auth_cookie_name, path="/")


@app.get(f"{settings.api_prefix}/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return user_response(current_user)


@app.post(f"{settings.api_prefix}/complaints/analyze", response_model=ComplaintAnalysis)
def analyze(
    payload: AnalyzeComplaintRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ComplaintAnalysis:
    result = analyze_complaint(
        complaint=payload.complaint,
        selected_language="Auto",
        supplied_location=payload.location,
        landmark=payload.landmark,
    )
    result.duplicate_candidates = find_duplicates(db, result, payload.complaint)
    return result


@app.post(f"{settings.api_prefix}/tickets", response_model=TicketResponse, status_code=201)
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
    if result.missing_information:
        raise HTTPException(
            status_code=422,
            detail={"message": "Clarification required before ticket creation.", "analysis": result.model_dump()},
        )
    try:
        ticket = create_ticket(
            db,
            payload,
            result,
            idempotency_key=idempotency_key,
            submitted_by_user_id=current_user.id,
        )
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return to_response(ticket)


@app.get(f"{settings.api_prefix}/tickets/mine", response_model=list[TicketResponse])
def my_tickets(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketResponse]:
    return [to_response(get_ticket(db, item.ticket_code)) for item in list_user_tickets(db, current_user.id, limit)]


@app.get(f"{settings.api_prefix}/tickets", response_model=list[TicketResponse])
def tickets(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> list[TicketResponse]:
    return [to_response(get_ticket(db, item.ticket_code)) for item in list_tickets(db, limit)]


@app.get(f"{settings.api_prefix}/tickets/{{ticket_code}}", response_model=TicketResponse)
def ticket(
    ticket_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketResponse:
    try:
        current = get_ticket(db, ticket_code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    if current_user.role not in {"OFFICER", "ADMIN"} and current.submitted_by_user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return to_response(current)


@app.patch(f"{settings.api_prefix}/tickets/{{ticket_code}}/status", response_model=TicketResponse)
def change_status(
    ticket_code: str,
    payload: TicketStatusRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> TicketResponse:
    try:
        current = get_ticket(db, ticket_code)
        updated = update_status(
            db,
            current,
            status=payload.status,
            note=payload.note,
            assigned_officer=payload.assigned_officer,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_response(updated)


@app.post(f"{settings.api_prefix}/tickets/{{ticket_code}}/simulate-breach", response_model=TicketResponse)
def breach(
    ticket_code: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> TicketResponse:
    try:
        current = get_ticket(db, ticket_code)
        return to_response(simulate_breach(db, current))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get(f"{settings.api_prefix}/analytics", response_model=AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> AnalyticsResponse:
    return AnalyticsResponse(**analytics(db))
