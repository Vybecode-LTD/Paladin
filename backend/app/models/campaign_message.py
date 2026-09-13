import secrets
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


def new_tracking_token() -> str:
    """A random, opaque, URL-safe token — 128 bits, 22 characters.

    Deliberately random-and-stored rather than an HMAC of the message id.
    A signed token cannot be revoked without rotating the key for every
    message ever sent, and it leaks its own structure; a random token is a
    single indexed lookup, is individually revocable by deleting the row, and
    tells an observer nothing. It appears in URLs inside sent email, so it
    must never encode the recipient's address.
    """
    return secrets.token_urlsafe(16)


class CampaignMessage(Base):
    """One campaign, one recipient — the row every metric hangs off.

    Created when a campaign is expanded, before anything is sent, so a send
    that fails halfway leaves a queryable record of what was and was not
    attempted rather than a silent gap.
    """
    __tablename__ = "campaign_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id"), index=True
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), index=True
    )
    # Denormalised on purpose: the address actually sent to, frozen at send
    # time. A contact may later change their address, and the events for this
    # message still belong to the address that received it.
    email: Mapped[str] = mapped_column(String(320))

    token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=new_tracking_token
    )
    # "a" or "b" for an A/B campaign; "holdout" for the held-back baseline,
    # which is never sent but IS counted, so the comparison has a control.
    variant: Mapped[str] = mapped_column(String(20), default="a")

    # The provider's own id, returned on accept. Mailgun webhooks identify a
    # message by its Message-Id header, so this is how a delivery or bounce
    # event finds its way back to this row when the custom variable is absent.
    provider_message_id: Mapped[str] = mapped_column(String(500), default="", index=True)

    # Whether the pixel was embedded. False when the contact has not consented
    # to tracking — recorded so a later open-rate figure can state honestly
    # how much of the audience was even measurable.
    pixel_embedded: Mapped[bool] = mapped_column(Boolean, default=False)

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Set when the provider refused the message outright, as distinct from
    # accepting it and bouncing later. The two are different failures and the
    # dashboard must not merge them.
    send_error: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    @property
    def is_holdout(self) -> bool:
        return self.variant == "holdout"
