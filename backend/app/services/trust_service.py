"""The domain's standing, on one screen.

Answers four questions an admin should be able to check in a glance each
morning: is anything sending as us that should not be, are we listed anywhere,
where is our mail actually landing, and are complaints anywhere near the line
that gets a sender blocked.

Deliberately does NOT include Google Postmaster Tools. Its API needs a service
account and domain-wide delegation to set up, and Google shows no data below
roughly a few hundred messages a day to Gmail — which is far above what this
company sends. Building an OAuth integration to display an empty panel would
be work that looks like progress. The DMARC reports and the seed inboxes below
answer the same questions and do work at this volume. Revisit it if the list
grows an order of magnitude.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.campaign_message import CampaignMessage
from app.models.email_event import EmailEvent, EventType
from app.models.trust import (
    BlocklistResult, DmarcRecord, Placement, SeedInbox, SeedPlacement,
)

# What providers act on. They enforce at 0.3% and prefer under 0.1%; on a list
# of a few hundred a single complaint can cross the first line, which is why
# the raw count matters as much as the rate here.
COMPLAINT_ENFORCEMENT_RATE = 0.003
COMPLAINT_TARGET_RATE = 0.001

DMARC_WINDOW_DAYS = 30


async def dmarc_summary(db: AsyncSession, *, days: int = DMARC_WINDOW_DAYS) -> dict:
    """Every source that sent as the domain recently, and how it did.

    Grouped by source address rather than listed per report, because the
    question is always "what is this server and why is it failing". A source
    at 100% is a system to leave alone; anything below it is either a
    forwarder, a legitimate sender nobody has authorised yet, or someone
    forging the domain — and the three are told apart by looking at what the
    address belongs to.
    """
    since = (datetime.now(timezone.utc) - timedelta(days=days)).date()
    rows = list((await db.execute(
        select(DmarcRecord).where(DmarcRecord.date_begin >= since)
    )).scalars().all())

    if not rows:
        return {
            "has_data": False,
            "window_days": days,
            "note": (
                "No DMARC reports yet. They start arriving within about 48 hours "
                "of pointing the domain's rua address at a mailbox this system "
                "can read."
            ),
            "sources": [], "totals": {},
        }

    grouped: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"messages": 0, "passing": 0, "dkim_domains": set(), "spf_domains": set(),
                 "org_names": set(), "policies": set()}
    )
    for r in rows:
        key = (r.source_ip, r.header_from)
        g = grouped[key]
        g["messages"] += r.count
        if r.passed:
            g["passing"] += r.count
        if r.dkim_domain:
            g["dkim_domains"].add(r.dkim_domain)
        if r.spf_domain:
            g["spf_domains"].add(r.spf_domain)
        if r.org_name:
            g["org_names"].add(r.org_name)
        if r.disposition:
            g["policies"].add(r.disposition)

    sources = []
    for (ip, header_from), g in grouped.items():
        messages = g["messages"]
        sources.append({
            "source_ip": ip,
            "header_from": header_from,
            "messages": messages,
            "passing": g["passing"],
            "failing": messages - g["passing"],
            "pass_rate": round(g["passing"] / messages, 4) if messages else 0.0,
            "dkim_domains": sorted(g["dkim_domains"]),
            "spf_domains": sorted(g["spf_domains"]),
            "reported_by": sorted(g["org_names"]),
            "dispositions": sorted(g["policies"]),
        })
    # Worst first: a failing source with volume behind it is the thing to look
    # at, and burying it under a list of healthy ones defeats the panel.
    sources.sort(key=lambda s: (s["pass_rate"], -s["messages"]))

    total = sum(s["messages"] for s in sources)
    passing = sum(s["passing"] for s in sources)
    failing_sources = [s for s in sources if s["failing"] > 0]

    return {
        "has_data": True,
        "window_days": days,
        "sources": sources,
        "totals": {
            "messages": total,
            "passing": passing,
            "failing": total - passing,
            "pass_rate": round(passing / total, 4) if total else 0.0,
            "sources": len(sources),
            "failing_sources": len(failing_sources),
        },
        # The gate on tightening the domain policy. Enforcing while any known
        # sender still fails is how a company stops receiving its own mail.
        "safe_to_enforce": total > 0 and not failing_sources,
    }


async def blocklist_summary(db: AsyncSession) -> dict:
    """The most recent result per target and list."""
    rows = list((await db.execute(
        select(BlocklistResult).order_by(BlocklistResult.checked_at.desc()).limit(200)
    )).scalars().all())

    latest: dict[tuple[str, str], BlocklistResult] = {}
    for r in rows:
        latest.setdefault((r.target, r.blocklist), r)

    checks = [
        {
            "target": r.target, "blocklist": r.blocklist, "listed": r.listed,
            "response": r.response, "checked_at": r.checked_at.isoformat(),
        }
        for r in sorted(latest.values(), key=lambda r: (not r.listed, r.target))
    ]
    return {
        "has_data": bool(checks),
        "checks": checks,
        "listed_count": sum(1 for c in checks if c["listed"]),
        "last_checked": max((r.checked_at for r in latest.values()), default=None),
    }


async def placement_summary(db: AsyncSession, *, limit: int = 5) -> dict:
    """Where the last few campaigns landed, per seed inbox."""
    inboxes = {
        i.id: i for i in (await db.execute(select(SeedInbox))).scalars().all()
    }
    if not inboxes:
        return {
            "has_data": False,
            "note": (
                "No seed inboxes configured. These are mailboxes the company owns "
                "that receive every campaign, and they are the only way to see a "
                "spam-folder placement before a client mentions it."
            ),
            "campaigns": [],
        }

    campaigns = list((await db.execute(
        select(Campaign)
        .where(Campaign.sent_at.isnot(None))
        .order_by(Campaign.sent_at.desc())
        .limit(limit)
    )).scalars().all())

    placements = defaultdict(list)
    for p in (await db.execute(
        select(SeedPlacement).where(
            SeedPlacement.campaign_id.in_([c.id for c in campaigns] or [None])
        )
    )).scalars().all():
        inbox = inboxes.get(p.seed_inbox_id)
        placements[p.campaign_id].append({
            "inbox": inbox.label or inbox.email if inbox else "unknown",
            "provider": inbox.provider if inbox else "",
            "placement": p.placement.value,
            "detail": p.detail,
        })

    return {
        "has_data": True,
        "inbox_count": len(inboxes),
        "campaigns": [
            {
                "id": str(c.id), "name": c.name,
                "sent_at": c.sent_at.isoformat() if c.sent_at else None,
                "results": placements.get(c.id, []),
            }
            for c in campaigns
        ],
    }


async def complaint_summary(db: AsyncSession) -> dict:
    sent = (await db.execute(
        select(func.count(CampaignMessage.sent_at))
    )).scalar() or 0
    complaints = (await db.execute(
        select(func.count(EmailEvent.id)).where(EmailEvent.type == EventType.complained)
    )).scalar() or 0
    hard_bounces = (await db.execute(
        select(func.count(EmailEvent.id)).where(EmailEvent.type == EventType.hard_bounced)
    )).scalar() or 0

    rate = complaints / sent if sent else None
    if rate is None:
        status = "unknown"
    elif rate >= COMPLAINT_ENFORCEMENT_RATE:
        status = "critical"
    elif rate >= COMPLAINT_TARGET_RATE:
        status = "warning"
    else:
        status = "good"

    return {
        "sent": sent,
        "complaints": complaints,
        "hard_bounces": hard_bounces,
        "rate": round(rate, 5) if rate is not None else None,
        "bounce_rate": round(hard_bounces / sent, 5) if sent else None,
        "status": status,
        "enforcement_rate": COMPLAINT_ENFORCEMENT_RATE,
        "target_rate": COMPLAINT_TARGET_RATE,
    }


async def panel(db: AsyncSession) -> dict:
    """Everything the trust screen shows."""
    return {
        "dmarc": await dmarc_summary(db),
        "blocklists": await blocklist_summary(db),
        "placement": await placement_summary(db),
        "complaints": await complaint_summary(db),
    }
