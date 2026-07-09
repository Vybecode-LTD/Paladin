"""Sends real email through the company's own SMTP server, configured via the
admin Settings screen (models/smtp_settings.py) — deliberately NOT sourced
from Railway/env vars, per the product requirement that the company manage
their own SMTP credentials in-app."""
from email.message import EmailMessage
import aiosmtplib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.crypto import decrypt_secret
from app.models.smtp_settings import SmtpSettings

# Fixed by the business for every demo-request reply — not admin-configurable.
DEMO_REPLY_FROM = "info@ashfordbriggs.com"
DEMO_REPLY_SUBJECT = "Your request for demo access to Paladin"


class EmailServiceError(Exception):
    """SMTP isn't configured yet, or the send itself failed — caught by
    routers and turned into a clean 4xx/502 instead of an unhandled 500."""


async def get_smtp_settings(db: AsyncSession) -> SmtpSettings | None:
    """Singleton read — the app only ever stores one settings row."""
    result = await db.execute(select(SmtpSettings))
    return result.scalars().first()


async def _send(
    db: AsyncSession, *, to_email: str, to_name: str, subject: str, body: str, from_email: str,
) -> None:
    cfg = await get_smtp_settings(db)
    if not cfg or not cfg.host or not cfg.username:
        raise EmailServiceError("SMTP is not configured yet — set it up in Settings first.")
    if not cfg.encrypted_password:
        raise EmailServiceError("SMTP password is not set — set it up in Settings first.")
    password = decrypt_secret(cfg.encrypted_password)

    message = EmailMessage()
    message["From"] = f'"{cfg.from_name}" <{from_email}>' if cfg.from_name else from_email
    message["To"] = f'"{to_name}" <{to_email}>' if to_name else to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=cfg.host,
            port=cfg.port,
            username=cfg.username,
            password=password,
            start_tls=cfg.use_tls,
            timeout=30,
        )
    except (aiosmtplib.SMTPException, OSError) as exc:
        raise EmailServiceError(f"Could not send email: {exc}")


async def send_demo_reply(db: AsyncSession, *, to_email: str, to_name: str, body: str) -> None:
    await _send(
        db, to_email=to_email, to_name=to_name,
        subject=DEMO_REPLY_SUBJECT, body=body, from_email=DEMO_REPLY_FROM,
    )


async def send_test_email(db: AsyncSession, *, to_email: str) -> None:
    await _send(
        db, to_email=to_email, to_name="",
        subject="Paladin SMTP test",
        body="This is a test email confirming your SMTP settings are working correctly.",
        from_email=DEMO_REPLY_FROM,
    )
