from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("auth_provider", sa.Enum("email", "phone", "google", "username", name="authprovider"), nullable=False),
        sa.Column("google_id", sa.String(128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("totp_secret", sa.String(64), nullable=True),
        sa.Column("explain_mode", sa.Enum("junior", "senior", "ceo", name="explainmode"), nullable=False, server_default="senior"),
        sa.Column("notify_channels", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("google_id"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_phone", "users", ["phone"])
    op.create_index("ix_users_username", "users", ["username"])

    # ── refresh_tokens ─────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    # ── verification_codes ─────────────────────────────────────────────────────
    op.create_table(
        "verification_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("code", sa.String(8), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_codes_target", "verification_codes", ["target"])

    # ── projects ───────────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("environment", sa.String(32), nullable=False, server_default="production"),
        sa.Column("docker_engine_url", sa.String(500), nullable=False),
        sa.Column("docker_tls_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("docker_tls_cert", sa.Text(), nullable=True),
        sa.Column("docker_tls_key", sa.Text(), nullable=True),
        sa.Column("docker_tls_ca", sa.Text(), nullable=True),
        sa.Column("docker_container_filter", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("gitlab_url", sa.String(500), nullable=False),
        sa.Column("gitlab_token", sa.String(255), nullable=False),
        sa.Column("gitlab_project_id", sa.String(64), nullable=False),
        sa.Column("gitlab_webhook_secret", sa.String(128), nullable=True),
        sa.Column("gitlab_branches", sa.JSON(), nullable=False, server_default='["main","master"]'),
        sa.Column("error_threshold_per_minute", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("log_level_filter", sa.JSON(), nullable=False, server_default='["error","critical"]'),
        sa.Column("notify_channels", sa.JSON(), nullable=False, server_default='["email"]'),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("monitoring_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── log_entries ────────────────────────────────────────────────────────────
    op.create_table(
        "log_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.Enum("docker", "gitlab", "system", name="logsource"), nullable=False),
        sa.Column("level", sa.Enum("debug", "info", "warning", "error", "critical", name="loglevel"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("container_name", sa.String(128), nullable=True),
        sa.Column("service_name", sa.String(128), nullable=True),
        sa.Column("raw", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_log_entries_project_id", "log_entries", ["project_id"])
    op.create_index("ix_log_entries_level", "log_entries", ["level"])
    op.create_index("ix_log_entries_timestamp", "log_entries", ["timestamp"])

    # ── incidents ──────────────────────────────────────────────────────────────
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("severity", sa.Enum("critical", "high", "medium", "low", name="incidentseverity"), nullable=False),
        sa.Column("status", sa.Enum("open", "acknowledged", "resolving", "resolved", "ignored", name="incidentstatus"), nullable=False, server_default="open"),
        sa.Column("ai_explanation_junior", sa.Text(), nullable=True),
        sa.Column("ai_explanation_senior", sa.Text(), nullable=True),
        sa.Column("ai_explanation_ceo", sa.Text(), nullable=True),
        sa.Column("ai_fix_suggestion", sa.Text(), nullable=True),
        sa.Column("ai_auto_fix_script", sa.Text(), nullable=True),
        sa.Column("ai_fix_applied", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ai_fix_applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timeline", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("affected_containers", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("estimated_revenue_loss", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["acknowledged_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incidents_project_id", "incidents", ["project_id"])
    op.create_index("ix_incidents_severity", "incidents", ["severity"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_started_at", "incidents", ["started_at"])

    # ── incident_logs ──────────────────────────────────────────────────────────
    op.create_table(
        "incident_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("log_entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["log_entry_id"], ["log_entries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("incident_id", "log_entry_id"),
    )

    # ── notifications ──────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.Enum("sms", "email", "push", name="notificationchannel"), nullable=False),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(512), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("incident_logs")
    op.drop_table("incidents")
    op.drop_table("log_entries")
    op.drop_table("projects")
    op.drop_table("verification_codes")
    op.drop_table("refresh_tokens")
    op.drop_table("users")

    for enum in ["authprovider", "explainmode", "incidentseverity", "incidentstatus",
                 "loglevel", "logsource", "notificationchannel"]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")