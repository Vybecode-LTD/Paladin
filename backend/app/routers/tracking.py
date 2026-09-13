"""Public tracking endpoints, served from the campaign subdomain.

Mounted at the ROOT, not under /api, and registered in main.py BEFORE the SPA
catch-all — exactly like routers/sitemap.py. These URLs live inside mail that
has already been sent and can never be changed afterwards, so they are kept
short and stable.

Three rules apply to everything here.

**No rate limiting.** The front proxy forwards no client address, so every
recipient appears as one IP and a shared bucket would start refusing real
unsubscribes and losing real events. There is nothing worth rate limiting
here anyway: the tokens are unguessable and the endpoints write one bounded
row each.

**Never show a recipient an error.** Someone who clicked a link in their mail
should land somewhere sensible whatever state the token is in. An unknown or
expired token gets a normal page or a redirect to the site, never a 404.

**Nothing here ever records `verified`, except the beacon.** A pixel fetch and
a redirect hit are both things a machine does perfectly. Only the beacon, which
requires JavaScript to have run, and a reply, which requires a person, produce
evidence a scanner cannot fake.
"""
import base64
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.campaign import Campaign
from app.models.campaign_message import CampaignMessage
from app.models.contact import Contact
from app.models.email_event import EmailEvent, EventTier, EventType
from app.models.suppression import SuppressionReason
from app.services import classifier, event_service, suppression_service

logger = logging.getLogger(__name__)

router = APIRouter()

# The smallest thing every mail client renders: a 43-byte transparent GIF.
PIXEL_GIF = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)

# Without these a proxy or client caches the pixel and the second open is
# never seen. Belt and braces because the three headers are honoured by
# different clients.
NO_STORE = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0, private",
    "Pragma": "no-cache",
    "Expires": "0",
}

_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Unsubscribed</title></head>
<body style="margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;background:#f4f7fb;color:#1a1c1f;">
<div style="max-width:520px;margin:12vh auto;padding:32px;background:#fff;border-radius:8px;">
<h1 style="font-size:22px;margin:0 0 12px;">{heading}</h1>
<p style="font-size:15px;line-height:1.55;color:#5c5e61;margin:0;">{body}</p>
</div></body></html>
"""


def _page(heading: str, body: str) -> HTMLResponse:
    return HTMLResponse(_PAGE.format(heading=heading, body=body))


def _pixel() -> Response:
    return Response(content=PIXEL_GIF, media_type="image/gif", headers=NO_STORE)


def _minute_bucket(when: datetime) -> str:
    """Collapses a burst of refetches into one event while still letting a
    genuine second open, minutes later, count as its own."""
    return when.strftime("%Y%m%d%H%M")


def _seconds_since_send(message: CampaignMessage, now: datetime) -> float | None:
    if message.sent_at is None:
        return None
    return (now - message.sent_at).total_seconds()


async def _message_for(db: AsyncSession, token: str) -> CampaignMessage | None:
    return (await db.execute(
        select(CampaignMessage).where(CampaignMessage.token == token)
    )).scalar_one_or_none()


async def _distinct_links_recently(
    db: AsyncSession, message: CampaignMessage, now: datetime,
) -> int:
    """How many different links in this message have been hit inside the sweep
    window. A security product walks every link in a message within seconds,
    which no person does, and which no user-agent check catches on a scanner
    that forwards the recipient's own browser string."""
    since = now.timestamp() - classifier.SWEEP_WINDOW_SECONDS
    rows = (await db.execute(
        select(EmailEvent.payload).where(
            EmailEvent.campaign_message_id == message.id,
            EmailEvent.type == EventType.clicked,
        )
    )).scalars().all()
    indices = {
        row.get("link_index")
        for row in rows
        if isinstance(row, dict)
        and row.get("link_index") is not None
        and float(row.get("at", 0) or 0) >= since
    }
    return len(indices)


async def _credit_engagement(db: AsyncSession, message: CampaignMessage) -> None:
    """Verified engagement only. Inferred opens never touch this, which is
    what keeps the engagement score from being half machine traffic and the
    automatic retirement of quiet contacts from being driven by noise."""
    contact = await db.get(Contact, message.contact_id)
    if contact is None:
        return
    contact.engagement_score = (contact.engagement_score or 0) + 1
    contact.last_engaged_at = datetime.now(timezone.utc)
    contact.consecutive_ignored = 0


# --- open pixel ---------------------------------------------------------------


@router.get("/t/o/{token}.png", include_in_schema=False)
async def open_pixel(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Records an open, always at inferred tier.

    Returns the image whatever happens. A recipient must never see a broken
    image because their token was unknown or the database was busy.
    """
    message = await _message_for(db, token)
    if message is None:
        return _pixel()

    now = datetime.now(timezone.utc)
    tier, classification = classifier.classify_open(
        user_agent=request.headers.get("user-agent"),
        seconds_since_send=_seconds_since_send(message, now),
    )
    try:
        await event_service.record(
            db,
            dedupe_key=f"open:{token}:{_minute_bucket(now)}",
            email=message.email,
            event_type=EventType.opened,
            tier=tier,
            occurred_at=now,
            classification=classification,
            payload={
                "user_agent": (request.headers.get("user-agent") or "")[:500],
                "at": now.timestamp(),
            },
            campaign_message_id=message.id,
        )
        await db.commit()
    except Exception:
        # An open is the least important signal in the system. Losing one is
        # not worth showing a recipient a broken image.
        logger.exception("failed to record open for %s", token)
        await db.rollback()
    return _pixel()


# --- click redirect -----------------------------------------------------------


@router.get("/t/c/{token}/{index}", include_in_schema=False)
async def click_redirect(
    token: str, index: int, request: Request, db: AsyncSession = Depends(get_db),
):
    """Records a click, always at inferred tier, then sends the visitor on.

    The destination is appended with the message token so the landing page's
    beacon can identify which message brought them — that beacon is what
    turns this inferred click into verified engagement.
    """
    fallback = RedirectResponse(url=settings.site_url, status_code=302)

    message = await _message_for(db, token)
    if message is None:
        return fallback

    campaign = await db.get(Campaign, message.campaign_id)
    links = list((campaign.links if campaign else None) or [])
    if index < 0 or index >= len(links):
        logger.info("click for out-of-range link index %s on %s", index, token)
        return fallback

    destination = links[index]
    if not destination.lower().startswith(("http://", "https://")):
        # The list comes from our own campaign body rather than from a
        # visitor, but a redirect endpoint should never be the thing that
        # trusts its input.
        return fallback

    now = datetime.now(timezone.utc)
    user_agent = request.headers.get("user-agent")
    try:
        tier, classification = classifier.classify_click(
            user_agent=user_agent,
            referer=request.headers.get("referer"),
            seconds_since_send=_seconds_since_send(message, now),
            distinct_links_recently=await _distinct_links_recently(db, message, now),
        )
        await event_service.record(
            db,
            dedupe_key=f"click:{token}:{index}:{_minute_bucket(now)}",
            email=message.email,
            event_type=EventType.clicked,
            tier=tier,
            occurred_at=now,
            classification=classification,
            payload={
                "link_index": index,
                "url": destination[:500],
                "user_agent": (user_agent or "")[:500],
                "referer": (request.headers.get("referer") or "")[:300],
                "at": now.timestamp(),
            },
            campaign_message_id=message.id,
        )
        await db.commit()
    except Exception:
        logger.exception("failed to record click for %s", token)
        await db.rollback()

    separator = "&" if "?" in destination else "?"
    return RedirectResponse(url=f"{destination}{separator}ab_t={token}", status_code=302)


# --- landing-page beacon ------------------------------------------------------


@router.get("/t/b/{token}", include_in_schema=False)
async def page_beacon(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """The one signal a scanner does not produce.

    Requested by a few lines of script on the landing page, so it only fires
    when a real browser rendered the page and ran JavaScript. Security
    products fetch the URL; they do not execute it. That difference is the
    whole basis for the verified tier.

    A plain image GET rather than a POST on purpose: no preflight, no CORS
    configuration to keep in step across two origins, and it works in every
    browser without a fetch polyfill.
    """
    message = await _message_for(db, token)
    if message is None:
        return _pixel()

    now = datetime.now(timezone.utc)
    try:
        written = await event_service.record(
            db,
            dedupe_key=f"beacon:{token}",
            email=message.email,
            event_type=EventType.page_confirmed,
            # The only place in the tracking path that produces this tier.
            tier=EventTier.verified,
            occurred_at=now,
            classification="beacon-confirmed",
            payload={
                "user_agent": (request.headers.get("user-agent") or "")[:500],
                "at": now.timestamp(),
            },
            campaign_message_id=message.id,
        )
        if written is not None:
            await _credit_engagement(db, message)
        await db.commit()
    except Exception:
        logger.exception("failed to record beacon for %s", token)
        await db.rollback()
    return _pixel()


# --- unsubscribe --------------------------------------------------------------


async def _unsubscribe(db: AsyncSession, token: str) -> bool:
    """Suppress the address behind this token. True if anything changed.

    Unknown tokens are ignored rather than raising: the token is opaque and
    unguessable, so a miss means an old or hand-edited link, and there is
    nothing useful to tell the person holding it.
    """
    message = await _message_for(db, token)
    if message is None:
        logger.info("unsubscribe for unknown token")
        return False

    await suppression_service.suppress(
        db,
        email=message.email,
        reason=SuppressionReason.unsubscribed,
        note=f"Unsubscribe link, campaign {message.campaign_id}",
    )
    db.add(EmailEvent(
        campaign_message_id=message.id,
        email=message.email,
        type=EventType.unsubscribed,
        # A person clicked a link in their own mail. Nothing infers this.
        tier=EventTier.verified,
        dedupe_key=f"unsub:{token}",
        classification="unsubscribe-link",
        payload={},
    ))
    await db.commit()
    return True


@router.post("/t/u/{token}", include_in_schema=False)
async def one_click_unsubscribe(token: str, db: AsyncSession = Depends(get_db)):
    """RFC 8058 one-click. This is the endpoint Gmail and Yahoo call from the
    unsubscribe control they render beside the sender name, with no human
    seeing a page. It must never require a confirmation step — a one-click
    flow that asks a question is treated as non-compliant."""
    await _unsubscribe(db, token)
    return {"unsubscribed": True}


@router.get("/t/u/{token}", include_in_schema=False)
async def unsubscribe_page(token: str, db: AsyncSession = Depends(get_db)):
    """The visible link in the footer. Same effect, with a page to confirm it
    worked."""
    await _unsubscribe(db, token)
    return _page(
        "You have been unsubscribed",
        "You will not receive any more marketing email from us. "
        "Replies to a real person and service messages about your account are "
        "not affected.",
    )
