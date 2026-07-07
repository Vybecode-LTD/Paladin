import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.ratelimit import limiter
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token,
)
from app.middleware.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import (
    UserCreate, UserOut, UserUpdate, ChangePasswordRequest, LoginResponse, RefreshRequest,
)

router = APIRouter()

_INVALID_REFRESH = HTTPException(status_code=401, detail="Invalid refresh token")


def _user_out(u: User) -> UserOut:
    return UserOut(id=str(u.id), email=u.email, full_name=u.full_name,
                   role=u.role, is_active=u.is_active)


def _parse_uuid(value: str, error: HTTPException) -> uuid.UUID:
    """uuid.UUID() raises a bare ValueError on malformed input — turn that
    into the caller's intended HTTP error instead of an unhandled 500."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        raise error


@router.post("/auth/login", response_model=LoginResponse)
@limiter.limit(settings.auth_rate_limit)
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends(),
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
        raise _INVALID_REFRESH
    sub = payload.get("sub")
    if not sub:
        raise _INVALID_REFRESH
    result = await db.execute(select(User).where(User.id == _parse_uuid(sub, _INVALID_REFRESH)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise _INVALID_REFRESH
    return LoginResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id)),
        user=_user_out(user),
    )


@router.get("/auth/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.patch("/auth/me/password", status_code=204)
async def change_own_password(payload: ChangePasswordRequest,
                              user: User = Depends(get_current_user),
                              db: AsyncSession = Depends(get_db)):
    """Self-service password change — the closest thing to a reset flow
    without email infrastructure. Requires the current password."""
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    user.hashed_password = hash_password(payload.new_password)
    await db.commit()


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


@router.get("/auth/users", response_model=list[UserOut])
async def list_users(_: User = Depends(require_role(UserRole.admin)),
                     db: AsyncSession = Depends(get_db)):
    """Admin-only: list every provisioned user."""
    result = await db.execute(select(User).order_by(User.created_at))
    return [_user_out(u) for u in result.scalars().all()]


@router.patch("/auth/users/{user_id}", response_model=UserOut)
async def update_user(user_id: str, payload: UserUpdate,
                      admin: User = Depends(require_role(UserRole.admin)),
                      db: AsyncSession = Depends(get_db)):
    """Admin-only: change a user's role or active status."""
    not_found = HTTPException(status_code=404, detail="User not found")
    target = await db.get(User, _parse_uuid(user_id, not_found))
    if not target:
        raise not_found
    data = payload.model_dump(exclude_unset=True)
    if "role" in data and target.id == admin.id and data["role"] != UserRole.admin:
        raise HTTPException(status_code=400, detail="You can't demote your own account")
    if "is_active" in data and target.id == admin.id and not data["is_active"]:
        raise HTTPException(status_code=400, detail="You can't deactivate your own account")
    for k, v in data.items():
        setattr(target, k, v)
    await db.commit()
    await db.refresh(target)
    return _user_out(target)
