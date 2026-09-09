"""Contacts and the suppression list.

Read access is editor and above, matching the demo inbox. Writes that change
who can be mailed are admin only, because an import is the one operation that
can put several hundred people into a send in a single click.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import require_role
from app.models.contact import Contact, ContactStatus
from app.models.suppression import Suppression
from app.models.user import User, UserRole
from app.schemas.contact import (
    ContactCreate, ContactImportRequest, ContactImportResult, ContactOut,
    ContactUpdate, SuppressionOut,
)
from app.services import contact_service, suppression_service

router = APIRouter()


@router.get("/admin/contacts", response_model=list[ContactOut])
async def list_contacts(
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
    search: str = Query(default="", max_length=200),
    tag: str = Query(default="", max_length=50),
    status: ContactStatus | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    query = select(Contact)
    if search:
        like = f"%{search.strip().lower()}%"
        query = query.where(or_(
            func.lower(Contact.email).like(like),
            func.lower(Contact.full_name).like(like),
            func.lower(Contact.company).like(like),
        ))
    if tag:
        query = query.where(Contact.tags.any(tag.strip().lower()))
    if status is not None:
        query = query.where(Contact.status == status)

    rows = (await db.execute(
        query.order_by(Contact.email).limit(limit).offset(offset)
    )).scalars().all()
    return [ContactOut.model_validate(r) for r in rows]


@router.get("/admin/contacts/tags", response_model=list[str])
async def list_tags(
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    """Every tag in use, so the campaign composer can offer real segments
    rather than a free-text box where a typo silently mails nobody."""
    rows = (await db.execute(
        select(func.unnest(Contact.tags).label("tag")).distinct().order_by("tag")
    )).scalars().all()
    return [t for t in rows if t]


@router.post("/admin/contacts", response_model=ContactOut, status_code=201)
async def create_contact(
    payload: ContactCreate,
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    contact, created = await contact_service.upsert(
        db,
        email=payload.email,
        full_name=payload.full_name,
        company=payload.company,
        country=payload.country,
        consent_basis=payload.consent_basis,
        consent_note=payload.consent_note,
        tracking_consent=payload.tracking_consent,
        tags=payload.tags,
    )
    await db.commit()
    await db.refresh(contact)
    return ContactOut.model_validate(contact)


@router.patch("/admin/contacts/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    contact = await db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    data = payload.model_dump(exclude_unset=True)

    # A suppressed address cannot be reactivated by editing the contact. The
    # suppression list is the authority, and an edit screen must not be a way
    # around it — that is precisely how someone who complained gets mailed
    # again.
    if data.get("status") == ContactStatus.active:
        if await suppression_service.is_suppressed(db, contact.email):
            raise HTTPException(
                status_code=409,
                detail=(
                    "This address is on the suppression list and cannot be "
                    "reactivated. Suppression is permanent by design."
                ),
            )

    for field, value in data.items():
        if field == "tags" and value is not None:
            value = sorted({t.strip().lower()[:50] for t in value if t and t.strip()})
        if field == "country" and value is not None:
            value = value.strip().upper()[:2]
        setattr(contact, field, value)

    await db.commit()
    await db.refresh(contact)
    return ContactOut.model_validate(contact)


@router.post("/admin/contacts/import", response_model=ContactImportResult)
async def import_contacts(
    payload: ContactImportRequest,
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await contact_service.import_many(
        db, [row.model_dump() for row in payload.rows]
    )
    await db.commit()
    return ContactImportResult(**result)


@router.get("/admin/suppressions", response_model=list[SuppressionOut])
async def list_suppressions(
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Read only, and there is deliberately no endpoint to remove a row. See
    models/suppression.py."""
    rows = (await db.execute(
        select(Suppression).order_by(desc(Suppression.created_at)).limit(limit).offset(offset)
    )).scalars().all()
    return [
        SuppressionOut(
            email=r.email, reason=r.reason.value, note=r.note, created_at=r.created_at,
        )
        for r in rows
    ]
