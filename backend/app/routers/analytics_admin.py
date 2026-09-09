"""Read-only analytics endpoints for the Analytics tab.

Editor and above, matching the demo inbox: these are figures about the
company's own campaigns, not credentials or the ability to send anything.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import require_role
from app.models.campaign import Campaign
from app.models.user import User, UserRole
from app.services import stats_service

router = APIRouter()


@router.get("/admin/analytics/overview")
async def analytics_overview(
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50),
):
    return await stats_service.overview(db, limit=limit)


@router.get("/admin/analytics/campaigns/{campaign_id}")
async def campaign_scorecard(
    campaign_id: uuid.UUID,
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    """Every figure for one campaign, each carrying its tier.

    Returned as one document rather than a dozen endpoints because the page
    shows them together and a partial view is misleading: an open count
    without its measurable denominator, or a click count without the machine
    split, is worse than no number.
    """
    campaign = await db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await stats_service.campaign_scorecard(db, campaign)


@router.get("/admin/analytics/send-time")
async def send_time(
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    return await stats_service.send_time_recommendation(db)
