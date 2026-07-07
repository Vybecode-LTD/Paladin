import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.ratelimit import limiter
from app.middleware.auth import require_role
from app.models.user import User, UserRole
from app.models.demo_request import DemoRequest
from app.schemas.demo import DemoRequestCreate, DemoRequestOut, DemoRequestUpdate

router = APIRouter()


@router.post("/demo-requests", response_model=DemoRequestOut, status_code=201)
@limiter.limit(settings.demo_rate_limit)
async def submit_demo(request: Request, payload: DemoRequestCreate, db: AsyncSession = Depends(get_db)):
    """Public: capture a demo request from the marketing site."""
    dr = DemoRequest(**payload.model_dump())
    db.add(dr)
    await db.commit()
    await db.refresh(dr)
    return DemoRequestOut.model_validate(dr)


@router.get("/admin/demo-requests", response_model=list[DemoRequestOut])
async def list_demo_requests(
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(DemoRequest).order_by(desc(DemoRequest.created_at))
    )).scalars().all()
    return [DemoRequestOut.model_validate(r) for r in rows]


@router.patch("/admin/demo-requests/{request_id}", response_model=DemoRequestOut)
async def update_demo_request(
    request_id: uuid.UUID,
    payload: DemoRequestUpdate,
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    dr = await db.get(DemoRequest, request_id)
    if not dr:
        raise HTTPException(status_code=404, detail="Demo request not found")
    dr.is_handled = payload.is_handled
    await db.commit()
    await db.refresh(dr)
    return DemoRequestOut.model_validate(dr)
