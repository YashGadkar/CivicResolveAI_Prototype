import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Priority = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
AgentStatus = Literal["WAITING", "PROCESSING", "COMPLETED", "ACTION REQUIRED"]

GMAIL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._%+\-]{0,62}[A-Za-z0-9])?@gmail\.com$", re.IGNORECASE)


def validate_password_strength(value: str) -> str:
    if len(value) < 10:
        raise ValueError("Password must be at least 10 characters long.")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain a lowercase letter.")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain an uppercase letter.")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain a number.")
    if not re.search(r"[^A-Za-z0-9]", value):
        raise ValueError("Password must contain a special character.")
    return value


class SignUpRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(max_length=255)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def valid_gmail(cls, value):
        email = value.strip().lower() if isinstance(value, str) else value
        if not isinstance(email, str) or not GMAIL_RE.fullmatch(email):
            raise ValueError("Enter a valid Gmail address ending in @gmail.com.")
        return email

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return validate_password_strength(value)


class LoginRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime


class AnalyzeComplaintRequest(BaseModel):
    complaint: str = Field(min_length=10, max_length=5000)
    language: str = Field(default="Auto", max_length=24)
    location: str | None = Field(default=None, max_length=255)
    landmark: str | None = Field(default=None, max_length=255)
    verify_location: bool = False

    @field_validator("complaint", "location", "landmark", mode="before")
    @classmethod
    def strip_strings(cls, value):
        return value.strip() if isinstance(value, str) else value


class LocationVerificationRequest(BaseModel):
    location: str = Field(min_length=2, max_length=255)


class LocationVerificationResponse(BaseModel):
    input: str
    valid: bool
    canonical_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    provider: str = "OpenStreetMap Nominatim"
    message: str


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
    source_text: str | None = None
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
    language_code: str
    detected_script: str
    analysis_mode: str
    confidence: float = Field(ge=0, le=1)
    reasoning_summary: str
    citizen_response: str
    agent_trace: list[AgentStage]
    duplicate_candidates: list[DuplicateCandidate] = Field(default_factory=list)
    location_verified: bool | None = None
    location_display_name: str | None = None
    location_verification_message: str | None = None


class ComplaintBatchAnalysis(BaseModel):
    language: str
    language_code: str
    issue_count: int
    issues: list[ComplaintAnalysis]


class TicketCreateRequest(AnalyzeComplaintRequest):
    contact: str | None = Field(default=None, max_length=255)
    duplicate_of: str | None = Field(default=None, max_length=32)


class TicketStatusRequest(BaseModel):
    status: Literal["SUBMITTED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "ESCALATED"]
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


class StaffCitizenResponse(BaseModel):
    name: str
    email: str
    contact: str | None = None


class StaffTicketResponse(TicketResponse):
    citizen: StaffCitizenResponse | None = None


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
