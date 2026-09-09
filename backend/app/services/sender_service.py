"""Builds the configured Sender from the stored settings.

The single place that knows which providers exist. Routers and the send
worker ask for "the sender" and get one back; adding a third provider later
touches this file and nothing above it.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_secret
from app.models.sender_settings import SenderProvider, SenderSettings
from app.services import email_service
from app.services.senders.base import Sender, SenderError
from app.services.senders.mailgun_sender import MailgunSender
from app.services.senders.smtp_sender import SmtpSender


async def get_sender_settings(db: AsyncSession) -> SenderSettings | None:
    """Singleton read — the app only ever stores one row, same as
    smtp_settings."""
    result = await db.execute(select(SenderSettings))
    return result.scalars().first()


def _decrypt(value: str | None, *, label: str) -> str:
    if not value:
        raise SenderError(f"{label} is not set — configure it in Settings.")
    try:
        return decrypt_secret(value)
    except ValueError as exc:
        # Raised when ENCRYPTION_KEY changed after the secret was stored. The
        # fix is re-entering the credential, not restoring the old key, so say
        # so rather than surfacing a bare decryption error.
        raise SenderError(
            f"{label} could not be decrypted ({exc}). Re-enter it in Settings."
        )


async def build_sender(db: AsyncSession) -> Sender:
    """The configured sender, ready to use. Raises SenderError with a message
    an admin can act on when configuration is missing or unusable."""
    cfg = await get_sender_settings(db)
    if cfg is None:
        raise SenderError(
            "No campaign sender is configured yet — set one up in Settings first."
        )

    if cfg.provider == SenderProvider.mailgun:
        return MailgunSender(
            domain=cfg.mailgun_domain,
            api_key=_decrypt(cfg.encrypted_api_key, label="Mailgun API key"),
            region=cfg.mailgun_region,
        )

    # SMTP borrows the credentials already configured for demo replies rather
    # than storing a second copy. See smtp_sender's module docstring for why
    # this path is for internal test sends only.
    smtp = await email_service.get_smtp_settings(db)
    if smtp is None or not smtp.host:
        raise SenderError(
            "The campaign sender is set to SMTP, but SMTP is not configured — "
            "set it up in the SMTP section of Settings first."
        )
    return SmtpSender(
        host=smtp.host,
        port=smtp.port,
        username=smtp.username,
        password=_decrypt(smtp.encrypted_password, label="SMTP password"),
        use_tls=smtp.use_tls,
    )


async def get_webhook_secret(db: AsyncSession) -> str:
    """The Mailgun webhook signing key, for verifying inbound events.

    A distinct credential from the API key. Returns "" when unset so the
    webhook route can refuse every event rather than accepting unverified
    ones — failing closed, because an unverified event could suppress a real
    contact or fabricate a delivery.
    """
    cfg = await get_sender_settings(db)
    if cfg is None or not cfg.encrypted_webhook_secret:
        return ""
    try:
        return decrypt_secret(cfg.encrypted_webhook_secret)
    except ValueError:
        return ""
