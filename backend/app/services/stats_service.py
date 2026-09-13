"""Turning stored events into the numbers the dashboard shows.

Every figure that leaves this module carries its tier, and the inferred ones
are split into what is probably a machine and what might be a person. That
split is the product. A single "open rate" would be about half automatic
prefetch and would be worse than showing nothing, because a number with a
percent sign next to it gets believed.

Nothing here promotes an event to a better tier. Corroboration is reported
alongside — a click that a beacon confirmed is counted separately — rather
than by relabelling the underlying row, so the audit trail survives.
"""
import math
import uuid
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignStatus
from app.models.campaign_message import CampaignMessage
from app.models.email_event import EmailEvent, EventTier, EventType
from app.services import classifier
from app.services.campaign_service import HOLDOUT

# Below these the arithmetic is theatre. A two-proportion test on twenty
# recipients can produce a confident-looking p-value from what is really one
# person's behaviour, and reporting it would be the same dishonesty the tier
# system exists to avoid.
MIN_GROUP_FOR_SIGNIFICANCE = 30
MIN_EVENTS_FOR_SIGNIFICANCE = 5
SIGNIFICANCE_THRESHOLD = 0.05

# A send-time recommendation drawn from a handful of interactions is noise
# wearing a suit.
MIN_ENGAGEMENTS_FOR_SEND_TIME = 20


# --- significance -------------------------------------------------------------


def _normal_cdf(z: float) -> float:
    """Standard normal CDF via the error function.

    `math.erf` is exact enough for a p-value and costs no dependency; pulling
    in SciPy to do this one thing would add tens of megabytes to an image that
    otherwise has none of it.
    """
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def two_proportion_p_value(x1: int, n1: int, x2: int, n2: int) -> float | None:
    """Two-sided p-value for the difference between two rates.

    Returns None when the inputs cannot support a test at all — an empty
    group, or a pooled rate of zero or one, where the standard error is zero
    and the arithmetic would divide by it.
    """
    if n1 <= 0 or n2 <= 0:
        return None
    p1, p2 = x1 / n1, x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    if pooled <= 0.0 or pooled >= 1.0:
        return None
    se = math.sqrt(pooled * (1.0 - pooled) * (1.0 / n1 + 1.0 / n2))
    if se == 0.0:
        return None
    z = (p1 - p2) / se
    return 2.0 * (1.0 - _normal_cdf(abs(z)))


def ab_verdict(x1: int, n1: int, x2: int, n2: int) -> dict:
    """A plain-language answer, and the reason for it.

    Deliberately refuses to name a winner on a small list. "B looks better"
    from eleven clicks against nine is a coin toss described confidently, and
    acting on it is worse than not testing at all.
    """
    if min(n1, n2) < MIN_GROUP_FOR_SIGNIFICANCE:
        return {
            "p_value": None,
            "significant": False,
            "verdict": (
                f"Not enough recipients to tell. Each variant needs about "
                f"{MIN_GROUP_FOR_SIGNIFICANCE} before a difference means anything."
            ),
        }
    if (x1 + x2) < MIN_EVENTS_FOR_SIGNIFICANCE:
        return {
            "p_value": None,
            "significant": False,
            "verdict": "Not enough engagement yet to compare the two.",
        }

    p = two_proportion_p_value(x1, n1, x2, n2)
    if p is None:
        return {"p_value": None, "significant": False,
                "verdict": "The two variants cannot be compared yet."}

    r1, r2 = x1 / n1, x2 / n2
    if p > SIGNIFICANCE_THRESHOLD:
        return {
            "p_value": round(p, 4),
            "significant": False,
            "verdict": (
                f"No real difference. A gap this size would happen by chance "
                f"about {round(p * 100)} times in 100."
            ),
        }
    better = "A" if r1 > r2 else "B"
    return {
        "p_value": round(p, 4),
        "significant": True,
        "verdict": (
            f"Variant {better} really did better "
            f"({r1 * 100:.1f}% against {r2 * 100:.1f}%)."
        ),
    }


# --- per-campaign -------------------------------------------------------------


def _split_by_machine(rows: list[tuple[str, int]]) -> dict:
    """Split a classification/count list into machine and possibly-human.

    Uses the stored classification rather than re-running the rules, so a
    later change to the classifier never silently rewrites history. What a
    figure meant when it was recorded is what it keeps meaning.
    """
    machine = Counter()
    other = Counter()
    for classification, count in rows:
        target = machine if classifier.is_machine(classification or "") else other
        target[classification or "unclassified"] += count
    return {
        "recorded": sum(machine.values()) + sum(other.values()),
        "machine": sum(machine.values()),
        "possibly_human": sum(other.values()),
        "machine_breakdown": dict(machine.most_common()),
        "other_breakdown": dict(other.most_common()),
    }


async def _classification_counts(
    db: AsyncSession, campaign_id: uuid.UUID, event_type: EventType,
) -> list[tuple[str, int]]:
    return list((await db.execute(
        select(EmailEvent.classification, func.count(EmailEvent.id))
        .join(CampaignMessage, EmailEvent.campaign_message_id == CampaignMessage.id)
        .where(
            CampaignMessage.campaign_id == campaign_id,
            EmailEvent.type == event_type,
        )
        .group_by(EmailEvent.classification)
    )).all())


async def _type_counts(db: AsyncSession, campaign_id: uuid.UUID) -> dict[EventType, int]:
    rows = (await db.execute(
        select(EmailEvent.type, func.count(EmailEvent.id))
        .join(CampaignMessage, EmailEvent.campaign_message_id == CampaignMessage.id)
        .where(CampaignMessage.campaign_id == campaign_id)
        .group_by(EmailEvent.type)
    )).all()
    return {t: c for t, c in rows}


async def _distinct_messages_with(
    db: AsyncSession, campaign_id: uuid.UUID, event_type: EventType,
) -> int:
    """Unique recipients, not raw events. A person who opens a message four
    times is one person, and the two figures answer different questions."""
    return (await db.execute(
        select(func.count(func.distinct(EmailEvent.campaign_message_id)))
        .join(CampaignMessage, EmailEvent.campaign_message_id == CampaignMessage.id)
        .where(
            CampaignMessage.campaign_id == campaign_id,
            EmailEvent.type == event_type,
        )
    )).scalar() or 0


async def _message_totals(db: AsyncSession, campaign_id: uuid.UUID) -> dict:
    row = (await db.execute(
        select(
            func.count(CampaignMessage.id),
            func.count(CampaignMessage.sent_at),
            func.count(CampaignMessage.id).filter(CampaignMessage.variant == HOLDOUT),
            func.count(CampaignMessage.id).filter(CampaignMessage.send_error != ""),
            func.count(CampaignMessage.id).filter(CampaignMessage.pixel_embedded.is_(True)),
        ).where(CampaignMessage.campaign_id == campaign_id)
    )).one()
    return {
        "messages": row[0], "sent": row[1], "holdout": row[2],
        "failed": row[3], "trackable": row[4],
    }


async def _per_link(db: AsyncSession, campaign: Campaign) -> list[dict]:
    """Clicks per destination, machine ones separated.

    Which link people actually used is the most directly actionable thing on
    the page, and it is worthless if scanner sweeps are mixed in.
    """
    rows = (await db.execute(
        select(EmailEvent.payload, EmailEvent.classification)
        .join(CampaignMessage, EmailEvent.campaign_message_id == CampaignMessage.id)
        .where(
            CampaignMessage.campaign_id == campaign.id,
            EmailEvent.type == EventType.clicked,
        )
    )).all()

    totals: dict[int, dict] = {}
    for payload, classification in rows:
        if not isinstance(payload, dict):
            continue
        index = payload.get("link_index")
        if index is None:
            continue
        bucket = totals.setdefault(int(index), {"clicks": 0, "machine": 0})
        bucket["clicks"] += 1
        if classifier.is_machine(classification or ""):
            bucket["machine"] += 1

    links = list(campaign.links or [])
    return [
        {
            "index": i,
            "url": links[i] if i < len(links) else "(link no longer in the campaign)",
            "clicks": data["clicks"],
            "machine": data["machine"],
            "possibly_human": data["clicks"] - data["machine"],
        }
        for i, data in sorted(totals.items())
    ]


async def _conversions(db: AsyncSession, campaign_id: uuid.UUID) -> dict:
    rows = (await db.execute(
        select(EmailEvent.payload)
        .join(CampaignMessage, EmailEvent.campaign_message_id == CampaignMessage.id)
        .where(
            CampaignMessage.campaign_id == campaign_id,
            EmailEvent.type == EventType.converted,
        )
    )).scalars().all()
    names = Counter(
        str(p.get("name", "unnamed")) for p in rows if isinstance(p, dict)
    )
    return {"total": sum(names.values()), "by_name": dict(names.most_common())}


async def _variant_split(db: AsyncSession, campaign_id: uuid.UUID) -> dict:
    """Sent count and verified engagement per variant.

    The test runs on verified clicks rather than opens. A subject line is
    supposed to influence opens, but opens are the least trustworthy number in
    the system — testing on them would measure which subject Apple's prefetch
    preferred.
    """
    sent = dict((await db.execute(
        select(CampaignMessage.variant, func.count(CampaignMessage.id))
        .where(
            CampaignMessage.campaign_id == campaign_id,
            CampaignMessage.sent_at.isnot(None),
        )
        .group_by(CampaignMessage.variant)
    )).all())

    confirmed = dict((await db.execute(
        select(CampaignMessage.variant, func.count(func.distinct(CampaignMessage.id)))
        .join(EmailEvent, EmailEvent.campaign_message_id == CampaignMessage.id)
        .where(
            CampaignMessage.campaign_id == campaign_id,
            EmailEvent.type == EventType.page_confirmed,
        )
        .group_by(CampaignMessage.variant)
    )).all())

    return {
        "a": {"sent": sent.get("a", 0), "verified_clicks": confirmed.get("a", 0)},
        "b": {"sent": sent.get("b", 0), "verified_clicks": confirmed.get("b", 0)},
    }


async def campaign_scorecard(db: AsyncSession, campaign: Campaign) -> dict:
    """Everything the campaign page shows, in one call."""
    totals = await _message_totals(db, campaign.id)
    by_type = await _type_counts(db, campaign.id)

    opens = _split_by_machine(
        await _classification_counts(db, campaign.id, EventType.opened)
    )
    opens["unique_recipients"] = await _distinct_messages_with(
        db, campaign.id, EventType.opened
    )
    # How many messages even carried a pixel. Without this an open rate is a
    # fraction with the wrong denominator: contacts who never consented to
    # tracking were never measurable and should not count against it.
    opens["measurable"] = totals["trackable"]
    opens["not_measurable"] = totals["sent"] - totals["trackable"]

    clicks = _split_by_machine(
        await _classification_counts(db, campaign.id, EventType.clicked)
    )
    clicks["unique_recipients"] = await _distinct_messages_with(
        db, campaign.id, EventType.clicked
    )
    clicks["verified_recipients"] = await _distinct_messages_with(
        db, campaign.id, EventType.page_confirmed
    )

    variants = await _variant_split(db, campaign.id)
    ab = None
    if (campaign.variant_b_subject or "").strip():
        ab = {
            **variants,
            "metric": "verified clicks",
            **ab_verdict(
                variants["a"]["verified_clicks"], variants["a"]["sent"],
                variants["b"]["verified_clicks"], variants["b"]["sent"],
            ),
        }

    return {
        "campaign": {
            "id": str(campaign.id),
            "name": campaign.name,
            "subject": campaign.subject,
            "status": campaign.status.value,
            "segment": campaign.segment,
            "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None,
            "holdout_percent": campaign.holdout_percent,
        },
        # Exact tier: the mail system told us. These cannot be wrong.
        "delivery": {
            **totals,
            "delivered": by_type.get(EventType.delivered, 0),
            "soft_bounced": by_type.get(EventType.soft_bounced, 0),
            "hard_bounced": by_type.get(EventType.hard_bounced, 0),
            "complained": by_type.get(EventType.complained, 0),
            "unsubscribed": by_type.get(EventType.unsubscribed, 0),
        },
        "opens": opens,
        "clicks": clicks,
        "links": await _per_link(db, campaign),
        # Verified tier: a person wrote something, or a browser ran a script.
        "replies": {
            "total": by_type.get(EventType.replied, 0),
            "auto_replies": by_type.get(EventType.auto_replied, 0),
        },
        "conversions": await _conversions(db, campaign.id),
        "ab": ab,
    }


# --- across campaigns ---------------------------------------------------------


async def overview(db: AsyncSession, *, limit: int = 10) -> dict:
    """Headline figures and the recent campaigns, for the landing view."""
    campaigns = list((await db.execute(
        select(Campaign).order_by(Campaign.created_at.desc()).limit(limit)
    )).scalars().all())

    totals = (await db.execute(
        select(
            func.count(CampaignMessage.id),
            func.count(CampaignMessage.sent_at),
        )
    )).one()

    verified = (await db.execute(
        select(func.count(func.distinct(EmailEvent.campaign_message_id)))
        .where(EmailEvent.tier == EventTier.verified)
    )).scalar() or 0

    complained = (await db.execute(
        select(func.count(EmailEvent.id)).where(EmailEvent.type == EventType.complained)
    )).scalar() or 0

    sent = totals[1] or 0
    return {
        "campaigns_total": (await db.execute(
            select(func.count(Campaign.id))
        )).scalar() or 0,
        "campaigns_sent": (await db.execute(
            select(func.count(Campaign.id)).where(Campaign.status == CampaignStatus.sent)
        )).scalar() or 0,
        "messages": totals[0] or 0,
        "sent": sent,
        "verified_engagement": verified,
        "complaints": complained,
        # The number that gets a domain blocked. Providers act at 0.3% and
        # prefer under 0.1%, so it belongs on the front page rather than
        # buried in a trust screen nobody opens.
        "complaint_rate": round(complained / sent, 5) if sent else None,
        "recent": [
            {
                "id": str(c.id), "name": c.name, "status": c.status.value,
                "segment": c.segment,
                "sent_at": c.sent_at.isoformat() if c.sent_at else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in campaigns
        ],
    }


async def send_time_recommendation(db: AsyncSession) -> dict:
    """When verified engagement actually happens, by weekday and hour.

    Verified events only. Building this from inferred opens would recommend
    whenever Apple's servers happen to prefetch, which is not a fact about
    the audience at all.
    """
    rows = (await db.execute(
        select(EmailEvent.occurred_at).where(EmailEvent.tier == EventTier.verified)
    )).scalars().all()

    if len(rows) < MIN_ENGAGEMENTS_FOR_SEND_TIME:
        return {
            "enough_data": False,
            "observations": len(rows),
            "needed": MIN_ENGAGEMENTS_FOR_SEND_TIME,
            "note": (
                "Not enough confirmed engagement yet to suggest a send time. "
                "A recommendation from a handful of interactions is noise."
            ),
        }

    by_hour = Counter(dt.hour for dt in rows)
    by_weekday = Counter(dt.strftime("%A") for dt in rows)
    return {
        "enough_data": True,
        "observations": len(rows),
        "best_hour_utc": by_hour.most_common(1)[0][0],
        "best_weekday": by_weekday.most_common(1)[0][0],
        "by_hour": {str(h): c for h, c in sorted(by_hour.items())},
        "by_weekday": dict(by_weekday.most_common()),
    }
