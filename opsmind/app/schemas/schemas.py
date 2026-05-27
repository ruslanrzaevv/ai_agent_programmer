"""Pydantic v2 schemas — request/response validation."""
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field, field_validator
import phonenumbers

from app.models.models import (
    AuthProvider, ExplainMode, IncidentSeverity,
    IncidentStatus, LogLevel, LogSource, NotificationChannel,
)


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    username: str | None = Field(None, min_length=3, max_length=64)
    full_name: str | None = Field(None, max_length=255)
    password: str | None = Field(None, min_length=8)
    auth_provider: AuthProvider = AuthProvider.EMAIL

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            parsed = phonenumbers.parse(v)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException as exc:
            raise ValueError("Invalid phone number format") from exc


class LoginRequest(BaseModel):
    identifier: str  # email | phone | username
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyRequest(BaseModel):
    target: str
    code: str
    purpose: str


# ─── User ─────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str | None
    phone: str | None
    username: str | None
    full_name: str | None
    avatar_url: str | None
    auth_provider: AuthProvider
    is_active: bool
    is_verified: bool
    explain_mode: ExplainMode
    notify_channels: list[str]
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    username: str | None = Field(None, min_length=3, max_length=64)
    explain_mode: ExplainMode | None = None
    notify_channels: list[NotificationChannel] | None = None


# ─── Project ──────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(None, max_length=1000)
    environment: str = Field("production", pattern="^(production|staging|development)$")

    # Docker
    docker_engine_url: str = Field(..., examples=["tcp://host:2376", "unix:///var/run/docker.sock"])
    docker_tls_enabled: bool = False
    docker_tls_cert: str | None = None
    docker_tls_key: str | None = None
    docker_tls_ca: str | None = None
    docker_container_filter: dict[str, str] = Field(default_factory=dict, examples=[{"name": "api-*"}])

    # GitLab
    gitlab_url: str = Field("https://gitlab.com", examples=["https://gitlab.com", "https://gitlab.mycompany.com"])
    gitlab_token: str
    gitlab_project_id: str
    gitlab_webhook_secret: str | None = None
    gitlab_branches: list[str] = Field(default_factory=lambda: ["main", "master"])

    # Alerting
    error_threshold_per_minute: int = Field(5, ge=1, le=1000)
    log_level_filter: list[LogLevel] = Field(default_factory=lambda: [LogLevel.ERROR, LogLevel.CRITICAL])
    notify_channels: list[NotificationChannel] = Field(default_factory=lambda: [NotificationChannel.EMAIL])
    timezone: str = "UTC"


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    error_threshold_per_minute: int | None = Field(None, ge=1, le=1000)
    log_level_filter: list[LogLevel] | None = None
    notify_channels: list[NotificationChannel] | None = None
    monitoring_enabled: bool | None = None
    gitlab_token: str | None = None
    docker_tls_cert: str | None = None
    docker_tls_key: str | None = None


class ProjectOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    description: str | None
    environment: str
    docker_engine_url: str
    docker_tls_enabled: bool
    gitlab_url: str
    gitlab_project_id: str
    gitlab_branches: list[str]
    error_threshold_per_minute: int
    log_level_filter: list[str]
    notify_channels: list[str]
    timezone: str
    is_active: bool
    monitoring_enabled: bool
    created_at: datetime
    updated_at: datetime


# ─── Incident ─────────────────────────────────────────────────────────────────

class TimelinePoint(BaseModel):
    minute: int
    ts: datetime
    event: str | None = None
    cpu_percent: float | None = None
    memory_mb: float | None = None
    error_count: int = 0
    request_count: int = 0
    first_failing_endpoint: str | None = None
    containers: list[str] = []


class IncidentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    ai_explanation_junior: str | None
    ai_explanation_senior: str | None
    ai_explanation_ceo: str | None
    ai_fix_suggestion: str | None
    ai_auto_fix_script: str | None
    ai_fix_applied: bool
    timeline: list[dict[str, Any]]
    error_count: int
    affected_containers: list[str]
    estimated_revenue_loss: float | None
    started_at: datetime
    resolved_at: datetime | None
    acknowledged_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IncidentAcknowledge(BaseModel):
    pass


class IncidentResolve(BaseModel):
    resolution_note: str | None = None


class ApplyFixRequest(BaseModel):
    confirmed: bool = False


# ─── Logs ─────────────────────────────────────────────────────────────────────

class LogEntryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    source: LogSource
    level: LogLevel
    message: str
    container_name: str | None
    service_name: str | None
    raw: dict[str, Any]
    timestamp: datetime


class LogQueryParams(BaseModel):
    level: LogLevel | None = None
    source: LogSource | None = None
    container_name: str | None = None
    from_ts: datetime | None = None
    to_ts: datetime | None = None
    search: str | None = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


# ─── AI ───────────────────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    mode: ExplainMode = ExplainMode.SENIOR
    incident_id: uuid.UUID


class AskAIRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    incident_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None


class AIResponse(BaseModel):
    content: str
    mode: ExplainMode | None = None


# ─── WebSocket ────────────────────────────────────────────────────────────────

class WSMessage(BaseModel):
    type: str  # "log" | "incident" | "metric" | "ping"
    project_id: str | None = None
    data: dict[str, Any] = {}


# ─── Pagination ───────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    limit: int
    offset: int