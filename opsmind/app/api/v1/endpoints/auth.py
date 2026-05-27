from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import (
    GoogleAuthRequest, LoginRequest, RefreshRequest,
    RegisterRequest, TokenResponse, UserOut, VerifyRequest,
)
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
from app.api.v1.deps import get_current_user
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_svc(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    background: BackgroundTasks,
    svc: AuthService = Depends(_auth_svc),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await svc.register(req)
        tokens = await svc._issue_tokens(user)  # noqa: SLF001
        await db.commit()

        # Send verification code
        if req.email:
            code = await svc.send_verification_code(req.email, "register")
            # TODO: background.add_task(send_email_code, req.email, code)

        return tokens
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    svc: AuthService = Depends(_auth_svc),
    db: AsyncSession = Depends(get_db),
):
    try:
        tokens = await svc.login(req.identifier, req.password)
        await db.commit()
        return tokens
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    req: GoogleAuthRequest,
    svc: AuthService = Depends(_auth_svc),
    db: AsyncSession = Depends(get_db),
):
    try:
        tokens = await svc.google_auth(req.id_token)
        await db.commit()
        return tokens
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    req: RefreshRequest,
    svc: AuthService = Depends(_auth_svc),
    db: AsyncSession = Depends(get_db),
):
    try:
        tokens = await svc.refresh(req.refresh_token)
        await db.commit()
        return tokens
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/verify")
async def verify(
    req: VerifyRequest,
    svc: AuthService = Depends(_auth_svc),
    db: AsyncSession = Depends(get_db),
):
    ok = await svc.verify_code(req.target, req.code, req.purpose)
    if not ok:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    await db.commit()
    return {"verified": True}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user