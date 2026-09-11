from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
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


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-assisted civic complaint understanding and resolution prototype.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


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
def create(payload: TicketCreateRequest, db: Session = Depends(get_db)) -> TicketResponse:
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
        ticket = create_ticket(db, payload, result)
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
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    return to_response(
        update_status(
            db,
            current,
            status=payload.status,
            note=payload.note,
            assigned_officer=payload.assigned_officer,
        )
    )


@app.post(f"{settings.api_prefix}/tickets/{{ticket_code}}/simulate-breach", response_model=TicketResponse)
def breach(ticket_code: str, db: Session = Depends(get_db)) -> TicketResponse:
    try:
        current = get_ticket(db, ticket_code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    if current.status == "RESOLVED":
        raise HTTPException(status_code=409, detail="Resolved tickets cannot be escalated.")
    return to_response(simulate_breach(db, current))


@app.get(f"{settings.api_prefix}/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)) -> AnalyticsResponse:
    return AnalyticsResponse(**analytics(db))
