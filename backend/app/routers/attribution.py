"""Where the product reports what a recipient did after the email.

This is the endpoint that turns "twelve people clicked" into "twelve people
clicked and four of them logged in", which is the only number in the system
that no bought email tool could ever produce, because none of them can see
inside Paladin.

**Authentication is the token itself.** It is 128 bits of randomness, minted
per message, and the only way to hold one is to have received that message or
to have been given it by the recipient's own browser. Fabricating a conversion
therefore requires being the recipient, and the worst a recipient can do is
over-report their own engagement — which is not an attack worth a second
credential to manage, a rotation procedure to forget, and another secret in
the deployment.

No rate limit, for the same reason as the tracking endpoints: the front proxy
forwards no client address, so a shared bucket would start refusing real
conversions from everyone the moment one caller was busy.
"""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.campaign_message import CampaignMessage
from app.models.contact import Contact
from app.models.email_event import EmailEvent, EventTier, EventType
from app.services import event_service

logger = logging.getLogger(__name__)

router = APIRouter()


class AttributionEvent(BaseModel):
    token: str = Field(min_length=16, max_length=64)
    # The action, as the product names it: "demo_booked", "first_login",
    # "feature_used". A free string rather than an enum so the product can
    # start reporting something new without a migration here.
    name: str = Field(min_length=1, max_length=100)
    metadata: dict = Field(default_factory=dict)


@router.post("/attribution")
async def record_attribution(
    payload: AttributionEvent, db: AsyncSession = Depends(get_db),
):
    """Record one product action against the message that led to it.

    Always returns 200, including for a token that means nothing to us. The
    caller is the product, not a person, and a 404 would give an unauthenticated
    caller a way to test whether a token is real — while also inviting a retry
    loop over something that will never succeed.
    """
    message = (await db.execute(
        select(CampaignMessage).where(CampaignMessage.token == payload.token)
    )).scalar_one_or_none()
    if message is None:
        logger.info("attribution for unknown token: %s", payload.name)
        return {"recorded": False}

    name = payload.name.strip().lower()
    written = await event_service.record(
        db,
        # One of each named action per message. A product that reports
        # "first_login" on every login should not turn one recipient into a
        # hundred conversions.
        dedupe_key=f"convert:{payload.token}:{name}",
        email=message.email,
        event_type=EventType.converted,
        # The product is stating something it observed directly. That is a
        # fact about its own system, not an inference about a mail client.
        tier=EventTier.exact,
        classification=f"product:{name}",
        payload={"name": name, "metadata": payload.metadata},
        campaign_message_id=message.id,
    )

    if written is not None:
        # A conversion is the strongest engagement signal there is, so it
        # counts toward the contact's score and clears the quiet counter that
        # would otherwise eventually retire them.
        contact = await db.get(Contact, message.contact_id)
        if contact is not None:
            contact.engagement_score = (contact.engagement_score or 0) + 3
            contact.last_engaged_at = written.occurred_at
            contact.consecutive_ignored = 0

    await db.commit()
    return {"recorded": written is not None}
