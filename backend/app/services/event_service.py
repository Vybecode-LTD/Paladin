"""Turns provider webhooks into EmailEvent rows.

Everything here is about being boring under repetition. Mailgun retries a
webhook until it receives a 200, so the same event arrives several times and
must land once; and three event types must also suppress the address, which
has to happen exactly once no matter how many copies arrive.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign_message import CampaignMessage
from app.models.email_event import EmailEvent, EventTier, EventType
from app.models.suppression import SuppressionReason
from app.services import suppression_service

logger = logging.getLogger(__name__)

# Mailgun's event name to ours. `failed` splits on severity, so it is handled
# separately below rather than living in this table.
MAILGUN_EVENTS: dict[str, tuple[EventType, EventTier]] = {
    "accepted": (EventType.accepted, EventTier.exact),
    "delivered": (EventType.delivered, EventTier.exact),
    "complained": (EventType.complained, EventTier.exact),
    "unsubscribed": (EventType.unsubscribed, EventTier.exact),
    # We disable Mailgun's own open and click tracking on every send, so these
    # should never arrive. Mapped anyway, as INFERRED: if a domain-level
    # setting ever re-enables them, the data still lands in the right tier
    # rather than being silently dropped or, worse, counted as exact.
    "opened": (EventType.opened, EventTier.inferred),
    "clicked": (EventType.clicked, EventTier.inferred),
}

# Which event types take an address out of circulation, and why.
SUPPRESSING_EVENTS: dict[EventType, SuppressionReason] = {
    EventType.hard_bounced: SuppressionReason.hard_bounced,
    EventType.complained: SuppressionReason.complained,
    EventType.unsubscribed: SuppressionReason.unsubscribed,
}


def classify_mailgun(event: dict) -> tuple[EventType, EventTier] | None:
    """Map one Mailgun event. None for anything unrecognised.

    A `failed` event splits on severity, and the distinction matters: a
    permanent failure means the address is dead and must be suppressed, while
    a temporary one is a full mailbox or a greylist and the provider will
    retry on its own. Treating them alike would either discard live contacts
    or keep mailing dead ones.
    """
    name = str(event.get("event", "")).strip().lower()
    if name == "failed":
        severity = str(event.get("severity", "")).strip().lower()
        if severity == "permanent":
            return EventType.hard_bounced, EventTier.exact
        return EventType.soft_bounced, EventTier.exact
    return MAILGUN_EVENTS.get(name)


def occurred_at_of(event: dict) -> datetime:
    """Mailgun timestamps are float epoch seconds. Falls back to now rather
    than raising: an event with a malformed timestamp is still a real event,
    and losing it would be worse than recording it a few seconds late."""
    raw = event.get("timestamp")
    try:
        return datetime.fromtimestamp(float(raw), tz=timezone.utc)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def recipient_of(event: dict) -> str:
    return suppression_service.normalize(str(event.get("recipient", "")))


def token_of(event: dict) -> str:
    """The message token we attached as a Mailgun custom variable (`v:` on the
    way out, `user-variables` on the way back). This is the primary way an
    event finds its message."""
    variables = event.get("user-variables")
    if isinstance(variables, dict):
        return str(variables.get("message_token", "")).strip()
    return ""


def provider_message_id_of(event: dict) -> str:
    """Fallback correlation. Mailgun reports the Message-Id header without the
    angle brackets it carries on the wire, so both forms are compared."""
    message = event.get("message")
    if isinstance(message, dict):
        headers = message.get("headers")
        if isinstance(headers, dict):
            return str(headers.get("message-id", "")).strip()
    return ""


async def find_message(db: AsyncSession, event: dict) -> CampaignMessage | None:
    """Locate the CampaignMessage an event belongs to, by token first and
    provider message id second.

    Returning None is normal, not a failure: a complaint can arrive for an
    address this system never sent to (a forwarded message, or mail from
    another system on the same domain). The event is still recorded against
    the address, because suppression must happen either way.
    """
    token = token_of(event)
    if token:
        row = (await db.execute(
            select(CampaignMessage).where(CampaignMessage.token == token)
        )).scalar_one_or_none()
        if row is not None:
            return row

    message_id = provider_message_id_of(event)
    if message_id:
        candidates = [message_id, f"<{message_id}>", message_id.strip("<>")]
        row = (await db.execute(
            select(CampaignMessage).where(
                CampaignMessage.provider_message_id.in_(candidates)
            )
        )).scalars().first()
        if row is not None:
            return row
    return None


async def record(
    db: AsyncSession,
    *,
    dedupe_key: str,
    email: str,
    event_type: EventType,
    tier: EventTier,
    occurred_at: datetime | None = None,
    classification: str = "",
    payload: dict | None = None,
    campaign_message_id=None,
) -> EmailEvent | None:
    """Insert one event, or return None if it is already recorded.

    Checked first with a SELECT and guarded second by the unique constraint,
    inside a savepoint. The SELECT handles the ordinary case cheaply; the
    savepoint means that when two copies of the same webhook arrive at once,
    the loser rolls back its own insert instead of poisoning the whole
    transaction and taking the suppression write down with it.
    """
    existing = (await db.execute(
        select(EmailEvent).where(EmailEvent.dedupe_key == dedupe_key)
    )).scalar_one_or_none()
    if existing is not None:
        return None

    row = EmailEvent(
        campaign_message_id=campaign_message_id,
        email=suppression_service.normalize(email),
        type=event_type,
        tier=tier,
        occurred_at=occurred_at or datetime.now(timezone.utc),
        dedupe_key=dedupe_key,
        classification=classification,
        payload=payload or {},
    )
    try:
        async with db.begin_nested():
            db.add(row)
    except IntegrityError:
        logger.info("duplicate event ignored: %s", dedupe_key)
        return None
    return row


async def ingest_mailgun_event(db: AsyncSession, event: dict, *, dedupe_key: str) -> bool:
    """Record one Mailgun event and apply its side effects.

    Returns True when something was written. Does not commit; the router owns
    the transaction so the event row and any suppression it causes land
    together or not at all.
    """
    classified = classify_mailgun(event)
    if classified is None:
        logger.info("ignoring unrecognised Mailgun event: %s", event.get("event"))
        return False

    event_type, tier = classified
    email = recipient_of(event)
    if not email:
        logger.warning("Mailgun event with no recipient: %s", dedupe_key)
        return False

    message = await find_message(db, event)
    written = await record(
        db,
        dedupe_key=dedupe_key,
        email=email,
        event_type=event_type,
        tier=tier,
        occurred_at=occurred_at_of(event),
        classification="provider-webhook",
        payload=_slim(event),
        campaign_message_id=message.id if message else None,
    )
    if written is None:
        return False

    reason = SUPPRESSING_EVENTS.get(event_type)
    if reason is not None:
        # Idempotent, so a repeated complaint is harmless. Runs even when the
        # event could not be matched to a message: someone who pressed the
        # spam button must stop receiving mail whether or not we can work out
        # which campaign upset them.
        await suppression_service.suppress(
            db, email=email, reason=reason,
            note=f"Mailgun {event.get('event')} event {event.get('id', '')}".strip(),
        )
    return True


# Fields worth keeping from a Mailgun event. The full body is large and mostly
# routing detail; these are what a human looks at when asking why a message
# bounced, plus the client and geo data that later reclassification would need.
_KEEP = (
    "event", "id", "severity", "reason", "recipient-domain",
    "delivery-status", "client-info", "geolocation", "tags",
)


def _slim(event: dict) -> dict:
    return {k: event[k] for k in _KEEP if k in event}
