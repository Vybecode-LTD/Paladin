from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.middleware.auth import require_role
from app.models.user import User, UserRole
from app.models.demo_request import DemoRequest
from app.schemas.demo import DemoRequestCreate, DemoRequestOut

router = APIRouter()


@router.post("/demo-requests", response_model=DemoRequestOut, status_code=201)
async def submit_demo(payload: DemoRequestCreate, db: AsyncSession = Depends(get_db)):
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
