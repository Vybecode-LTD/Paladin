import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class SuppressionReason(str, enum.Enum):
    unsubscribed = "unsubscribed"
    complained = "complained"      # pressed the spam button
    hard_bounced = "hard_bounced"
    manual = "manual"


class Suppression(Base):
    """Addresses that must never be sent to again.

    Deliberately keyed on the email address rather than on a contact id: an
    address can be suppressed before any contact row exists for it (a
    complaint arriving by webhook for an address imported later), and deleting
    a contact must NOT quietly re-enable mail to someone who asked to stop.
    This table is the one place in the system with no delete path in the API.

    Rows here are permanent by design. Every other record has a retention
    policy; forgetting a suppression is how a company mails a complainer a
    second time, which is both a legal problem and the fastest way to lose
    domain reputation.
    """
    __tablename__ = "suppressions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Stored lower-cased and stripped by suppression_service — never write to
    # this column directly, or case differences will let a suppressed address
    # slip through the guard.
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    reason: Mapped[SuppressionReason] = mapped_column(
        SAEnum(SuppressionReason, name="suppression_reason")
    )
    # Free-text provenance: which campaign, which webhook, who added it.
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
