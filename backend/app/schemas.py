from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Priority = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
AgentStatus = Literal["WAITING", "PROCESSING", "COMPLETED", "ACTION REQUIRED"]


class AnalyzeComplaintRequest(BaseModel):
    complaint: str = Field(min_length=10, max_length=5000)
    language: str = Field(default="English", max_length=24)
    location: str | None = Field(default=None, max_length=255)
    landmark: str | None = Field(default=None, max_length=255)

    @field_validator("complaint", "location", "landmark", mode="before")
    @classmethod
    def strip_strings(cls, value):
        return value.strip() if isinstance(value, str) else value


class AgentStage(BaseModel):
    name: str
    status: AgentStatus
    output: str
    processing_ms: int


class DuplicateCandidate(BaseModel):
    ticket_code: str
    summary: str
    similarity: float


class ComplaintAnalysis(BaseModel):
    category: str
    location: str | None
    landmark: str | None
    duration: str | None
    priority: Priority
    urgency: Priority
    department: str
    missing_information: list[str]
    clarification_questions: list[str]
    resolution_recommendation: list[str]
    language: str
    confidence: float = Field(ge=0, le=1)
    reasoning_summary: str
    citizen_response: str
    agent_trace: list[AgentStage]
    duplicate_candidates: list[DuplicateCandidate] = Field(default_factory=list)


class TicketCreateRequest(AnalyzeComplaintRequest):
    contact: str | None = Field(default=None, max_length=255)
    duplicate_of: str | None = Field(default=None, max_length=32)


class TicketStatusRequest(BaseModel):
    status: Literal[
        "SUBMITTED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "ESCALATED"
    ]
    note: str | None = Field(default=None, max_length=1000)
    assigned_officer: str | None = Field(default=None, max_length=120)


class AuditEventResponse(BaseModel):
    event: str
    detail: str
    created_at: datetime


class TicketResponse(BaseModel):
    ticket_code: str
    complaint: str
    language: str
    location: str
    landmark: str | None
    category: str
    duration: str | None
    priority: Priority
    urgency: Priority
    department: str
    confidence: float
    status: str
    sla_deadline: datetime
    sla_state: str
    resolution_recommendation: list[str]
    citizen_response: str
    reasoning_summary: str
    assigned_officer: str | None
    duplicate_of: str | None
    created_at: datetime
    updated_at: datetime
    audit_events: list[AuditEventResponse]


class AnalyticsResponse(BaseModel):
    label: str = "Synthetic / Demo Data"
    total: int
    pending: int
    in_progress: int
    resolved: int
    escalated: int
    sla_breaches: int
    sla_compliance: float
    by_category: dict[str, int]
    by_department: dict[str, int]
    by_priority: dict[str, int]
    by_status: dict[str, int]
    by_location: dict[str, int]
