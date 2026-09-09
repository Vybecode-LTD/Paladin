"""Campaign send worker. One pass, then exit.

Run from a systemd timer rather than as a long-lived process:

    python -m app.worker

That choice matches how this app is already deployed. The web app is a systemd
unit whose logs go to the journal, so a timer beside it needs no new tooling,
no queue broker, and no supervision the team does not already have — and a run
that crashes is visible with the same `journalctl` command they already use.
An in-process scheduler would share the web process's lifetime and hide its
failures inside it.

Safe to run on a short interval. If a previous pass is still going, this one
takes the advisory lock's refusal as its answer and exits immediately.
"""
import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.core.database import async_session, engine
from app.models.campaign import Campaign, CampaignStatus
from app.services import campaign_service, sender_service
from app.services.senders.base import SenderError

logger = logging.getLogger("paladin.worker")

# Arbitrary but fixed. Postgres advisory locks are a single global namespace
# per database, so this number just has to stay unique within this app.
WORKER_LOCK_KEY = 84712026

# The worker fires every minute for campaigns. These checks only need to
# happen daily, and a blocklist queried every sixty seconds will start
# refusing the queries.
BLOCKLIST_INTERVAL_HOURS = 12
# A message needs a moment to arrive and be filed before there is anything to
# look at in a seed inbox.
PLACEMENT_DELAY_MINUTES = 5
PLACEMENT_LOOKBACK_DAYS = 7


async def _process_campaign(db, campaign_id) -> dict:
    """Expand and send one campaign. Returns a small summary for the log."""
    campaign = await campaign_service.claim_for_sending(db, campaign_id)
    if campaign is None:
        # Someone else finished it, or it left a sendable state between the
        # listing query and now.
        return {"campaign": str(campaign_id), "skipped": True}
    await db.commit()

    try:
        sender = await sender_service.build_sender(db)
        settings = await sender_service.get_sender_settings(db)
    except SenderError as exc:
        # A configuration problem, not a transient one: every message in this
        # campaign would fail the same way, so stop rather than burn through
        # the list recording identical errors.
        campaign.status = CampaignStatus.failed
        campaign.error = str(exc)[:2000]
        await db.commit()
        logger.error("campaign %s failed: %s", campaign.id, exc)
        return {"campaign": str(campaign.id), "failed": True, "error": str(exc)}

    created = await campaign_service.expand(db, campaign)
    await db.commit()

    sent, failed = await campaign_service.send_pending(db, campaign, sender, settings)

    remaining = await campaign_service.pending_messages(db, campaign)
    if not remaining:
        campaign.status = CampaignStatus.sent
        campaign.sent_at = datetime.now(timezone.utc)
        campaign.error = ""
    else:
        # Retryable failures only — permanent ones carry a send_error and are
        # excluded from `pending`. Left in `sending` so the next pass picks it
        # up, with the count visible to whoever is watching.
        campaign.error = f"{len(remaining)} message(s) still pending after this run."
    await db.commit()

    logger.info(
        "campaign %s: expanded %d, sent %d, failed %d, pending %d",
        campaign.id, created, sent, failed, len(remaining),
    )
    return {
        "campaign": str(campaign.id),
        "expanded": created,
        "sent": sent,
        "failed": failed,
        "pending": len(remaining),
    }


async def _trust_maintenance(db) -> dict:
    """The daily reputation checks, and seed placement for recent sends.

    Rate-limited by looking at when the last check actually ran rather than by
    a separate timer unit. The worker fires every minute for campaigns; these
    only need to happen once a day, and a blocklist that is queried every
    sixty seconds will eventually refuse the queries.
    """
    from sqlalchemy import func, select

    from app.models.campaign import Campaign, CampaignStatus
    from app.models.trust import BlocklistResult, Placement, SeedInbox, SeedPlacement
    from app.services import blocklist_service, seed_service, sender_service

    out: dict = {}
    now = datetime.now(timezone.utc)

    last = (await db.execute(select(func.max(BlocklistResult.checked_at)))).scalar()
    if last is None or (now - last) > timedelta(hours=BLOCKLIST_INTERVAL_HOURS):
        settings = await sender_service.get_sender_settings(db)
        domains = sorted({
            d for d in [
                getattr(settings, "mailgun_domain", "") or "",
                getattr(settings, "reply_domain", "") or "",
            ] if d
        })
        if domains:
            results = await blocklist_service.check_all(domains=domains, ips=[])
            for r in results:
                db.add(BlocklistResult(
                    target=r["target"], blocklist=r["blocklist"],
                    listed=r["listed"], response=r["response"],
                ))
            await db.commit()
            out["blocklists_checked"] = len(results)
            listed = [r for r in results if r["listed"]]
            if listed:
                # Worth a loud line in the journal: this is the kind of thing
                # that otherwise surfaces as "some people stopped getting our
                # mail" a week later.
                logger.error("BLOCKLISTED: %s", listed)
            out["listed"] = len(listed)

    # Seed placement, for campaigns sent recently that have no result yet.
    # Delayed rather than immediate: a message needs a minute or two to arrive
    # and be filed before there is anything to look at.
    inboxes = list((await db.execute(
        select(SeedInbox).where(SeedInbox.is_active.is_(True))
    )).scalars().all())
    if inboxes:
        cutoff = now - timedelta(days=PLACEMENT_LOOKBACK_DAYS)
        campaigns = list((await db.execute(
            select(Campaign).where(
                Campaign.status == CampaignStatus.sent,
                Campaign.sent_at.isnot(None),
                Campaign.sent_at >= cutoff,
                Campaign.sent_at <= now - timedelta(minutes=PLACEMENT_DELAY_MINUTES),
            )
        )).scalars().all())

        checked = 0
        for campaign in campaigns:
            done = {
                p.seed_inbox_id for p in (await db.execute(
                    select(SeedPlacement).where(SeedPlacement.campaign_id == campaign.id)
                )).scalars().all()
            }
            for inbox in inboxes:
                if inbox.id in done:
                    continue
                placement, detail = await seed_service.check_placement(
                    inbox, campaign.subject
                )
                # An `error` result is not stored: it means we could not look,
                # not that the mail is missing, and writing it would freeze a
                # transient IMAP failure into the record permanently.
                if placement == Placement.error:
                    logger.warning("seed check failed for %s: %s", inbox.email, detail)
                    continue
                db.add(SeedPlacement(
                    campaign_id=campaign.id, seed_inbox_id=inbox.id,
                    placement=placement, detail=detail,
                ))
                checked += 1
                if placement == Placement.spam:
                    logger.error(
                        "campaign %s landed in SPAM at %s", campaign.id, inbox.email
                    )
        if checked:
            await db.commit()
            out["placements_recorded"] = checked

    return out


async def run_once() -> dict:
    """One pass over every campaign that is due.

    The advisory lock is taken on its own connection, deliberately. A lock
    taken on the working session would be released the first time that session
    commits — and this worker commits after every message — which would defeat
    the whole point.
    """
    async with engine.connect() as lock_conn:
        acquired = (await lock_conn.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": WORKER_LOCK_KEY}
        )).scalar()
        if not acquired:
            logger.info("another worker pass is already running; exiting")
            return {"skipped": "locked"}

        results = []
        try:
            async with async_session() as db:
                # Reputation checks run whether or not there are campaigns
                # waiting. A blocklisting or a spam-folder placement is the
                # kind of thing that matters most on a quiet week.
                try:
                    trust = await _trust_maintenance(db)
                except Exception:
                    logger.exception("trust maintenance raised")
                    await db.rollback()
                    trust = {"error": True}

                campaign_ids = await campaign_service.due_campaign_ids(db)
                if not campaign_ids:
                    return {"campaigns": 0, "results": [], "trust": trust}
                for campaign_id in campaign_ids:
                    try:
                        results.append(await _process_campaign(db, campaign_id))
                    except Exception:
                        # One bad campaign must not abandon the rest of the
                        # queue. Rolled back so the session is usable for the
                        # next one.
                        logger.exception("campaign %s raised", campaign_id)
                        await db.rollback()
                        results.append({"campaign": str(campaign_id), "error": True})
        finally:
            await lock_conn.execute(
                text("SELECT pg_advisory_unlock(:key)"), {"key": WORKER_LOCK_KEY}
            )

    return {"campaigns": len(results), "results": results, "trust": trust}


async def _main() -> int:
    try:
        summary = await run_once()
    finally:
        # The worker is a short-lived process; leaving pooled connections open
        # keeps Postgres backends alive between runs for no benefit.
        await engine.dispose()
    logger.info("worker finished: %s", summary)
    return 0


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        # No timestamp: journald adds one, and two is noise.
        format="%(levelname)s %(name)s %(message)s",
    )
    sys.exit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
