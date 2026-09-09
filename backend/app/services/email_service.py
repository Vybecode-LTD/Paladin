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

# Default sender for demo-request replies and test emails, used when the admin
# has not configured one in Settings (smtp_settings.from_email).
DEMO_REPLY_FROM = "info@ashfordbriggs.com"
DEMO_REPLY_SUBJECT = "Your request for demo access to Paladin"

# Fail before a reverse proxy's typical ~30 s limit, so the admin sees the real
# SMTP error instead of an opaque 504 from the proxy (seen on the dev server).
SMTP_TIMEOUT_SECONDS = 15


def smtp_tls_options(port: int, use_tls: bool) -> dict[str, bool]:
    """Map the Settings screen's single "use TLS" switch onto aiosmtplib's two
    mutually exclusive modes. Port 465 is implicit TLS by convention (the
    server speaks TLS before any SMTP greeting), so it always gets ``use_tls``
    and never STARTTLS; every other port treats the switch as STARTTLS.
    Passing both would make aiosmtplib raise ValueError."""
    if port == 465:
        return {"use_tls": True, "start_tls": False}
    return {"use_tls": False, "start_tls": bool(use_tls)}


def resolve_from_email(configured: str | None) -> str:
    """The admin-configured sender, or the default when blank. Mail providers
    reject a From address the authenticated account does not own, so the admin
    sets the one their account is allowed to use."""
    return (configured or "").strip() or DEMO_REPLY_FROM


class EmailServiceError(Exception):
    """SMTP isn't configured yet, or the send itself failed — caught by
    routers and turned into a clean 4xx/502 instead of an unhandled 500."""


async def get_smtp_settings(db: AsyncSession) -> SmtpSettings | None:
    """Singleton read — the app only ever stores one settings row."""
    result = await db.execute(select(SmtpSettings))
    return result.scalars().first()


async def _send(
    db: AsyncSession, *, to_email: str, to_name: str, subject: str, body: str,
) -> None:
    cfg = await get_smtp_settings(db)
    if not cfg or not cfg.host or not cfg.username:
        raise EmailServiceError("SMTP is not configured yet — set it up in Settings first.")
    if not cfg.encrypted_password:
        raise EmailServiceError("SMTP password is not set — set it up in Settings first.")
    try:
        password = decrypt_secret(cfg.encrypted_password)
    except ValueError as exc:
        raise EmailServiceError(str(exc))

    from_email = resolve_from_email(cfg.from_email)
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
            timeout=SMTP_TIMEOUT_SECONDS,
            **smtp_tls_options(cfg.port, cfg.use_tls),
        )
    except (aiosmtplib.SMTPException, OSError) as exc:
        raise EmailServiceError(f"Could not send email: {exc}")


async def send_demo_reply(db: AsyncSession, *, to_email: str, to_name: str, body: str) -> None:
    await _send(
        db, to_email=to_email, to_name=to_name,
        subject=DEMO_REPLY_SUBJECT, body=body,
    )


async def send_test_email(db: AsyncSession, *, to_email: str) -> None:
    await _send(
        db, to_email=to_email, to_name="",
        subject="Paladin SMTP test",
        body="This is a test email confirming your SMTP settings are working correctly.",
    )
