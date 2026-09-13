"""Expanding a campaign into per-recipient messages, and sending them.

The two operations are deliberately separate. Expansion decides *who* gets
mail and is cheap, deterministic and repeatable; sending puts messages on the
wire and is slow and failure-prone. Keeping them apart means a send that dies
half way can be resumed without recomputing the audience, and the audience can
be inspected before a single message leaves.

Both are idempotent. That is the property that makes a crashed worker safe to
re-run: expansion skips contacts that already have a message row, and the send
loop skips messages that already have a `sent_at`. Without it, a restart at
the wrong moment mails the list twice.
"""
import hashlib
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignStatus
from app.models.campaign_message import CampaignMessage
from app.models.contact import ConsentBasis, Contact, ContactStatus
from app.models.email_event import EmailEvent, EventTier, EventType
from app.models.sender_settings import SenderSettings
from app.services import render_service, suppression_service
from app.services.senders.base import OutboundMessage, Sender, SenderError

logger = logging.getLogger(__name__)

# Segment names that mean "everyone eligible" rather than a tag to match.
ALL_SEGMENTS = {"", "all", "*"}

HOLDOUT = "holdout"


# --- audience ----------------------------------------------------------------


async def resolve_audience(db: AsyncSession, campaign: Campaign) -> list[Contact]:
    """Every contact eligible for this campaign, right now.

    Three gates, in order of authority:

    1. `status` is active — excludes anyone unsubscribed, bounced or retired.
    2. `consent_basis` is established — an imported row defaults to `unknown`
       and is never mailed until someone records how the person came to be on
       the list.
    3. The address is not suppressed — checked last because suppression
       outranks everything on the contact row, including a consent basis
       recorded later by mistake.

    Resolved at send time rather than when the campaign was drafted, so
    someone who unsubscribed yesterday is not mailed by a campaign written
    last week.
    """
    conditions = [
        Contact.status == ContactStatus.active,
        Contact.consent_basis != ConsentBasis.unknown,
    ]
    segment = (campaign.segment or "").strip().lower()
    if segment not in ALL_SEGMENTS:
        # Postgres array containment: the contact carries this tag.
        conditions.append(Contact.tags.any(segment))

    rows = (await db.execute(
        select(Contact).where(and_(*conditions)).order_by(Contact.email)
    )).scalars().all()

    suppressed = await suppression_service.filter_suppressed(
        db, [c.email for c in rows]
    )
    if suppressed:
        logger.info(
            "campaign %s: %d of %d contacts suppressed",
            campaign.id, len(suppressed), len(rows),
        )
    return [
        c for c in rows
        if suppression_service.normalize(c.email) not in suppressed
    ]


# --- variant assignment ------------------------------------------------------


def _bucket(salt: str, campaign_id: uuid.UUID, contact_id: uuid.UUID) -> int:
    """A stable 0-99 bucket for one contact in one campaign.

    Deterministic rather than random so re-expanding a campaign puts everyone
    in the same group they were in the first time. A random draw would
    reshuffle the holdout on every resume, which destroys the comparison the
    holdout exists to provide.

    The salt keeps the holdout cut and the A/B split independent. Deriving
    both from one hash would correlate them, so the B variant would
    systematically over-represent one end of the holdout boundary.
    """
    digest = hashlib.sha256(f"{salt}:{campaign_id}:{contact_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % 100


def assign_variant(campaign: Campaign, contact: Contact) -> str:
    """"holdout", "a" or "b"."""
    holdout = max(0, min(100, campaign.holdout_percent or 0))
    if holdout and _bucket("holdout", campaign.id, contact.id) < holdout:
        return HOLDOUT
    if (campaign.variant_b_subject or "").strip():
        return "a" if _bucket("variant", campaign.id, contact.id) < 50 else "b"
    return "a"


def subject_for(campaign: Campaign, variant: str) -> str:
    if variant == "b" and (campaign.variant_b_subject or "").strip():
        return campaign.variant_b_subject
    return campaign.subject or ""


# --- expansion ---------------------------------------------------------------


async def expand(db: AsyncSession, campaign: Campaign) -> int:
    """Create a CampaignMessage per eligible contact. Returns how many were
    created this call.

    Idempotent: contacts that already have a row for this campaign are
    skipped, so calling it again after a crash tops up rather than duplicates.
    Does not commit — the caller owns the transaction.
    """
    # Frozen on first expansion and never recomputed: a click URL carries only
    # an index into this list, and re-numbering it after any mail has gone out
    # would silently point old links at the wrong destinations.
    if not campaign.links:
        campaign.links = render_service.body_links(campaign)

    audience = await resolve_audience(db, campaign)
    if not audience:
        return 0

    existing = set((await db.execute(
        select(CampaignMessage.contact_id).where(
            CampaignMessage.campaign_id == campaign.id
        )
    )).scalars().all())

    created = 0
    for contact in audience:
        if contact.id in existing:
            continue
        db.add(CampaignMessage(
            campaign_id=campaign.id,
            contact_id=contact.id,
            email=suppression_service.normalize(contact.email),
            variant=assign_variant(campaign, contact),
        ))
        created += 1
    return created


# --- sending -----------------------------------------------------------------


async def pending_messages(db: AsyncSession, campaign: Campaign) -> list[CampaignMessage]:
    """Messages still to send.

    Excludes three groups, each for a different reason: holdouts are never
    sent by design, anything with a `sent_at` already went out, and anything
    carrying a `send_error` failed permanently and retrying it would jam the
    queue on a message that can never leave.
    """
    return list((await db.execute(
        select(CampaignMessage).where(and_(
            CampaignMessage.campaign_id == campaign.id,
            CampaignMessage.sent_at.is_(None),
            CampaignMessage.send_error == "",
            CampaignMessage.variant != HOLDOUT,
        )).order_by(CampaignMessage.created_at)
    )).scalars().all())


def build_outbound(
    *,
    campaign: Campaign,
    contact: Contact,
    message: CampaignMessage,
    settings: SenderSettings,
) -> OutboundMessage:
    """One fully rendered message. The sender never edits what comes out of
    here, so two providers produce identical mail from the same campaign."""
    unsubscribe = render_service.unsubscribe_url(settings.tracking_base_url, message.token)
    headers = render_service.list_unsubscribe_headers(unsubscribe)

    reply_to = ""
    if settings.reply_domain:
        # Plus-tagged with the message token, so an inbound reply identifies
        # its campaign and recipient without parsing the body.
        reply_to = f"replies+{message.token}@{settings.reply_domain}"

    # Decided per recipient, never per campaign. A contact outside the US who
    # has not consented to open tracking gets the same message with no pixel.
    embed_pixel = contact.may_track_opens
    tracking = {
        "links": list(campaign.links or []),
        "tracking_base_url": settings.tracking_base_url,
        "token": message.token,
    }

    return OutboundMessage(
        to_email=message.email,
        to_name=contact.full_name or "",
        subject=subject_for(campaign, message.variant),
        text_body=render_service.render_text(
            campaign, contact,
            unsubscribe=unsubscribe, postal=settings.postal_address, **tracking,
        ),
        html_body=render_service.render_html(
            campaign, contact,
            unsubscribe=unsubscribe, postal=settings.postal_address,
            embed_pixel=embed_pixel, **tracking,
        ),
        from_email=settings.from_email,
        from_name=settings.from_name,
        reply_to=reply_to,
        headers=headers,
        # Echoed back on every webhook for this message, which is how a
        # delivery or bounce event finds this row.
        variables={"message_token": message.token, "campaign_id": str(campaign.id)},
        tags=[f"campaign-{campaign.id}", f"variant-{message.variant}"],
    )


async def send_pending(
    db: AsyncSession,
    campaign: Campaign,
    sender: Sender,
    settings: SenderSettings,
) -> tuple[int, int]:
    """Send everything outstanding for this campaign. Returns (sent, failed).

    Serial on purpose. A few hundred recipients at a couple of hundred
    milliseconds each is about a minute, and a burst of concurrent sends buys
    little while making rate-limit handling and partial-failure accounting
    much harder to reason about.

    Commits per message rather than once at the end: a crash then loses at
    most the message in flight, instead of replaying the whole batch and
    mailing everyone a second time.
    """
    messages = await pending_messages(db, campaign)
    if not messages:
        return 0, 0

    contacts = {
        c.id: c for c in (await db.execute(
            select(Contact).where(
                Contact.id.in_([m.contact_id for m in messages])
            )
        )).scalars().all()
    }

    sent = failed = 0
    for message in messages:
        contact = contacts.get(message.contact_id)
        if contact is None:
            # The contact was deleted between expansion and send. Not an
            # error worth failing the campaign over, but the message can
            # never go out, so retire it rather than retrying forever.
            message.send_error = "Contact no longer exists."
            await db.commit()
            failed += 1
            continue

        try:
            result = await sender.send(build_outbound(
                campaign=campaign, contact=contact, message=message, settings=settings,
            ))
        except SenderError as exc:
            if exc.retryable:
                # Left pending on purpose: the next worker run picks it up.
                logger.warning("campaign %s message %s deferred: %s", campaign.id, message.id, exc)
                failed += 1
                continue
            message.send_error = str(exc)[:2000]
            await db.commit()
            failed += 1
            continue

        message.provider_message_id = result.provider_message_id
        message.sent_at = datetime.now(timezone.utc)
        # Recorded as a historical fact about THIS message. A contact's
        # tracking consent can change later, and an open rate must still be
        # able to say honestly how much of the audience was measurable at the
        # time it was sent.
        message.pixel_embedded = contact.may_track_opens
        db.add(EmailEvent(
            campaign_message_id=message.id,
            email=message.email,
            type=EventType.accepted,
            # The provider took the message. That is a fact about the mail
            # system, not an inference about a person — but it is NOT
            # delivery, which only a webhook can confirm.
            tier=EventTier.exact,
            dedupe_key=f"accepted:{message.token}",
            classification="sender-accepted",
            payload={"provider": sender.name, "provider_message_id": result.provider_message_id},
        ))
        await db.commit()
        sent += 1

    return sent, failed


# --- status transitions ------------------------------------------------------


async def claim_for_sending(db: AsyncSession, campaign_id: uuid.UUID) -> Campaign | None:
    """Take exclusive ownership of a campaign, or return None if another
    worker already has it.

    `FOR UPDATE SKIP LOCKED` is what makes it safe to run the worker on a
    timer without checking whether the previous run is still going: a second
    worker skips a locked row instead of blocking on it or, worse, sending
    the same campaign alongside the first.
    """
    campaign = (await db.execute(
        select(Campaign)
        .where(and_(
            Campaign.id == campaign_id,
            or_(
                Campaign.status == CampaignStatus.scheduled,
                Campaign.status == CampaignStatus.sending,
            ),
        ))
        .with_for_update(skip_locked=True)
    )).scalar_one_or_none()

    if campaign is None:
        return None
    campaign.status = CampaignStatus.sending
    return campaign


async def audience_breakdown(db: AsyncSession, campaign: Campaign) -> dict:
    """What a send would do, without doing it.

    Reports the gap between "contacts carrying this tag" and "people who will
    actually receive this", broken down by why each group falls out. An admin
    who queues a campaign to 300 contacts and sees 240 delivered should be
    able to find the other 60 here beforehand, not afterwards.
    """
    segment = (campaign.segment or "").strip().lower()
    in_segment_query = select(Contact)
    if segment not in ALL_SEGMENTS:
        in_segment_query = in_segment_query.where(Contact.tags.any(segment))
    in_segment = (await db.execute(in_segment_query)).scalars().all()

    # The exclusion buckets are mutually exclusive and, with `eligible`, add up
    # to `total_contacts`. That property is the point of this function: an
    # admin who queues to 300 contacts and sees 240 sent has to be able to
    # account for the other 60 here. Overlapping categories — a contact who is
    # both suppressed and marked unsubscribed being counted twice, or neither —
    # would make the numbers unreconcilable and the preview useless.
    suppressed_set = await suppression_service.filter_suppressed(
        db, [c.email for c in in_segment]
    )
    suppressed, rest = [], []
    for contact in in_segment:
        if suppression_service.normalize(contact.email) in suppressed_set:
            suppressed.append(contact)
        else:
            rest.append(contact)

    inactive = [c for c in rest if c.status != ContactStatus.active]
    active = [c for c in rest if c.status == ContactStatus.active]
    no_consent = [c for c in active if c.consent_basis == ConsentBasis.unknown]

    eligible = await resolve_audience(db, campaign)
    variants = [assign_variant(campaign, c) for c in eligible]

    return {
        "total_contacts": len(in_segment),
        "eligible": len(eligible),
        "suppressed": len(suppressed),
        "excluded_inactive": len(inactive),
        "excluded_no_consent": len(no_consent),
        "holdout": variants.count(HOLDOUT),
        "variant_a": variants.count("a"),
        "variant_b": variants.count("b"),
        "untrackable": sum(1 for c in eligible if not c.may_track_opens),
        "eligible_contacts": eligible,
        "variants": variants,
    }


async def due_campaign_ids(db: AsyncSession) -> list[uuid.UUID]:
    """Campaigns the worker should pick up: scheduled and due, plus anything
    left in `sending` by a run that died before finishing."""
    now = datetime.now(timezone.utc)
    return list((await db.execute(
        select(Campaign.id).where(or_(
            and_(
                Campaign.status == CampaignStatus.scheduled,
                or_(Campaign.scheduled_for.is_(None), Campaign.scheduled_for <= now),
            ),
            Campaign.status == CampaignStatus.sending,
        )).order_by(Campaign.created_at)
    )).scalars().all())
