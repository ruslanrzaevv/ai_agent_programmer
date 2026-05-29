from __future__ import annotations

import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.models import Incident, Notification, NotificationChannel, Project, User

logger = get_logger("notifications")


# ── Gmail SMTP ─────────────────────────────────────────────────────────────────

def _send_gmail(to_email: str, subject: str, html_body: str) -> None:
    """Отправить письмо через Gmail SMTP (порт 465, SSL)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.GMAIL_USER
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(settings.GMAIL_USER, settings.GMAIL_PASSWORD)
        server.sendmail(settings.GMAIL_USER, to_email, msg.as_string())


# ── Notification Service ───────────────────────────────────────────────────────

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

    # ── SMS (лог — подключи Eskiz/другой шлюз позже) ──────────────────────────

    async def _send_sms(
        self, user: User, incident: Incident, project: Project
    ) -> None:
        body = (
            f"OpsMind [{incident.severity.upper()}] "
            f"Project: {project.name} — {incident.title[:80]}"
        )
        notif = Notification(
            incident_id=incident.id,
            user_id=user.id,
            channel=NotificationChannel.SMS,
            recipient=user.phone,  # type: ignore[arg-type]
            body=body,
            sent=False,
            error="SMS gateway not configured",
        )
        self.db.add(notif)
        await self.db.flush()
        logger.warning("sms_not_configured", user_id=str(user.id), phone=user.phone)

    # ── Email через Gmail SMTP ─────────────────────────────────────────────────

    async def _send_email(
        self, user: User, incident: Incident, project: Project
    ) -> None:
        if not settings.GMAIL_USER or not settings.GMAIL_PASSWORD:
            logger.warning("gmail_not_configured_skipping_email")
            return

        severity_emoji = {
            "critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"
        }.get(incident.severity, "⚪")

        subject = (
            f"{severity_emoji} [{incident.severity.upper()}] "
            f"{incident.title} — {project.name}"
        )

        from app.models.models import ExplainMode
        explanation_map = {
            ExplainMode.JUNIOR: incident.ai_explanation_junior,
            ExplainMode.SENIOR: incident.ai_explanation_senior,
            ExplainMode.CEO: incident.ai_explanation_ceo,
        }
        explanation = (
            explanation_map.get(user.explain_mode, incident.ai_explanation_senior)
            or "Analysis pending..."
        )

        html_body = f"""
<html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: #1a1a2e; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
    <h1 style="margin: 0; font-size: 20px;">⚡ OpsMind Incident Alert</h1>
  </div>
  <div style="background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6;">
    <table style="width: 100%; border-collapse: collapse;">
      <tr>
        <td style="padding: 8px; font-weight: bold; width: 140px;">Project</td>
        <td style="padding: 8px;">{project.name} ({project.environment})</td>
      </tr>
      <tr style="background: white;">
        <td style="padding: 8px; font-weight: bold;">Severity</td>
        <td style="padding: 8px;">{severity_emoji} {incident.severity.upper()}</td>
      </tr>
      <tr>
        <td style="padding: 8px; font-weight: bold;">Status</td>
        <td style="padding: 8px;">{incident.status.upper()}</td>
      </tr>
      <tr style="background: white;">
        <td style="padding: 8px; font-weight: bold;">Errors</td>
        <td style="padding: 8px;">{incident.error_count}</td>
      </tr>
      <tr>
        <td style="padding: 8px; font-weight: bold;">Started</td>
        <td style="padding: 8px;">{incident.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
      </tr>
    </table>

    <h2 style="color: #333; margin-top: 20px;">What happened</h2>
    <p style="color: #555; line-height: 1.6;">{explanation}</p>

    {'<h2 style="color: #333;">Suggested fix</h2><p style="color: #555;">' + (incident.ai_fix_suggestion or '') + '</p>' if incident.ai_fix_suggestion else ''}

    <div style="text-align: center; margin-top: 30px;">
      <a href="{settings.FRONTEND_URL}/incidents/{incident.id}"
         style="background: #4361ee; color: white; padding: 12px 30px;
                border-radius: 6px; text-decoration: none; font-weight: bold;">
        View Incident in OpsMind
      </a>
    </div>
  </div>
  <div style="background: #6c757d; color: white; padding: 10px 20px;
              font-size: 12px; border-radius: 0 0 8px 8px;">
    OpsMind · AI-powered incident monitoring
  </div>
</body></html>
"""
        notif = Notification(
            incident_id=incident.id,
            user_id=user.id,
            channel=NotificationChannel.EMAIL,
            recipient=user.email,  # type: ignore[arg-type]
            subject=subject,
            body=html_body,
        )
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _send_gmail, user.email, subject, html_body)
            notif.sent = True
            notif.sent_at = datetime.now(timezone.utc)
            logger.info("email_sent_gmail", user_id=str(user.id), to=user.email)
        except Exception as e:
            notif.error = str(e)
            logger.error("email_failed_gmail", error=str(e), user_id=str(user.id))
        finally:
            self.db.add(notif)
            await self.db.flush()


# ── Утилита для отправки кода верификации ──────────────────────────────────────

async def send_verification_email(to_email: str, code: str) -> bool:
    """Отправить код верификации на email через Gmail SMTP."""
    if not settings.GMAIL_USER or not settings.GMAIL_PASSWORD:
        logger.warning("gmail_not_configured_skipping_verification_email")
        return False

    subject = "OpsMind — код подтверждения"
    html_body = f"""
<html><body style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
  <div style="background: #1a1a2e; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
    <h2 style="margin: 0;">⚡ OpsMind</h2>
  </div>
  <div style="background: #f8f9fa; padding: 30px; border: 1px solid #dee2e6;
              border-radius: 0 0 8px 8px; text-align: center;">
    <p style="color: #555; font-size: 16px;">Ваш код подтверждения:</p>
    <div style="font-size: 42px; font-weight: bold; letter-spacing: 10px;
                color: #4361ee; padding: 20px; background: #fff;
                border-radius: 8px; margin: 20px 0; border: 2px solid #e0e0e0;">
      {code}
    </div>
    <p style="color: #888; font-size: 13px;">
      Код действителен <strong>10 минут</strong>.<br>
      Если вы не запрашивали код — проигнорируйте это письмо.
    </p>
  </div>
</body></html>
"""
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_gmail, to_email, subject, html_body)
        logger.info("verification_email_sent", to=to_email)
        return True
    except Exception as e:
        logger.error("verification_email_failed", error=str(e), to=to_email)
        return False