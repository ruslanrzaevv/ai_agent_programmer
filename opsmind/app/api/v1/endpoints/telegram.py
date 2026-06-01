"""
Telegram Bot webhook endpoint + API для привязки аккаунта.

Endpoints:
  POST /telegram/webhook          ← Telegram шлёт сюда все обновления
  POST /telegram/connect          ← Генерирует ссылку для привязки (авторизован)
  DELETE /telegram/disconnect     ← Отвязать Telegram (авторизован)
  GET  /telegram/status           ← Статус привязки (авторизован)
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.models import User
from app.services.telegram_service import (
    generate_link_token,
    get_telegram_connect_url,
    handle_callback,
    handle_start,
    handle_stop,
    notify_incident_telegram,
)

router = APIRouter(prefix="/telegram", tags=["telegram"])
logger = get_logger("telegram.endpoint")


# ─── Webhook от Telegram ──────────────────────────────────────────────────────

@router.post("/webhook")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Telegram шлёт все апдейты сюда.
    Зарегистрировать webhook:
      POST https://api.telegram.org/bot{TOKEN}/setWebhook
      {"url": "https://yourdomain.com/api/v1/telegram/webhook"}
    """
    # Проверяем секретный токен если настроен
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if settings.TELEGRAM_BOT_TOKEN and secret and secret != settings.TELEGRAM_BOT_TOKEN[:20]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Invalid webhook token")

    try:
        update = await request.json()
    except Exception:
        return {"ok": True}

    # ── Обычное сообщение (команды /start, /stop) ─────────────────────────────
    message = update.get("message")
    if message:
        chat_id  = message["chat"]["id"]
        username = message["from"].get("username")
        fname    = message["from"].get("first_name", "")
        text     = message.get("text", "")

        if text.startswith("/start"):
            # /start TOKEN  или просто /start
            parts = text.split(maxsplit=1)
            link_token = parts[1].strip() if len(parts) > 1 else None
            await handle_start(db, chat_id, username, link_token, fname)

        elif text.startswith("/stop"):
            await handle_stop(db, chat_id)

        elif text.startswith("/status"):
            from sqlalchemy import select
            user = await db.scalar(
                select(User).where(User.telegram_chat_id == chat_id)
            )
            from app.services.telegram_service import send_message
            if user:
                await send_message(chat_id, (
                    f"✅ Подключён к аккаунту: "
                    f"<b>{user.email or user.username or user.phone}</b>"
                ))
            else:
                await send_message(chat_id,
                    "❌ Этот чат не привязан ни к одному аккаунту OpsMind.")

    # ── Callback от кнопок (Acknowledge) ──────────────────────────────────────
    callback = update.get("callback_query")
    if callback:
        chat_id     = callback["from"]["id"]
        callback_id = callback["id"]
        data        = callback.get("data", "")
        await handle_callback(db, chat_id, callback_id, data)

    return {"ok": True}


# ─── Генерация ссылки для привязки ────────────────────────────────────────────

@router.post("/connect")
async def connect_telegram(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Генерирует одноразовую ссылку для привязки Telegram.
    Фронт показывает её как кнопку "Открыть в Telegram".
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot not configured",
        )

    # Генерируем новый токен (сбрасываем старый если был)
    token = generate_link_token()
    current_user.telegram_link_token = token
    await db.commit()

    connect_url = get_telegram_connect_url(token)
    logger.info("telegram_link_generated", user_id=str(current_user.id))

    return {
        "connect_url": connect_url,
        "bot_username": settings.TELEGRAM_BOT_USERNAME,
        "already_connected": current_user.telegram_chat_id is not None,
        "telegram_username": current_user.telegram_username,
    }


# ─── Статус привязки ──────────────────────────────────────────────────────────

@router.get("/status")
async def telegram_status(current_user: User = Depends(get_current_user)):
    """Проверить подключён ли Telegram к аккаунту."""
    return {
        "connected": current_user.telegram_chat_id is not None,
        "telegram_username": current_user.telegram_username,
        "telegram_chat_id": current_user.telegram_chat_id,
        "bot_username": settings.TELEGRAM_BOT_USERNAME,
    }


# ─── Отвязать Telegram ────────────────────────────────────────────────────────

@router.delete("/disconnect")
async def disconnect_telegram(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отвязать Telegram от аккаунта."""
    if not current_user.telegram_chat_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Telegram not connected")

    # Уведомляем пользователя в ТГ перед отключением
    from app.services.telegram_service import send_message
    await send_message(
        current_user.telegram_chat_id,
        "🔕 Ваш Telegram был отвязан от OpsMind через настройки сайта."
    )

    current_user.telegram_chat_id = None
    current_user.telegram_username = None
    current_user.telegram_link_token = None
    await db.commit()

    return {"disconnected": True}