from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TicketMetaResponse(BaseModel):
    ward: str | None = None
    zone: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    emergency: bool = False
    incident_key: str | None = None
    related_reports: int = 1
    archived: bool = False
    citizen_confirmation: str = "PENDING"
    rating: int | None = None
    feedback: str | None = None
    resolution_note: str | None = None


class AttachmentResponse(BaseModel):
    id: str
    kind: str
    original_name: str
    content_type: str
    size_bytes: int
    created_at: datetime


class EnrichedTicketResponse(BaseModel):
    ticket: dict
    meta: TicketMetaResponse
    attachments: list[AttachmentResponse] = Field(default_factory=list)
    citizen: dict | None = None


class CitizenResolutionRequest(BaseModel):
    resolved: bool
    rating: int | None = Field(default=None, ge=1, le=5)
    feedback: str | None = Field(default=None, max_length=1000)


class ResolutionRequest(BaseModel):
    note: str = Field(min_length=3, max_length=2000)


class TransferRequest(BaseModel):
    department: str = Field(min_length=2, max_length=120)
    reason: str = Field(min_length=3, max_length=1000)


class AssignmentRequest(BaseModel):
    officer: str | None = Field(default=None, max_length=120)


class AssistantRequest(BaseModel):
    message: str = Field(min_length=2, max_length=5000)


class AssistantAction(BaseModel):
    type: Literal["NONE", "OPEN_TICKET", "OPEN_QUEUE", "CREATE_COMPLAINT", "SHOW_MY_TICKETS"] = "NONE"
    label: str | None = None
    value: str | None = None


class AssistantResponse(BaseModel):
    reply: str
    actions: list[AssistantAction] = Field(default_factory=list)
    data: dict = Field(default_factory=dict)


class IncidentResponse(BaseModel):
    incident_key: str
    category: str
    location: str
    department: str
    priority: str
    report_count: int
    active_count: int
    latest_ticket: str


class PlatformAnalyticsResponse(BaseModel):
    incidents: list[IncidentResponse] = Field(default_factory=list)
    satisfaction_average: float | None = None
    rated_resolutions: int = 0
    archived_tickets: int = 0
    emergency_tickets: int = 0
    by_ward: dict[str, int] = Field(default_factory=dict)
    by_zone: dict[str, int] = Field(default_factory=dict)
