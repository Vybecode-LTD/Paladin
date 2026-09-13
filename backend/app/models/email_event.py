import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class EventType(str, enum.Enum):
    # From the provider — these are facts about what the mail system did.
    accepted = "accepted"
    delivered = "delivered"
    soft_bounced = "soft_bounced"
    hard_bounced = "hard_bounced"
    complained = "complained"
    unsubscribed = "unsubscribed"
    # From our own endpoints — these are inferences about what a person did.
    opened = "opened"
    clicked = "clicked"
    page_confirmed = "page_confirmed"   # landing-page beacon: a real browser ran
    replied = "replied"
    auto_replied = "auto_replied"       # out-of-office; NOT engagement
    # From the product itself: a demo booked, a first login, a feature used.
    # The specific action is a name in the payload rather than its own enum
    # value, so the product can start reporting a new one without a migration.
    converted = "converted"


class EventTier(str, enum.Enum):
    """How much this event can be trusted. Stored on the row, surfaced on
    every figure in the dashboard.

    This is the whole point of building rather than buying. Around half of all
    tracked opens industry-wide are Apple's automatic prefetch, and corporate
    scanners fetch every link in a message within seconds of delivery. A tool
    that reports those as people is not measuring engagement, and a company
    selling honesty about recruiting calls should not ship a dashboard that
    does it.

    exact     the mail system told us; cannot be wrong
    verified  a human action we can prove
    inferred  a signal machines also generate, filtered as well as we can
    derived   computed from the others
    """
    exact = "exact"
    verified = "verified"
    inferred = "inferred"
    derived = "derived"


class EmailEvent(Base):
    """Append-only. Nothing rewrites an event; a later, better-corroborated
    signal is a NEW row (an inferred open followed by a verified click), and
    the reporting layer resolves them. Rewriting would destroy the audit trail
    that makes the tier system meaningful."""
    __tablename__ = "email_events"
    __table_args__ = (
        # The pixel is fetched every time a message is re-opened, and providers
        # retry webhooks. Dedupe on the provider's own event id where there is
        # one; our own endpoints pass a synthesised key (token + type + minute
        # bucket) so a burst of re-fetches collapses to one row.
        UniqueConstraint("dedupe_key", name="uq_email_events_dedupe_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaign_messages.id"), nullable=True, index=True
    )
    # Denormalised so provider events that arrive before, or without, a
    # matching message row are still recorded rather than dropped.
    email: Mapped[str] = mapped_column(String(320), index=True)

    type: Mapped[EventType] = mapped_column(
        SAEnum(EventType, name="email_event_type"), index=True
    )
    tier: Mapped[EventTier] = mapped_column(SAEnum(EventTier, name="email_event_tier"))

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    dedupe_key: Mapped[str] = mapped_column(String(200))

    # Why this event got the tier it did — "apple-mpp", "datacenter-ip",
    # "beacon-confirmed", "provider-webhook". Makes the classifier auditable
    # instead of a black box, and is what lets a wrong rule be found later.
    classification: Mapped[str] = mapped_column(String(100), default="")

    # User agent, IP, geolocation, the provider's raw body. JSONB rather than
    # columns because the shape differs per provider and per event type, and
    # because we want the original preserved for any reclassification.
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
