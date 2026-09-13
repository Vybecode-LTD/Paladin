"""The trust panel, and the things that feed it.

Reading is editor and above. Anything that changes configuration or stores a
credential is admin only.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt_secret
from app.core.database import get_db
from app.middleware.auth import require_role
from app.models.campaign import Campaign
from app.models.trust import BlocklistResult, SeedInbox
from app.models.user import User, UserRole
from app.services import (
    blocklist_service, dmarc_service, preflight_service, sender_service,
    trust_service,
)
from app.services.dmarc_service import DmarcParseError

logger = logging.getLogger(__name__)

router = APIRouter()

# One report is a few kilobytes compressed. Anything far larger is not a DMARC
# report, and reading it into memory to find that out is the thing to avoid.
MAX_REPORT_BYTES = 10 * 1024 * 1024


@router.get("/admin/trust")
async def trust_panel(
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    return await trust_service.panel(db)


# --- DMARC --------------------------------------------------------------------


@router.post("/admin/trust/dmarc/upload")
async def upload_dmarc_report(
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
):
    """Take one aggregate report, gzipped, zipped or bare XML.

    An upload path exists so the panel is useful from day one, before anyone
    has wired the dmarc mailbox to anything: a provider's report can be
    dragged straight out of the inbox and dropped here. The worker reads the
    mailbox automatically once it is configured, and both paths land in the
    same place.
    """
    data = await file.read(MAX_REPORT_BYTES + 1)
    if len(data) > MAX_REPORT_BYTES:
        raise HTTPException(status_code=413, detail="That file is too large to be a DMARC report.")
    if not data:
        raise HTTPException(status_code=400, detail="The file is empty.")

    try:
        records = dmarc_service.parse(data)
    except DmarcParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not records:
        return {"stored": 0, "skipped": 0, "records": 0,
                "note": "The report parsed but contained no sending records."}

    result = await dmarc_service.store(db, records)
    await db.commit()
    return result


# --- blocklists ---------------------------------------------------------------


@router.post("/admin/trust/blocklists/check")
async def run_blocklist_check(
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    """Check the sending domains against the public blocklists now.

    Also runs on the worker's daily schedule; this is the button for when
    something looks wrong and waiting until tomorrow is not an option.
    """
    settings = await sender_service.get_sender_settings(db)
    domains = sorted({
        d for d in [
            (settings.mailgun_domain if settings else ""),
            (settings.reply_domain if settings else ""),
        ] if d
    })
    if not domains:
        raise HTTPException(
            status_code=400,
            detail="No sending domain is configured yet, so there is nothing to check.",
        )

    results = await blocklist_service.check_all(domains=domains, ips=[])
    for r in results:
        db.add(BlocklistResult(
            target=r["target"], blocklist=r["blocklist"],
            listed=r["listed"], response=r["response"],
        ))
    await db.commit()
    return {
        "checked": len(results),
        "listed": sum(1 for r in results if r["listed"]),
        "errors": sum(1 for r in results if r.get("error")),
        "results": results,
    }


# --- seed inboxes -------------------------------------------------------------


class SeedInboxIn(BaseModel):
    label: str = Field(default="", max_length=100)
    email: EmailStr
    provider: str = Field(default="gmail", max_length=50)
    imap_host: str = Field(default="", max_length=255)
    imap_port: int = Field(default=993, ge=1, le=65535)
    imap_username: str = Field(default="", max_length=320)
    # Write-only, same contract as every other secret in this system.
    password: str | None = Field(default=None, max_length=500)


@router.get("/admin/trust/seed-inboxes")
async def list_seed_inboxes(
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(select(SeedInbox).order_by(SeedInbox.email))).scalars().all()
    return [
        {
            "id": str(r.id), "label": r.label, "email": r.email,
            "provider": r.provider, "imap_host": r.imap_host, "imap_port": r.imap_port,
            "imap_username": r.imap_username,
            "password_set": bool(r.encrypted_password), "is_active": r.is_active,
        }
        for r in rows
    ]


@router.post("/admin/trust/seed-inboxes", status_code=201)
async def create_seed_inbox(
    payload: SeedInboxIn,
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(
        select(SeedInbox).where(SeedInbox.email == payload.email.lower())
    )).scalar_one_or_none()
    row = existing or SeedInbox(email=payload.email.lower())
    if existing is None:
        db.add(row)

    row.label = payload.label
    row.provider = payload.provider
    row.imap_host = payload.imap_host
    row.imap_port = payload.imap_port
    row.imap_username = payload.imap_username or payload.email.lower()
    if payload.password:
        try:
            row.encrypted_password = encrypt_secret(payload.password)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    await db.commit()
    await db.refresh(row)
    return {"id": str(row.id), "email": row.email, "password_set": bool(row.encrypted_password)}


@router.delete("/admin/trust/seed-inboxes/{inbox_id}", status_code=204)
async def delete_seed_inbox(
    inbox_id: uuid.UUID,
    _: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    row = await db.get(SeedInbox, inbox_id)
    if row is not None:
        await db.delete(row)
        await db.commit()


# --- pre-flight ----------------------------------------------------------------


@router.get("/admin/campaigns/{campaign_id}/preflight")
async def preflight(
    campaign_id: uuid.UUID,
    _: User = Depends(require_role(UserRole.editor)),
    db: AsyncSession = Depends(get_db),
):
    """What is wrong with this campaign, before it goes anywhere.

    Also enforced at send time — this endpoint is so an author can see the
    findings while writing, rather than discovering them at the moment they
    press send.
    """
    campaign = await db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")

    settings = await sender_service.get_sender_settings(db)
    findings = preflight_service.check(campaign, settings)
    return {
        "findings": [
            {"severity": f.severity.value, "code": f.code, "message": f.message}
            for f in findings
        ],
        "blockers": len(preflight_service.blockers(findings)),
        "can_send": not preflight_service.blockers(findings),
    }
