from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import (
    GoogleAuthRequest, LoginRequest, RefreshRequest,
    RegisterRequest, TokenResponse, UserOut, VerifyRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_svc(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/register")
async def register(
    req: RegisterRequest,
    background: BackgroundTasks,
    svc: AuthService = Depends(_auth_svc),
):
    user = await svc.register(req)

    if req.email:
        background.add_task(
            svc.send_verification_code,
            req.email,
            "register"
        )

    return {
        "success": True,
        "target": req.email
    }
    
    
@router.post("/send-code")
async def send_code(
    target: str,
    purpose: str = "login",
    svc: AuthService = Depends(_auth_svc),
    db: AsyncSession = Depends(get_db),
):
    """
    Отправить код подтверждения вручную.
    target — email или номер телефона (+998...)
    purpose — register | login | reset
    """
    try:
        await svc.send_verification_code(target, purpose)
        await db.commit()
        return {"message": f"Код отправлен на {target}"}
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/verify", response_model=TokenResponse)
async def verify(
    req: VerifyRequest,
    svc: AuthService = Depends(_auth_svc),
    db: AsyncSession = Depends(get_db),
):
    ok = await svc.verify_code(
        req.target,
        req.code,
        req.purpose
    )

    if not ok:
        raise HTTPException(400, "Invalid code")

    user = await svc._find_user(req.target)

    user.is_verified = True

    tokens = await svc._issue_tokens(user)

    await db.commit()

    return tokens

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


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user