"""Campaign CRUD, audience preview, test send and queueing.

Drafting is editor and above; queueing a real send is admin only. Everything
before the send is reversible, and the send is not.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import require_role
from app.models.campaign import Campaign, CampaignStatus
from app.models.campaign_message import CampaignMessage
from app.models.contact import Contact
from app.models.email_event import EmailEvent, EventTier, EventType
from app.models.user import User, UserRole
from app.schemas.campaign import (
    AudienceMember, AudiencePreview, CampaignCreate, CampaignOut,
    CampaignSendRequest, CampaignStats, CampaignTestRequest, CampaignUpdate,
)
from app.services import (
    campaign_service, preflight_service, render_service, sender_service,
)
from app.services.senders.base import OutboundMessage, SenderError

router = APIRouter()

# Editable states. Once a campaign is queued its content is frozen: messages
# already handed to the provider cannot be recalled, so allowing an edit
# mid-send would mean one list receiving two different emails under one name.
EDITABLE = {CampaignStatus.draft, CampaignStatus.failed}

PREVIEW_SAMPLE_SIZE = 10


async def _get(db: AsyncSession, campaign_id: uuid.UUID) -> Campaign:
    campaign = await db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("/admin/campaigns", response_model=list[CampaignOut])
async def list_campaigns(
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Campaign).order_by(desc(Campaign.created_at))
    )).scalars().all()
    return [CampaignOut.model_validate(r) for r in rows]


@router.post("/admin/campaigns", response_model=CampaignOut, status_code=201)
async def create_campaign(
    payload: CampaignCreate,
    user: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    campaign = Campaign(**payload.model_dump(), created_by_id=user.id)
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return CampaignOut.model_validate(campaign)


@router.get("/admin/campaigns/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: uuid.UUID,
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    return CampaignOut.model_validate(await _get(db, campaign_id))


@router.patch("/admin/campaigns/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: uuid.UUID,
    payload: CampaignUpdate,
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get(db, campaign_id)
    if campaign.status not in EDITABLE:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This campaign is {campaign.status.value} and can no longer be "
                "edited. Messages already sent cannot be recalled."
            ),
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    await db.commit()
    await db.refresh(campaign)
    return CampaignOut.model_validate(campaign)


@router.delete("/admin/campaigns/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: uuid.UUID,
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get(db, campaign_id)
    if campaign.status != CampaignStatus.draft:
        raise HTTPException(
            status_code=409,
            detail=(
                "Only a draft can be deleted. A campaign that has been queued "
                "or sent is a record of mail that left the building."
            ),
        )
    await db.delete(campaign)
    await db.commit()


@router.get("/admin/campaigns/{campaign_id}/audience", response_model=AudiencePreview)
async def preview_audience(
    campaign_id: uuid.UUID,
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get(db, campaign_id)
    breakdown = await campaign_service.audience_breakdown(db, campaign)

    contacts: list[Contact] = breakdown.pop("eligible_contacts")
    variants: list[str] = breakdown.pop("variants")
    sample = [
        AudienceMember(
            email=c.email,
            full_name=c.full_name,
            variant=v,
            trackable=c.may_track_opens,
        )
        for c, v in list(zip(contacts, variants))[:PREVIEW_SAMPLE_SIZE]
    ]
    return AudiencePreview(**breakdown, sample=sample)


@router.post("/admin/campaigns/{campaign_id}/test")
async def send_test(
    campaign_id: uuid.UUID,
    payload: CampaignTestRequest,
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    """Send the real rendered campaign to one address.

    Bypasses the audience entirely and creates no message row, so it cannot
    affect the campaign's own numbers. Personalisation renders against a
    stand-in contact, which is also how an author discovers that
    `{{first_name}}` looks wrong when someone has no name recorded.
    """
    campaign = await _get(db, campaign_id)
    settings = await sender_service.get_sender_settings(db)
    if settings is None or not settings.from_email:
        raise HTTPException(
            status_code=400,
            detail="Configure the campaign sender and its From address in Settings first.",
        )

    try:
        sender = await sender_service.build_sender(db)
    except SenderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    stand_in = Contact(email=payload.to_email, full_name="", company="", country="")
    # A stable, obviously-fake token: a test must never mint a real tracking
    # token, or a click in a test message would be recorded against nothing.
    unsubscribe = render_service.unsubscribe_url(settings.tracking_base_url, "test-preview")

    try:
        await sender.send(OutboundMessage(
            to_email=payload.to_email,
            subject=f"[TEST] {campaign.subject}",
            text_body=render_service.render_text(
                campaign, stand_in,
                unsubscribe=unsubscribe, postal=settings.postal_address,
            ),
            html_body=render_service.render_html(
                campaign, stand_in,
                unsubscribe=unsubscribe, postal=settings.postal_address,
            ),
            from_email=settings.from_email,
            from_name=settings.from_name,
            headers=render_service.list_unsubscribe_headers(unsubscribe),
            tags=["campaign-test"],
        ))
    except SenderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"sent": True}


@router.post("/admin/campaigns/{campaign_id}/send", response_model=CampaignOut)
async def queue_send(
    campaign_id: uuid.UUID,
    payload: CampaignSendRequest,
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    """Queue a campaign. The worker does the sending.

    Deliberately does NOT send inline. A request that mails several hundred
    people would sit open for minutes behind a proxy that times out in thirty
    seconds, and a dropped connection mid-send would leave nobody knowing how
    far it got.
    """
    campaign = await _get(db, campaign_id)
    if campaign.status not in EDITABLE:
        raise HTTPException(
            status_code=409,
            detail=f"This campaign is already {campaign.status.value}.",
        )
    if not campaign.subject.strip() or not campaign.body_markdown.strip():
        raise HTTPException(
            status_code=400, detail="A campaign needs a subject and a body before it can be sent.",
        )

    settings = await sender_service.get_sender_settings(db)
    if settings is None or not settings.from_email or not settings.tracking_base_url:
        raise HTTPException(
            status_code=400,
            detail=(
                "Configure the campaign sender, its From address and the tracking "
                "URL in Settings first — the unsubscribe link is built from the "
                "tracking URL, and mail cannot go out without one."
            ),
        )

    # Pre-flight is enforced here, not merely offered in the editor. A check
    # an author can skip is not a check, and the blockers are all things that
    # make a message either illegal or undeliverable.
    findings = preflight_service.check(campaign, settings)
    blockers = preflight_service.blockers(findings)
    if blockers:
        raise HTTPException(
            status_code=400,
            detail="This campaign cannot be sent yet: "
                   + " ".join(f.message for f in blockers),
        )

    breakdown = await campaign_service.audience_breakdown(db, campaign)
    if breakdown["eligible"] == 0:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No eligible recipients. Of {breakdown['total_contacts']} contacts "
                f"matching this segment, {breakdown['suppressed']} are suppressed, "
                f"{breakdown['excluded_inactive']} are not active and "
                f"{breakdown['excluded_no_consent']} have no consent basis recorded."
            ),
        )

    campaign.status = CampaignStatus.scheduled
    campaign.scheduled_for = payload.scheduled_for
    campaign.error = ""
    await db.commit()
    await db.refresh(campaign)
    return CampaignOut.model_validate(campaign)


@router.get("/admin/campaigns/{campaign_id}/stats", response_model=CampaignStats)
async def campaign_stats(
    campaign_id: uuid.UUID,
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get(db, campaign_id)

    totals = (await db.execute(
        select(
            func.count(CampaignMessage.id),
            func.count(CampaignMessage.sent_at),
            func.count(CampaignMessage.id).filter(CampaignMessage.variant == campaign_service.HOLDOUT),
            func.count(CampaignMessage.id).filter(CampaignMessage.send_error != ""),
        ).where(CampaignMessage.campaign_id == campaign_id)
    )).one()

    counts = dict((await db.execute(
        select(EmailEvent.type, func.count(EmailEvent.id))
        .join(CampaignMessage, EmailEvent.campaign_message_id == CampaignMessage.id)
        .where(CampaignMessage.campaign_id == campaign_id)
        .group_by(EmailEvent.type)
    )).all())

    inferred = dict((await db.execute(
        select(EmailEvent.type, func.count(EmailEvent.id))
        .join(CampaignMessage, EmailEvent.campaign_message_id == CampaignMessage.id)
        .where(
            CampaignMessage.campaign_id == campaign_id,
            EmailEvent.tier == EventTier.inferred,
        )
        .group_by(EmailEvent.type)
    )).all())

    return CampaignStats(
        campaign_id=campaign.id,
        messages=totals[0],
        sent=totals[1],
        holdout=totals[2],
        failed=totals[3],
        accepted=counts.get(EventType.accepted, 0),
        delivered=counts.get(EventType.delivered, 0),
        soft_bounced=counts.get(EventType.soft_bounced, 0),
        hard_bounced=counts.get(EventType.hard_bounced, 0),
        complained=counts.get(EventType.complained, 0),
        unsubscribed=counts.get(EventType.unsubscribed, 0),
        # Reported as inferred explicitly. An open is never promoted to a fact
        # here; corroboration happens in the reporting layer, not by relabelling
        # the underlying event.
        opened_inferred=inferred.get(EventType.opened, 0),
        clicked_inferred=inferred.get(EventType.clicked, 0),
        replied=counts.get(EventType.replied, 0),
    )
