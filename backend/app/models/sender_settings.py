import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class SenderProvider(str, enum.Enum):
    """Which implementation carries campaign mail (services/senders/).

    `smtp` reuses the company SMTP credentials already configured for demo
    replies. It is correct for internal test sends and nothing else: raw SMTP
    reports no delivery, bounce or complaint events, so three of the four
    exact-tier metrics do not exist on that path, and sending campaigns
    through a Workspace mailbox breaks that provider's terms and puts campaign
    reputation on a founder's own inbox.
    """
    smtp = "smtp"
    mailgun = "mailgun"


class MailgunRegion(str, enum.Enum):
    us = "us"
    eu = "eu"


class SenderSettings(Base):
    """Campaign sender configuration — a singleton row, same shape as
    SmtpSettings.

    Deliberately a SEPARATE table from smtp_settings rather than more columns
    on it. The two describe different things: smtp_settings is how a person
    replies to one demo request, this is how the company sends a campaign to
    a list. Keeping them apart means changing the campaign provider can never
    disturb the demo-reply path, and the two can point at different domains
    and different reputations, which is the entire point of sending campaigns
    from a subdomain.

    `encrypted_api_key` and `encrypted_webhook_secret` are Fernet-encrypted
    (app/core/crypto.py) and never returned to the client in plaintext.
    """
    __tablename__ = "sender_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[SenderProvider] = mapped_column(
        SAEnum(SenderProvider, name="sender_provider"), default=SenderProvider.smtp
    )

    # --- Mailgun ---------------------------------------------------------
    # The sending domain, e.g. updates.ashfordbriggs.com. MUST NOT be the same
    # domain used for the product's password and PIN mail: sharing it merges
    # campaign reputation with the most sensitive mail the company sends.
    mailgun_domain: Mapped[str] = mapped_column(String(255), default="")
    encrypted_api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Mailgun's webhook signing key is a DIFFERENT credential from the API
    # key (dashboard: Settings, API keys, HTTP webhook signing key). Used to
    # verify the HMAC on every inbound event.
    encrypted_webhook_secret: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mailgun_region: Mapped[MailgunRegion] = mapped_column(
        SAEnum(MailgunRegion, name="mailgun_region"), default=MailgunRegion.us
    )

    # --- Identity applied to every campaign ------------------------------
    # Chosen once and never varied: consistency is itself a reputation signal,
    # and it is what recipients add to their contacts.
    from_name: Mapped[str] = mapped_column(String(200), default="")
    from_email: Mapped[str] = mapped_column(String(320), default="")
    # Domain that receives replies, e.g. updates.ashfordbriggs.com. Each
    # message gets a unique plus-tagged address under it so a reply can be
    # matched to its campaign and recipient.
    reply_domain: Mapped[str] = mapped_column(String(255), default="")
    # Public origin serving the tracking pixel and click redirects, no
    # trailing slash. Kept separate from settings.site_url because tracking
    # must live on the campaign subdomain, not the marketing site.
    tracking_base_url: Mapped[str] = mapped_column(String(500), default="")
    # Required in the footer of every marketing message by US law.
    postal_address: Mapped[str] = mapped_column(String(500), default="")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
