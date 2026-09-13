import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ConsentBasis(str, enum.Enum):
    """How this person came to be on the list.

    Stored per contact rather than assumed list-wide because the rules differ
    by jurisdiction and by how the address was obtained: the US allows an
    opt-out model, Canada requires consent before the first send, and the EU
    and UK require consent to send AND separate consent to track opens. The
    composer reads this field plus `country` and builds the correct message
    variant, so nobody has to remember the rules at send time.

    `unknown` is deliberately a value rather than a null: it makes "we have
    no basis recorded for this person" explicit and queryable, and the send
    guard refuses to mail anyone still marked unknown.
    """
    express = "express"           # explicitly opted in
    implied = "implied"           # existing business relationship (CASL)
    contract = "contract"         # a signed agreement covers it
    signup = "signup"             # signed up on the site
    demo_request = "demo_request" # submitted the demo form
    unknown = "unknown"           # not established — never mailed


class ContactStatus(str, enum.Enum):
    """`retired` is distinct from `unsubscribed`: the contact never asked to
    stop, we stopped because they ignored several consecutive campaigns.
    Continuing to mail non-engaged recipients erodes domain reputation, so
    retirement is a deliverability measure, not a request we are honouring."""
    active = "active"
    unsubscribed = "unsubscribed"
    bounced = "bounced"
    retired = "retired"


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), default="")
    company: Mapped[str] = mapped_column(String(200), default="")
    # ISO 3166-1 alpha-2. Drives which consent rules apply; "" means unknown,
    # which the composer treats as the strictest applicable rule.
    country: Mapped[str] = mapped_column(String(2), default="")

    consent_basis: Mapped[ConsentBasis] = mapped_column(
        SAEnum(ConsentBasis, name="consent_basis"), default=ConsentBasis.unknown
    )
    consent_recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    consent_note: Mapped[str] = mapped_column(Text, default="")
    # Separate from consent to receive mail. April 2026 guidance from the
    # French and Italian regulators treats per-recipient open tracking as
    # needing its own consent, so a contact can agree to the mail and not the
    # pixel. Defaults False: the pixel is opt-in, never opt-out.
    tracking_consent: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[ContactStatus] = mapped_column(
        SAEnum(ContactStatus, name="contact_status"),
        default=ContactStatus.active,
        index=True,
    )
    # Audience membership. A campaign names one tag and every contact carrying
    # it is in scope, resolved at SEND time rather than frozen when the
    # campaign was drafted — so suppression, consent and status are re-checked
    # against the state of the world when the mail actually goes out.
    # A plain text array rather than a join table: the list is a few hundred
    # people with a handful of tags, and a second table would buy nothing but
    # a join on every expansion.
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), default=list, server_default="{}"
    )
    # Recency/frequency of VERIFIED engagement only (clicks confirmed by the
    # landing-page beacon, and replies) — never inferred opens, which are
    # roughly half machine prefetch and would inflate this into nonsense.
    engagement_score: Mapped[int] = mapped_column(Integer, default=0)
    last_engaged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Consecutive campaigns sent with no verified engagement. Drives automatic
    # retirement; reset to 0 on any verified event.
    consecutive_ignored: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def is_mailable(self) -> bool:
        """A contact may be mailed only with an established consent basis and
        an active status. Checked by the send guard alongside the suppression
        list — this property alone is NOT the guard (see
        services/suppression_service.py), because suppression outranks
        everything recorded here."""
        return (
            self.status == ContactStatus.active
            and self.consent_basis != ConsentBasis.unknown
        )

    @property
    def may_track_opens(self) -> bool:
        """US contacts may be tracked under the opt-out model; everyone else
        needs explicit tracking consent. An unknown country is treated as
        non-US, i.e. the stricter rule."""
        return self.tracking_consent or self.country.upper() == "US"
