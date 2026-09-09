"""Creating and updating contacts, including bulk import.

The one rule that shapes this module: an import must never quietly re-enable
mail to someone who stopped it. Re-uploading last quarter's spreadsheet is a
routine thing for a person to do, and a naive upsert would flip every
unsubscribed row back to active.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import ConsentBasis, Contact, ContactStatus
from app.services import suppression_service

logger = logging.getLogger(__name__)

# Statuses an import is not allowed to change. Each represents a decision made
# by the recipient or by the mail system, which an uploaded row does not
# outrank.
PROTECTED_STATUSES = {
    ContactStatus.unsubscribed,
    ContactStatus.bounced,
}


async def get_by_email(db: AsyncSession, email: str) -> Contact | None:
    return (await db.execute(
        select(Contact).where(Contact.email == suppression_service.normalize(email))
    )).scalar_one_or_none()


async def upsert(
    db: AsyncSession,
    *,
    email: str,
    full_name: str = "",
    company: str = "",
    country: str = "",
    consent_basis: ConsentBasis = ConsentBasis.unknown,
    consent_note: str = "",
    tracking_consent: bool = False,
    tags: list[str] | None = None,
    merge_tags: bool = True,
) -> tuple[Contact, bool]:
    """Create or update one contact. Returns (contact, created).

    Field-level rules, all of them chosen so a partial spreadsheet cannot
    destroy better data that is already recorded:

    * Blank incoming values do not overwrite existing ones. A column missing
      from this month's export should not wipe the name captured last month.
    * `consent_basis` is only ever upgraded away from `unknown`, never back
      to it, and `consent_recorded_at` is stamped on the first real basis and
      never re-stamped — it is the date consent was given, not the date the
      row was last touched.
    * Tags merge by default rather than replace, so importing a list of
      "pilot" contacts does not strip the "prospect" tag from people who are
      both.
    * A protected status is left alone entirely.

    Does not commit; the caller owns the transaction so a whole import
    succeeds or fails together.
    """
    normalized = suppression_service.normalize(email)
    contact = await get_by_email(db, normalized)
    created = contact is None

    if contact is None:
        contact = Contact(email=normalized)
        db.add(contact)

    if full_name:
        contact.full_name = full_name
    if company:
        contact.company = company
    if country:
        contact.country = country.strip().upper()[:2]
    if consent_note:
        contact.consent_note = consent_note

    if consent_basis != ConsentBasis.unknown:
        contact.consent_basis = consent_basis
        if contact.consent_recorded_at is None:
            contact.consent_recorded_at = datetime.now(timezone.utc)

    # Only ever grants tracking consent, never revokes it here: withdrawing
    # consent is a deliberate action through the admin screen or an
    # unsubscribe, not a side effect of a column being blank in a CSV.
    if tracking_consent:
        contact.tracking_consent = True

    if tags:
        cleaned = [t.strip().lower()[:50] for t in tags if t and t.strip()]
        if merge_tags:
            contact.tags = sorted(set(list(contact.tags or []) + cleaned))
        else:
            contact.tags = sorted(set(cleaned))

    # A suppressed address is imported as a row so the admin can see it, but
    # never as an active one — the suppression list is the authority.
    if created and await suppression_service.is_suppressed(db, normalized):
        contact.status = ContactStatus.unsubscribed
    elif not created and contact.status in PROTECTED_STATUSES:
        pass
    elif not created and contact.status == ContactStatus.retired:
        # Retirement was our decision for non-engagement, not theirs. A fresh
        # import is a reasonable signal to give them another chance.
        contact.status = ContactStatus.active

    return contact, created


async def import_many(db: AsyncSession, rows: list[dict]) -> dict[str, int]:
    """Bulk import. Returns counts of created, updated and skipped.

    A row with no usable email is skipped rather than raising: an import of
    three hundred contacts must not fail entirely because one line has a
    trailing comma.
    """
    created = updated = skipped = 0
    for row in rows:
        email = suppression_service.normalize(str(row.get("email", "")))
        if not email or "@" not in email:
            skipped += 1
            continue
        _, was_created = await upsert(
            db,
            email=email,
            full_name=str(row.get("full_name", "") or ""),
            company=str(row.get("company", "") or ""),
            country=str(row.get("country", "") or ""),
            consent_basis=row.get("consent_basis") or ConsentBasis.unknown,
            consent_note=str(row.get("consent_note", "") or ""),
            tracking_consent=bool(row.get("tracking_consent", False)),
            tags=row.get("tags") or [],
        )
        if was_created:
            created += 1
        else:
            updated += 1
    return {"created": created, "updated": updated, "skipped": skipped}
