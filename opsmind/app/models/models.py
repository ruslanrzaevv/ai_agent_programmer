import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint, JSON,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()




class AuthProvider(str, PyEnum):
    EMAIL = "email"
    PHONE = "phone"
    GOOGLE = "google"
    USERNAME = "username"


class IncidentSeverity(str, PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, PyEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class ExplainMode(str, PyEnum):
    JUNIOR = "junior"
    SENIOR = "senior"
    CEO = "ceo"


class NotificationChannel(str, PyEnum):
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"


class LogLevel(str, PyEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogSource(str, PyEnum):
    DOCKER = "docker"
    GITLAB = "gitlab"
    SYSTEM = "system"




class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[AuthProvider] = mapped_column(Enum(AuthProvider), default=AuthProvider.EMAIL)
    google_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    explain_mode: Mapped[ExplainMode] = mapped_column(Enum(ExplainMode), default=ExplainMode.SENIOR)
    notify_channels: Mapped[list] = mapped_column(JSON, default=list)  # ["sms", "email"]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="owner", lazy="selectin")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    user: Mapped[User] = relationship("User", back_populates="refresh_tokens")


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    target: Mapped[str] = mapped_column(String(255), index=True)  # email or phone
    code: Mapped[str] = mapped_column(String(8))
    purpose: Mapped[str] = mapped_column(String(32))  # register | login | reset
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)




class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    environment: Mapped[str] = mapped_column(String(32), default="production")  # production|staging|dev


    docker_engine_url: Mapped[str] = mapped_column(String(500))
    docker_tls_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    docker_tls_cert: Mapped[str | None] = mapped_column(Text, nullable=True)
    docker_tls_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    docker_tls_ca: Mapped[str | None] = mapped_column(Text, nullable=True)
    docker_container_filter: Mapped[dict] = mapped_column(JSONB, default=dict)  # {"name": "api-*"}


    gitlab_url: Mapped[str] = mapped_column(String(500), default="https://gitlab.com")
    gitlab_token: Mapped[str] = mapped_column(String(255))
    gitlab_project_id: Mapped[str] = mapped_column(String(64))
    gitlab_webhook_secret: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gitlab_branches: Mapped[list] = mapped_column(JSON, default=lambda: ["main", "master"])


    error_threshold_per_minute: Mapped[int] = mapped_column(Integer, default=5)
    log_level_filter: Mapped[list] = mapped_column(JSON, default=lambda: ["error", "critical"])
    notify_channels: Mapped[list] = mapped_column(JSON, default=lambda: ["email", "sms"])
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")


    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    monitoring_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    owner: Mapped[User] = relationship("User", back_populates="projects")
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="project")
    log_entries: Mapped[list["LogEntry"]] = relationship("LogEntry", back_populates="project")




class LogEntry(Base):
    __tablename__ = "log_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    source: Mapped[LogSource] = mapped_column(Enum(LogSource))
    level: Mapped[LogLevel] = mapped_column(Enum(LogLevel), index=True)
    message: Mapped[str] = mapped_column(Text)
    container_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    service_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    project: Mapped[Project] = relationship("Project", back_populates="log_entries")
    incident_logs: Mapped[list["IncidentLog"]] = relationship("IncidentLog", back_populates="log_entry")




class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(512))
    severity: Mapped[IncidentSeverity] = mapped_column(Enum(IncidentSeverity), index=True)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.OPEN, index=True)

    # AI analysis
    ai_explanation_junior: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_explanation_senior: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_explanation_ceo: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_fix_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_auto_fix_script: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_fix_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_fix_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    timeline: Mapped[list] = mapped_column(JSONB, default=list)
    # [{"minute": 0, "ts": "...", "event": "First error", "cpu": 12.3, "errors": 3, "requests": 100}]

    error_count: Mapped[int] = mapped_column(Integer, default=0)
    affected_containers: Mapped[list] = mapped_column(JSON, default=list)
    estimated_revenue_loss: Mapped[float | None] = mapped_column(Float, nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    project: Mapped[Project] = relationship("Project", back_populates="incidents")
    logs: Mapped[list["IncidentLog"]] = relationship("IncidentLog", back_populates="incident")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="incident")


class IncidentLog(Base):
    """M2M: which log entries belong to an incident."""
    __tablename__ = "incident_logs"
    __table_args__ = (UniqueConstraint("incident_id", "log_entry_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"))
    log_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("log_entries.id", ondelete="CASCADE"))

    incident: Mapped[Incident] = relationship("Incident", back_populates="logs")
    log_entry: Mapped[LogEntry] = relationship("LogEntry", back_populates="incident_logs")




class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel))
    recipient: Mapped[str] = mapped_column(String(255))  # email or phone
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    incident: Mapped[Incident] = relationship("Incident", back_populates="notifications")