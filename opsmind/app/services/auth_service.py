"""Authentication service: email/phone/username/Google OAuth."""
import hashlib
import random
import string
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token, create_refresh_token,
    decode_token, hash_password, verify_password,
)
from app.db.redis import cache
from app.models.models import AuthProvider, RefreshToken, User, VerificationCode
from app.schemas.schemas import RegisterRequest, TokenResponse

logger = get_logger("auth")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Registration ───────────────────────────────────────────────────────────

    async def register(self, req: RegisterRequest) -> User:
        if req.email:
            existing = await self.db.scalar(select(User).where(User.email == req.email))
            if existing:
                raise ValueError("Email already registered")
        if req.phone:
            existing = await self.db.scalar(select(User).where(User.phone == req.phone))
            if existing:
                raise ValueError("Phone already registered")
        if req.username:
            existing = await self.db.scalar(select(User).where(User.username == req.username))
            if existing:
                raise ValueError("Username already taken")

        user = User(
            email=req.email,
            phone=req.phone,
            username=req.username,
            full_name=req.full_name,
            auth_provider=req.auth_provider,
            hashed_password=hash_password(req.password) if req.password else None,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()
        logger.info("user_registered", user_id=str(user.id), provider=req.auth_provider)
        return user

    # ── Send verification code ─────────────────────────────────────────────────

    async def send_verification_code(self, target: str, purpose: str) -> str:
        """
        Генерирует 6-значный код, сохраняет в БД.
        Если target — email → отправляет письмо через Gmail.
        Если target — телефон → логирует (SMS шлюз подключается отдельно).
        """
        code = "".join(random.choices(string.digits, k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        vc = VerificationCode(
            target=target,
            code=code,
            purpose=purpose,
            expires_at=expires_at,
        )
        self.db.add(vc)
        await self.db.flush()

        # Email — отправляем через Gmail
        if "@" in target:
            from app.services.notification_service import send_verification_email
            await send_verification_email(target, code)

        # Телефон — логируем код (для дебага), SMS шлюз подключишь позже
        else:
            logger.info(
                "verification_code_generated_for_phone",
                phone=target,
                code=code,  # в продакшене убери это!
                purpose=purpose,
            )

        return code

    async def verify_code(self, target: str, code: str, purpose: str) -> bool:
        vc = await self.db.scalar(
            select(VerificationCode).where(
                VerificationCode.target == target,
                VerificationCode.code == code,
                VerificationCode.purpose == purpose,
                VerificationCode.used == False,  # noqa: E712
                VerificationCode.expires_at > datetime.now(timezone.utc),
            )
        )
        if not vc:
            return False
        vc.used = True
        user = await self._find_user(target)
        if user:
            user.is_verified = True
        return True

    # ── Login ──────────────────────────────────────────────────────────────────

    async def login(self, identifier: str, password: str) -> TokenResponse:
        user = await self._find_user(identifier)
        if not user:
            raise ValueError("Invalid credentials")
        if not user.hashed_password or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Account is disabled")
        return await self._issue_tokens(user)

    # ── Google OAuth ───────────────────────────────────────────────────────────

    async def google_auth(self, id_token: str) -> TokenResponse:
        profile = await self._verify_google_token(id_token)
        google_id = profile["sub"]

        user = await self.db.scalar(select(User).where(User.google_id == google_id))
        if not user and profile.get("email"):
            user = await self.db.scalar(select(User).where(User.email == profile["email"]))

        if not user:
            user = User(
                email=profile.get("email"),
                full_name=profile.get("name"),
                avatar_url=profile.get("picture"),
                google_id=google_id,
                auth_provider=AuthProvider.GOOGLE,
                is_verified=True,
            )
            self.db.add(user)
            await self.db.flush()
            logger.info("google_user_created", user_id=str(user.id))
        else:
            user.google_id = google_id
            user.avatar_url = profile.get("picture")

        return await self._issue_tokens(user)

    # ── Refresh ────────────────────────────────────────────────────────────────

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        token_hash = _hash_token(refresh_token)
        rt = await self.db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,  # noqa: E712
            )
        )
        if not rt or rt.expires_at < datetime.now(timezone.utc):
            raise ValueError("Refresh token expired or invalid")

        user = await self.db.get(User, uuid.UUID(payload["sub"]))
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        rt.revoked = True
        return await self._issue_tokens(user)

    # ── Helpers ────────────────────────────────────────────────────────────────

    async def _find_user(self, identifier: str) -> User | None:
        for field in [User.email, User.phone, User.username]:
            user = await self.db.scalar(select(User).where(field == identifier))
            if user:
                return user
        return None

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))

        rt = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            ),
        )
        self.db.add(rt)
        user.last_login_at = datetime.now(timezone.utc)

        try:
            await cache.set(
                f"user:{user.id}",
                {"id": str(user.id), "is_active": user.is_active},
                ttl=3600,
            )
        except Exception:
            pass  # Redis недоступен — продолжаем без кэша

        return TokenResponse(access_token=access, refresh_token=refresh)

    @staticmethod
    async def _verify_google_token(id_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
            )
        if r.status_code != 200:
            raise ValueError("Invalid Google token")
        data = r.json()
        if data.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise ValueError("Token audience mismatch")
        return data