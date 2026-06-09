from __future__ import annotations

import secrets
import httpx
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.models import Incident, Notification, NotificationChannel, Project, User

logger = get_logger("telegram")

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


# ─── Низкоуровневые вызовы Telegram API ───────────────────────────────────────

async def _tg_call(method: str, payload: dict) -> dict:
    """Вызвать Telegram Bot API."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("telegram_bot_token_not_configured")
        return {}

    url = TELEGRAM_API.format(token=settings.TELEGRAM_BOT_TOKEN, method=method)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()
        if not data.get("ok"):
            logger.error("telegram_api_error", method=method, error=data.get("description"))
        return data


async def send_message(chat_id: int, text: str, parse_mode: str = "HTML",
                        reply_markup: dict | None = None) -> bool:
    """Отправить сообщение пользователю."""
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    result = await _tg_call("sendMessage", payload)
    return result.get("ok", False)


# ─── Генерация ссылки для привязки ────────────────────────────────────────────

def generate_link_token() -> str:
    """Сгенерировать уникальный токен для привязки Telegram."""
    return secrets.token_urlsafe(32)


def get_telegram_connect_url(link_token: str) -> str:
    """Вернуть ссылку на бота с токеном привязки."""
    if not settings.TELEGRAM_BOT_USERNAME:
        return ""
    return f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={link_token}"


# ─── Привязка пользователя (при /start) ──────────────────────────────────────

async def handle_start(db: AsyncSession, chat_id: int, username: str | None,
                        link_token: str | None, first_name: str = "") -> None:
    """
    Вызывается когда пользователь нажимает /start в боте.
    link_token — параметр из ссылки t.me/bot?start=TOKEN
    """
    if not link_token:
        # /start без токена — просто приветствие
        await send_message(chat_id, (
            f"👋 Привет{', ' + first_name if first_name else ''}!\n\n"
            "Я <b>OpsMind Bot</b> — уведомляю об инцидентах на ваших проектах.\n\n"
            "Чтобы подключить меня, зайдите в <b>OpsMind → Настройки → Telegram</b> "
            "и нажмите кнопку <b>Подключить Telegram</b>."
        ))
        return

    # Ищем пользователя по токену
    user = await db.scalar(
        select(User).where(User.telegram_link_token == link_token)
    )

    if not user:
        await send_message(chat_id, (
            "❌ Ссылка недействительна или устарела.\n\n"
            "Сгенерируйте новую ссылку в настройках OpsMind."
        ))
        return

    # Проверяем — вдруг этот chat_id уже привязан к другому аккаунту
    existing = await db.scalar(
        select(User).where(User.telegram_chat_id == chat_id)
    )
    if existing and existing.id != user.id:
        existing.telegram_chat_id = None
        existing.telegram_username = None

    # Привязываем
    user.telegram_chat_id = chat_id
    user.telegram_username = username
    user.telegram_link_token = None  # одноразовый токен — сбрасываем
    await db.commit()

    logger.info("telegram_linked", user_id=str(user.id), chat_id=chat_id)

    await send_message(chat_id, (
        f"✅ <b>Telegram успешно подключён!</b>\n\n"
        f"Аккаунт: <b>{user.email or user.username or user.phone}</b>\n\n"
        "Теперь вы будете получать уведомления об инцидентах прямо сюда.\n\n"
        "🔕 Чтобы отключить уведомления — напишите /stop"
    ))


async def handle_stop(db: AsyncSession, chat_id: int) -> None:
    """Отвязать Telegram от аккаунта по команде /stop."""
    user = await db.scalar(
        select(User).where(User.telegram_chat_id == chat_id)
    )
    if not user:
        await send_message(chat_id, "Ваш аккаунт и так не привязан.")
        return

    user.telegram_chat_id = None
    user.telegram_username = None
    await db.commit()

    await send_message(chat_id, (
        "🔕 Уведомления отключены.\n\n"
        "Вы можете снова подключить Telegram в настройках OpsMind."
    ))


# ─── Уведомление об инциденте ─────────────────────────────────────────────────

async def notify_incident_telegram(
    db: AsyncSession,
    user: User,
    incident: Incident,
    project: Project,
) -> None:
    """Отправить уведомление об инциденте в Telegram."""
    if not user.telegram_chat_id:
        return
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    # Эмодзи по severity
    emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
        incident.severity, "⚪"
    )

    # Объяснение в зависимости от режима пользователя
    from app.models.models import ExplainMode
    explanation_map = {
        ExplainMode.JUNIOR: incident.ai_explanation_junior,
        ExplainMode.SENIOR: incident.ai_explanation_senior,
        ExplainMode.CEO:    incident.ai_explanation_ceo,
    }
    explanation = explanation_map.get(user.explain_mode, incident.ai_explanation_senior)

    # Формируем сообщение
    text = (
        f"{emoji} <b>Инцидент — {incident.severity.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Проект:</b> {project.name} ({project.environment})\n"
        f"⚡ <b>Ошибок:</b> {incident.error_count}\n"
        f"🕐 <b>Время:</b> {incident.started_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>{incident.title}</b>\n"
    )

    if explanation:
        # Обрезаем до 300 символов чтобы сообщение не было слишком длинным
        short = explanation[:300] + ("..." if len(explanation) > 300 else "")
        text += f"\n💬 {short}\n"

    if incident.ai_fix_suggestion:
        short_fix = incident.ai_fix_suggestion[:200] + ("..." if len(incident.ai_fix_suggestion) > 200 else "")
        text += f"\n🔧 <i>{short_fix}</i>\n"

    # Кнопка "Открыть в OpsMind"
    reply_markup = {
        "inline_keyboard": [[
            {
                "text": "🔍 Открыть инцидент",
                "url": f"{settings.FRONTEND_URL}/incidents/{incident.id}",
            },
            {
                "text": "✓ Acknowledge",
                "callback_data": f"ack:{incident.id}",
            },
        ]]
    }

    ok = await send_message(user.telegram_chat_id, text, reply_markup=reply_markup)

    # Записываем в таблицу notifications
    notif = Notification(
        incident_id=incident.id,
        user_id=user.id,
        channel=NotificationChannel.TELEGRAM,
        recipient=str(user.telegram_chat_id),
        body=text,
        sent=ok,
        sent_at=datetime.now(timezone.utc) if ok else None,
        error=None if ok else "Failed to send",
    )
    db.add(notif)
    await db.flush()

    if ok:
        logger.info("telegram_notification_sent",
                    user_id=str(user.id), incident_id=str(incident.id))
    else:
        logger.error("telegram_notification_failed",
                     user_id=str(user.id), incident_id=str(incident.id))


# ─── Обработка callback кнопок (Acknowledge прямо из ТГ) ──────────────────────

async def handle_callback(db: AsyncSession, chat_id: int,
                           callback_id: str, data: str) -> None:
    """Обработать нажатие кнопки в сообщении."""
    # Подтверждаем callback чтобы убрать loading
    await _tg_call("answerCallbackQuery", {"callback_query_id": callback_id})

    if data.startswith("ack:"):
        incident_id = data.split(":", 1)[1]
        from app.models.models import Incident as IncidentModel, IncidentStatus
        incident = await db.scalar(
            select(IncidentModel).where(IncidentModel.id == incident_id)
        )
        if incident and incident.status == IncidentStatus.OPEN:
            incident.status = IncidentStatus.ACKNOWLEDGED
            incident.acknowledged_at = datetime.now(timezone.utc)
            await db.commit()
            await send_message(chat_id, f"✅ Инцидент <b>{incident.title[:80]}</b> подтверждён.")
        else:
            await send_message(chat_id, "Инцидент уже был подтверждён или не найден.")