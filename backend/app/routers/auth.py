import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token,
)
from app.middleware.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserOut, LoginResponse, RefreshRequest

router = APIRouter()


def _user_out(u: User) -> UserOut:
    return UserOut(id=str(u.id), email=u.email, full_name=u.full_name,
                   role=u.role, is_active=u.is_active)


@router.post("/auth/login", response_model=LoginResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password")
    return LoginResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id)),
        user=_user_out(user),
    )


@router.post("/auth/refresh", response_model=LoginResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return LoginResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id)),
        user=_user_out(user),
    )


@router.get("/auth/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.post("/auth/users", response_model=UserOut, status_code=201)
async def create_user(payload: UserCreate,
                      _: User = Depends(require_role(UserRole.admin)),
                      db: AsyncSession = Depends(get_db)):
    """Admin-only: provision a new author/editor/admin."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email, hashed_password=hash_password(payload.password),
                full_name=payload.full_name, role=payload.role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _user_out(user)
