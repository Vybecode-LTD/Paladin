import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class CampaignStatus(str, enum.Enum):
    """`sending` is a real state, not a transient one: expanding a campaign
    into per-recipient messages and handing them to the provider happens in a
    worker over seconds to minutes, and the UI has to show that honestly
    rather than pretending the send is instant."""
    draft = "draft"
    scheduled = "scheduled"
    sending = "sending"
    sent = "sent"
    failed = "failed"


class Campaign(Base):
    """One send to one audience.

    Body is Markdown, matching the blog model — the same authoring convention
    the team already uses, rendered to email-safe HTML at send time rather
    than stored twice.
    """
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(300))
    subject: Mapped[str] = mapped_column(String(500), default="")
    # Shown after the subject in most inbox previews. Absent it, clients pull
    # the first line of the body, which is usually a greeting.
    preheader: Mapped[str] = mapped_column(String(300), default="")
    body_markdown: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus, name="campaign_status"),
        default=CampaignStatus.draft,
        index=True,
    )

    # Audience. A named segment resolved at send time rather than a frozen
    # recipient list, so suppression and consent are re-checked against the
    # state of the world when the send actually runs, not when it was drafted.
    segment: Mapped[str] = mapped_column(String(100), default="")

    # --- A/B ------------------------------------------------------------
    # One variant only. On a list of a few hundred, a second variable makes
    # every cell too small for any difference to be real.
    variant_b_subject: Mapped[str] = mapped_column(String(500), default="")
    # Percent of the audience held back entirely, as the baseline the campaign
    # is measured against. 0 disables the holdout.
    holdout_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Trackable destinations in the body, in document order, frozen when the
    # campaign is expanded. A click URL carries only this list's index, which
    # keeps it short — it is printed inside mail that can never be edited —
    # and it is safe to freeze because a queued campaign's body cannot change.
    links: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]")

    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Populated when status becomes `failed`, so the UI can say what went
    # wrong instead of showing a dead campaign with no explanation.
    error: Mapped[str] = mapped_column(Text, default="")

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
