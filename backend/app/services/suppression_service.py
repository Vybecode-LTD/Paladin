"""The one gate every send passes through.

Two rules that look like detail and are not:

  * Addresses are normalised (lower-cased, stripped) on the way in AND on the
    way out. Mail addresses are case-insensitive in the part that matters to
    every real provider, so storing "Bob@X.com" and checking "bob@x.com" would
    let a suppressed person be mailed again — the exact failure this table
    exists to prevent.
  * There is no remove function. Suppression is permanent by design, and an
    API that can un-suppress is an API that will eventually un-suppress
    someone who pressed the spam button.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact, ContactStatus
from app.models.suppression import Suppression, SuppressionReason


def normalize(email: str) -> str:
    return (email or "").strip().lower()


async def is_suppressed(db: AsyncSession, email: str) -> bool:
    result = await db.execute(
        select(Suppression.id).where(Suppression.email == normalize(email))
    )
    return result.scalar_one_or_none() is not None


async def filter_suppressed(db: AsyncSession, emails: list[str]) -> set[str]:
    """Returns the normalised subset that IS suppressed, in one query.

    Campaign expansion checks hundreds of addresses at once; doing that one
    round trip at a time is slow enough that someone will eventually be
    tempted to skip the check.
    """
    if not emails:
        return set()
    normalized = [normalize(e) for e in emails]
    result = await db.execute(
        select(Suppression.email).where(Suppression.email.in_(normalized))
    )
    return set(result.scalars().all())


async def suppress(
    db: AsyncSession,
    *,
    email: str,
    reason: SuppressionReason,
    note: str = "",
) -> Suppression:
    """Idempotent. A repeated complaint webhook, or an unsubscribe clicked
    twice, must not raise — the address is already suppressed, which is the
    outcome the caller wanted.

    Does NOT commit: the caller decides the transaction boundary, so
    suppressing and marking the contact stay atomic together.
    """
    normalized = normalize(email)
    existing = (await db.execute(
        select(Suppression).where(Suppression.email == normalized)
    )).scalar_one_or_none()
    if existing is not None:
        return existing

    row = Suppression(email=normalized, reason=reason, note=note)
    db.add(row)

    # Keep the contact's own status in step, so the admin list shows why
    # someone stopped receiving mail without a join against this table.
    contact = (await db.execute(
        select(Contact).where(Contact.email == normalized)
    )).scalar_one_or_none()
    if contact is not None:
        if reason == SuppressionReason.hard_bounced:
            contact.status = ContactStatus.bounced
        elif reason in (SuppressionReason.unsubscribed, SuppressionReason.complained):
            contact.status = ContactStatus.unsubscribed
    return row
