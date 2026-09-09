"""Inbound provider events.

Public by necessity — Mailgun has to be able to reach it — and therefore
guarded by signature rather than by a session. Two deliberate choices:

**Fails closed.** With no signing key configured, every event is rejected.
An unverified event could suppress a real contact or fabricate a delivery, so
"not configured" must mean "accept nothing", never "accept everything".

**No rate limit.** The front proxy on this server forwards no client address,
so every request appears to come from one IP and a shared slowapi bucket would
be exhausted by a normal burst of webhooks, silently dropping real events. The
signature is the gate here, not a request count.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import event_service, sender_service
from app.services.senders.mailgun_sender import (
    dedupe_key_for, parse_event, verify_webhook_signature,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhooks/mailgun")
async def mailgun_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Record one Mailgun event.

    Returns 200 for anything correctly signed, including events this system
    does not recognise. Mailgun retries until it gets a 200, so answering
    non-200 to an event we simply do not care about would put it in a retry
    loop forever. The only non-200 here is a failed signature check, which
    SHOULD keep being rejected.
    """
    try:
        body = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail="Expected a JSON body.")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Expected a JSON object.")

    secret = await sender_service.get_webhook_secret(db)
    if not secret:
        logger.warning("Mailgun webhook rejected: no signing key configured")
        raise HTTPException(
            status_code=403,
            detail="Webhook signing key is not configured.",
        )

    signature = body.get("signature")
    if not isinstance(signature, dict):
        raise HTTPException(status_code=403, detail="Missing signature.")

    if not verify_webhook_signature(
        signing_key=secret,
        timestamp=str(signature.get("timestamp", "")),
        token=str(signature.get("token", "")),
        signature=str(signature.get("signature", "")),
    ):
        logger.warning("Mailgun webhook rejected: bad signature")
        raise HTTPException(status_code=403, detail="Invalid signature.")

    event = parse_event(body)
    if not event:
        # Correctly signed but shaped in a way we do not understand. Accept it
        # so Mailgun stops retrying, and log it so a change in their payload
        # shows up somewhere a person will see.
        logger.warning("Mailgun webhook: signed but unparseable body")
        return {"ok": True, "recorded": False}

    recorded = await event_service.ingest_mailgun_event(
        db, event, dedupe_key=dedupe_key_for(event),
    )
    await db.commit()
    return {"ok": True, "recorded": recorded}
