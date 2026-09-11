import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, engine, get_db
from .schemas import (
    AnalyzeComplaintRequest,
    AnalyticsResponse,
    ComplaintAnalysis,
    TicketCreateRequest,
    TicketResponse,
    TicketStatusRequest,
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
    simulate_breach,
    to_response,
    update_status,
)

settings = get_settings()
logger = logging.getLogger("civicresolve.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Zero-config local developer mode remains convenient. Production containers set
    # AUTO_CREATE_SCHEMA=false and apply reviewed Alembic migrations before serving.
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="AI-assisted civic complaint understanding and resolution prototype.",
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
        return response
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        # Deliberately avoid query strings, request bodies, contact details and complaint text.
        logger.info(
            "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            status_code,
            duration_ms,
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - exercised by infrastructure failures
        logger.exception("database_readiness_failed")
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc
    return {"status": "ready", "database": "reachable"}


@app.post(f"{settings.api_prefix}/complaints/analyze", response_model=ComplaintAnalysis)
def analyze(payload: AnalyzeComplaintRequest, db: Session = Depends(get_db)) -> ComplaintAnalysis:
    result = analyze_complaint(
        complaint=payload.complaint,
        selected_language=payload.language,
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
) -> TicketResponse:
    result = analyze_complaint(
        complaint=payload.complaint,
        selected_language=payload.language,
        supplied_location=payload.location,
        landmark=payload.landmark,
    )
    if result.missing_information:
        raise HTTPException(
            status_code=422,
            detail={"message": "Clarification required before ticket creation.", "analysis": result.model_dump()},
        )
    try:
        ticket = create_ticket(db, payload, result, idempotency_key=idempotency_key)
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return to_response(ticket)


@app.get(f"{settings.api_prefix}/tickets", response_model=list[TicketResponse])
def tickets(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[TicketResponse]:
    result: list[TicketResponse] = []
    for item in list_tickets(db, limit):
        # get_ticket applies automatic SLA transitions atomically when needed.
        result.append(to_response(get_ticket(db, item.ticket_code)))
    return result


@app.get(f"{settings.api_prefix}/tickets/{{ticket_code}}", response_model=TicketResponse)
def ticket(ticket_code: str, db: Session = Depends(get_db)) -> TicketResponse:
    try:
        return to_response(get_ticket(db, ticket_code))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc


@app.patch(f"{settings.api_prefix}/tickets/{{ticket_code}}/status", response_model=TicketResponse)
def change_status(
    ticket_code: str,
    payload: TicketStatusRequest,
    db: Session = Depends(get_db),
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
def breach(ticket_code: str, db: Session = Depends(get_db)) -> TicketResponse:
    try:
        current = get_ticket(db, ticket_code)
        return to_response(simulate_breach(db, current))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get(f"{settings.api_prefix}/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)) -> AnalyticsResponse:
    return AnalyticsResponse(**analytics(db))
