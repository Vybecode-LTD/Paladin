"""Domain reputation: who sends as us, where our mail lands, and whether
anyone has listed us.

These four tables answer the questions an admin has on the morning something
looks wrong, and the DMARC one answers the question that has to be settled
*before* the domain policy can be tightened: which systems are sending as
ashfordbriggs.com, and are they all authenticating? Turning on enforcement
without that answer is how a company silently stops receiving its own
voicemail notifications.
"""
import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean, Date, DateTime, Enum as SAEnum, Integer, String, Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DmarcRecord(Base):
    """One sending source, from one provider's daily aggregate report.

    A report covers a day and contains a handful of these, one per source
    address. Stored per source rather than per report because the question is
    always "what is this IP and why is it failing", never "show me report
    12345".
    """
    __tablename__ = "dmarc_records"
    __table_args__ = (
        # Providers resend a report if they think it was not received, and the
        # dmarc mailbox may be polled twice. Same report, same source, same
        # window is the same fact.
        UniqueConstraint(
            "report_id", "source_ip", "header_from",
            name="uq_dmarc_records_report_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_name: Mapped[str] = mapped_column(String(255), default="")
    report_id: Mapped[str] = mapped_column(String(255), index=True)
    date_begin: Mapped[date] = mapped_column(Date, index=True)
    date_end: Mapped[date] = mapped_column(Date)

    # The domain the policy was published for, and the domain in the visible
    # From header. They differ when a subdomain is sending.
    policy_domain: Mapped[str] = mapped_column(String(255), default="")
    header_from: Mapped[str] = mapped_column(String(255), default="", index=True)
    policy_p: Mapped[str] = mapped_column(String(20), default="")

    source_ip: Mapped[str] = mapped_column(String(45), index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)

    # What the receiver actually decided, after alignment.
    disposition: Mapped[str] = mapped_column(String(20), default="")
    dkim_aligned: Mapped[bool] = mapped_column(Boolean, default=False)
    spf_aligned: Mapped[bool] = mapped_column(Boolean, default=False)

    # The raw auth results, which say WHICH domain signed or authorised —
    # the difference between "DKIM passed for mailgun.org" and "DKIM passed
    # for ashfordbriggs.com", and therefore between a forwarding artefact and
    # a real alignment failure.
    dkim_domain: Mapped[str] = mapped_column(String(255), default="")
    spf_domain: Mapped[str] = mapped_column(String(255), default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    @property
    def passed(self) -> bool:
        """DMARC passes when EITHER check passes and aligns. Requiring both
        would report every forwarded message as a failure, because forwarding
        breaks SPF by design."""
        return self.dkim_aligned or self.spf_aligned


class SeedInbox(Base):
    """A mailbox we own that receives every campaign, so the system can see
    where its own mail landed.

    The only way to know about a spam-folder placement before a client
    mentions it. Deliberately company-owned accounts rather than a founder's
    personal one, so they outlive any individual.
    """
    __tablename__ = "seed_inboxes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[str] = mapped_column(String(100), default="")
    email: Mapped[str] = mapped_column(String(320), unique=True)
    # "gmail", "outlook", "other" — decides which folder names to look in,
    # since the spam folder is called something different everywhere.
    provider: Mapped[str] = mapped_column(String(50), default="gmail")
    imap_host: Mapped[str] = mapped_column(String(255), default="")
    imap_port: Mapped[int] = mapped_column(Integer, default=993)
    imap_username: Mapped[str] = mapped_column(String(320), default="")
    # Fernet-encrypted, same as every other stored secret. For Gmail this is
    # an app password, not the account password.
    encrypted_password: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Placement(str, enum.Enum):
    inbox = "inbox"
    spam = "spam"
    promotions = "promotions"      # Gmail's tab: delivered, but not seen
    missing = "missing"            # never arrived at all
    error = "error"                # could not check; NOT the same as missing


class SeedPlacement(Base):
    """Where one campaign landed in one seed inbox."""
    __tablename__ = "seed_placements"
    __table_args__ = (
        UniqueConstraint("campaign_id", "seed_inbox_id", name="uq_seed_placements_campaign_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    seed_inbox_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    placement: Mapped[Placement] = mapped_column(
        SAEnum(Placement, name="seed_placement")
    )
    detail: Mapped[str] = mapped_column(Text, default="")
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class BlocklistResult(Base):
    """One blocklist lookup for one target.

    Kept as history rather than a current-status flag: a listing that appeared
    and cleared last Tuesday is the thing you want to find when this
    Tuesday's delivery looks odd.
    """
    __tablename__ = "blocklist_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # The domain or IP that was looked up.
    target: Mapped[str] = mapped_column(String(255), index=True)
    # The list's own zone, e.g. "zen.spamhaus.org".
    blocklist: Mapped[str] = mapped_column(String(255))
    listed: Mapped[bool] = mapped_column(Boolean, default=False)
    # The A record a listing returns, which encodes WHY on most lists.
    response: Mapped[str] = mapped_column(String(100), default="")
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
