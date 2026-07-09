"""Admin-only SMTP settings API. Single-row config used to send demo-request
replies (see services/email_service.py) — password is write-only, never
returned to the client in plaintext (see schemas/settings.py)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.crypto import encrypt_secret
from app.core.database import get_db
from app.middleware.auth import require_role
from app.models.smtp_settings import SmtpSettings
from app.models.user import User, UserRole
from app.schemas.settings import SmtpSettingsOut, SmtpSettingsUpdate, SmtpTestRequest
from app.services import email_service
from app.services.email_service import EmailServiceError

router = APIRouter()


def _to_out(row: SmtpSettings | None) -> SmtpSettingsOut:
    if row is None:
        return SmtpSettingsOut(
            host="", port=587, username="", password_set=False,
            use_tls=True, from_name="", updated_at=None,
        )
    return SmtpSettingsOut(
        host=row.host, port=row.port, username=row.username,
        password_set=bool(row.encrypted_password),
        use_tls=row.use_tls, from_name=row.from_name, updated_at=row.updated_at,
    )


@router.get("/admin/settings/smtp", response_model=SmtpSettingsOut)
async def get_smtp_settings(
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    row = await email_service.get_smtp_settings(db)
    return _to_out(row)


@router.put("/admin/settings/smtp", response_model=SmtpSettingsOut)
async def update_smtp_settings(
    payload: SmtpSettingsUpdate,
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    row = await email_service.get_smtp_settings(db)
    if row is None:
        row = SmtpSettings()
        db.add(row)

    row.host = payload.host
    row.port = payload.port
    row.username = payload.username
    row.use_tls = payload.use_tls
    row.from_name = payload.from_name
    if payload.password:
        try:
            row.encrypted_password = encrypt_secret(payload.password)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    await db.commit()
    await db.refresh(row)
    return _to_out(row)


@router.post("/admin/settings/smtp/test")
async def test_smtp_settings(
    payload: SmtpTestRequest,
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    try:
        await email_service.send_test_email(db, to_email=payload.to_email)
    except EmailServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"sent": True}
