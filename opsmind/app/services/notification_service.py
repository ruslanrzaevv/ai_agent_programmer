"""Notification service: SMS (Twilio) + Email (SendGrid)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client as TwilioClient

from app.core.config import settings
from app.core.logging import get_logger
from app.models.models import Incident, Notification, NotificationChannel, Project, User

logger = get_logger("notifications")


def _twilio() -> TwilioClient:
    return TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def _sendgrid() -> SendGridAPIClient:
    return SendGridAPIClient(settings.SENDGRID_API_KEY)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Main entry point ───────────────────────────────────────────────────────

    async def notify_incident(
        self,
        incident: Incident,
        project: Project,
        users: list[User],
    ) -> None:
        for user in users:
            channels = project.notify_channels or []
            for channel in channels:
                if channel == NotificationChannel.SMS and user.phone:
                    await self._send_sms(user, incident, project)
                elif channel == NotificationChannel.EMAIL and user.email:
                    await self._send_email(user, incident, project)

    # ── SMS ────────────────────────────────────────────────────────────────────

    async def _send_sms(
        self, user: User, incident: Incident, project: Project
    ) -> None:
        body = (
            f"🚨 OpsMind Alert [{incident.severity.upper()}]\n"
            f"Project: {project.name}\n"
            f"{incident.title}\n"
            f"Visit {settings.FRONTEND_URL}/incidents/{incident.id}"
        )
        notif = Notification(
            incident_id=incident.id,
            user_id=user.id,
            channel=NotificationChannel.SMS,
            recipient=user.phone,  # type: ignore[arg-type]
            body=body,
        )
        try:
            _twilio().messages.create(
                body=body,
                from_=settings.TWILIO_FROM_PHONE,
                to=user.phone,  # type: ignore[arg-type]
            )
            notif.sent = True
            notif.sent_at = datetime.now(timezone.utc)
            logger.info("sms_sent", user_id=str(user.id), incident_id=str(incident.id))
        except Exception as e:
            notif.error = str(e)
            logger.error("sms_failed", error=str(e), user_id=str(user.id))
        finally:
            self.db.add(notif)
            await self.db.flush()

    # ── Email ──────────────────────────────────────────────────────────────────

    async def _send_email(
        self, user: User, incident: Incident, project: Project
    ) -> None:
        severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
            incident.severity, "⚪"
        )
        subject = f"{severity_emoji} [{incident.severity.upper()}] {incident.title} — {project.name}"

        # Pick explanation based on user mode
        from app.models.models import ExplainMode
        explanation_map = {
            ExplainMode.JUNIOR: incident.ai_explanation_junior,
            ExplainMode.SENIOR: incident.ai_explanation_senior,
            ExplainMode.CEO: incident.ai_explanation_ceo,
        }
        explanation = explanation_map.get(user.explain_mode, incident.ai_explanation_senior) or "Analysis pending..."

        html_body = f"""
<html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: #1a1a2e; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
    <h1 style="margin: 0; font-size: 20px;">⚡ OpsMind Incident Alert</h1>
  </div>
  <div style="background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6;">
    <table style="width: 100%; border-collapse: collapse;">
      <tr><td style="padding: 8px; font-weight: bold; width: 140px;">Project</td><td style="padding: 8px;">{project.name} ({project.environment})</td></tr>
      <tr style="background: white;"><td style="padding: 8px; font-weight: bold;">Severity</td><td style="padding: 8px;">{severity_emoji} {incident.severity.upper()}</td></tr>
      <tr><td style="padding: 8px; font-weight: bold;">Status</td><td style="padding: 8px;">{incident.status.upper()}</td></tr>
      <tr style="background: white;"><td style="padding: 8px; font-weight: bold;">Error Count</td><td style="padding: 8px;">{incident.error_count}</td></tr>
      <tr><td style="padding: 8px; font-weight: bold;">Started</td><td style="padding: 8px;">{incident.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
    </table>

    <h2 style="color: #333; margin-top: 20px;">What happened</h2>
    <p style="color: #555; line-height: 1.6;">{explanation}</p>

    {'<h2 style="color: #333;">Suggested fix</h2><p style="color: #555;">' + incident.ai_fix_suggestion + '</p>' if incident.ai_fix_suggestion else ''}

    <div style="text-align: center; margin-top: 30px;">
      <a href="{settings.FRONTEND_URL}/incidents/{incident.id}"
         style="background: #4361ee; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">
        View Incident in OpsMind
      </a>
    </div>
  </div>
  <div style="background: #6c757d; color: white; padding: 10px 20px; font-size: 12px; border-radius: 0 0 8px 8px;">
    OpsMind · AI-powered incident monitoring · <a href="{settings.FRONTEND_URL}/settings" style="color: #adb5bd;">Unsubscribe</a>
  </div>
</body></html>
"""
        mail = Mail(
            from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=user.email,
            subject=subject,
            html_content=html_body,
        )
        notif = Notification(
            incident_id=incident.id,
            user_id=user.id,
            channel=NotificationChannel.EMAIL,
            recipient=user.email,  # type: ignore[arg-type]
            subject=subject,
            body=html_body,
        )
        try:
            _sendgrid().send(mail)
            notif.sent = True
            notif.sent_at = datetime.now(timezone.utc)
            logger.info("email_sent", user_id=str(user.id), incident_id=str(incident.id))
        except Exception as e:
            notif.error = str(e)
            logger.error("email_failed", error=str(e), user_id=str(user.id))
        finally:
            self.db.add(notif)
            await self.db.flush()