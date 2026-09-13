"""Admin-only campaign sender API.

Separate router from routers/settings.py (which owns the SMTP config used for
demo replies) for the same reason the tables are separate: changing how
campaigns are sent must never be able to disturb the path a person uses to
answer a demo request.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt_secret
from app.core.database import get_db
from app.middleware.auth import require_role
from app.models.sender_settings import MailgunRegion, SenderProvider, SenderSettings
from app.models.user import User, UserRole
from app.schemas.sender import (
    SenderSettingsOut, SenderSettingsUpdate, SenderTestRequest,
)
from app.services import sender_service
from app.services.senders.base import OutboundMessage, SenderError

router = APIRouter()

TEST_SUBJECT = "Paladin campaign sender test"
TEST_BODY = (
    "This is a test from the Paladin admin backend, confirming the campaign "
    "sender is configured correctly.\n\nNo campaign was sent."
)


def _to_out(row: SenderSettings | None) -> SenderSettingsOut:
    if row is None:
        return SenderSettingsOut(
            provider=SenderProvider.smtp,
            mailgun_domain="", mailgun_region=MailgunRegion.us,
            api_key_set=False, webhook_secret_set=False,
            from_name="", from_email="", reply_domain="",
            tracking_base_url="", postal_address="", updated_at=None,
        )
    return SenderSettingsOut(
        provider=row.provider,
        mailgun_domain=row.mailgun_domain,
        mailgun_region=row.mailgun_region,
        api_key_set=bool(row.encrypted_api_key),
        webhook_secret_set=bool(row.encrypted_webhook_secret),
        from_name=row.from_name,
        from_email=row.from_email,
        reply_domain=row.reply_domain,
        tracking_base_url=row.tracking_base_url,
        postal_address=row.postal_address,
        updated_at=row.updated_at,
    )


@router.get("/admin/settings/sender", response_model=SenderSettingsOut)
async def get_sender_settings(
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    return _to_out(await sender_service.get_sender_settings(db))


@router.put("/admin/settings/sender", response_model=SenderSettingsOut)
async def update_sender_settings(
    payload: SenderSettingsUpdate,
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    row = await sender_service.get_sender_settings(db)
    if row is None:
        row = SenderSettings()
        db.add(row)

    row.provider = payload.provider
    row.mailgun_domain = payload.mailgun_domain
    row.mailgun_region = payload.mailgun_region
    row.from_name = payload.from_name
    row.from_email = payload.from_email
    row.reply_domain = payload.reply_domain
    row.tracking_base_url = payload.tracking_base_url
    row.postal_address = payload.postal_address

    try:
        if payload.api_key:
            row.encrypted_api_key = encrypt_secret(payload.api_key)
        if payload.webhook_secret:
            row.encrypted_webhook_secret = encrypt_secret(payload.webhook_secret)
    except ValueError as exc:
        # ENCRYPTION_KEY missing or invalid. Deliberately a 400 with the real
        # message: it is a deployment configuration problem the admin can fix,
        # not a server fault to hide behind a 500.
        raise HTTPException(status_code=400, detail=str(exc))

    await db.commit()
    await db.refresh(row)
    return _to_out(row)


@router.post("/admin/settings/sender/test")
async def test_sender(
    payload: SenderTestRequest,
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    """Verify the configuration, and optionally send one real test message.

    Verification always runs first. Without a recipient this touches no
    inbox, which is what makes it safe to click while getting the settings
    right — the reason the SMTP screen's equivalent button was frustrating is
    that it could only prove itself by mailing someone.
    """
    try:
        sender = await sender_service.build_sender(db)
        await sender.verify()
    except SenderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if payload.to_email is None:
        return {"verified": True, "sent": False}

    cfg = await sender_service.get_sender_settings(db)
    from_email = (cfg.from_email if cfg else "") or ""
    if not from_email:
        raise HTTPException(
            status_code=400,
            detail="Set the campaign From address before sending a test message.",
        )

    try:
        await sender.send(OutboundMessage(
            to_email=payload.to_email,
            subject=TEST_SUBJECT,
            text_body=TEST_BODY,
            html_body="",
            from_email=from_email,
            from_name=cfg.from_name if cfg else "",
            tags=["sender-test"],
        ))
    except SenderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {"verified": True, "sent": True}
