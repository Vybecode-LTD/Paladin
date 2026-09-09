"""Reading DMARC aggregate reports.

Every mailbox provider that supports DMARC emails one of these a day, listing
every server on the internet that sent mail claiming to be from the domain and
whether each one authenticated. It is the only complete answer to "what sends
as us", and having that answer is what makes it safe to tighten the domain
policy — the alternative is turning on enforcement and finding out which
forgotten system it broke from the people who stop receiving mail.

Reports arrive as a small XML file, gzipped or zipped, attached to an email.
The schema (RFC 7489 appendix C) is stable and simple enough that parsing it
directly is less work than carrying a dependency to do it.

The parser is pure and takes bytes, so it is testable without a mailbox, and
the transport — an admin uploading a file, or the worker polling IMAP — is a
separate concern that can change without touching any of this.
"""
import gzip
import io
import logging
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from xml.etree import ElementTree

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trust import DmarcRecord

logger = logging.getLogger(__name__)


class DmarcParseError(Exception):
    """The bytes were not a DMARC report we can read."""


@dataclass(frozen=True)
class ParsedRecord:
    org_name: str
    report_id: str
    date_begin: date
    date_end: date
    policy_domain: str
    policy_p: str
    header_from: str
    source_ip: str
    count: int
    disposition: str
    dkim_aligned: bool
    spf_aligned: bool
    dkim_domain: str
    spf_domain: str


def decompress(data: bytes) -> bytes:
    """Reports arrive gzipped, zipped, or occasionally as bare XML.

    Sniffed by magic bytes rather than by file extension, because the
    extension comes from an attachment filename that providers do not agree
    on and that a mail client may have rewritten.
    """
    if data[:2] == b"\x1f\x8b":                      # gzip
        try:
            return gzip.decompress(data)
        except OSError as exc:
            raise DmarcParseError(f"Could not un-gzip the report: {exc}")
    if data[:2] == b"PK":                            # zip
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = [n for n in archive.namelist() if n.lower().endswith(".xml")]
                if not names:
                    raise DmarcParseError("The zip contains no XML file.")
                return archive.read(names[0])
        except zipfile.BadZipFile as exc:
            raise DmarcParseError(f"Could not open the zip: {exc}")
    return data


def _text(node, path: str, default: str = "") -> str:
    found = node.find(path) if node is not None else None
    return (found.text or "").strip() if found is not None and found.text else default


def _to_date(epoch: str) -> date:
    try:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).date()
    except (TypeError, ValueError):
        return datetime.now(timezone.utc).date()


def parse(data: bytes) -> list[ParsedRecord]:
    """Parse one report into its per-source records.

    A malformed individual record is skipped rather than failing the whole
    report: providers do occasionally emit one with a missing field, and
    losing a day of visibility over one bad row would be the wrong trade.
    """
    xml = decompress(data)
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise DmarcParseError(f"Not valid XML: {exc}")

    if root.tag != "feedback":
        raise DmarcParseError(
            f"Expected a DMARC <feedback> document, found <{root.tag}>."
        )

    meta = root.find("report_metadata")
    policy = root.find("policy_published")
    org_name = _text(meta, "org_name")
    report_id = _text(meta, "report_id")
    date_begin = _to_date(_text(meta, "date_range/begin"))
    date_end = _to_date(_text(meta, "date_range/end"))
    policy_domain = _text(policy, "domain")
    policy_p = _text(policy, "p")

    out: list[ParsedRecord] = []
    for record in root.findall("record"):
        try:
            row = record.find("row")
            evaluated = row.find("policy_evaluated") if row is not None else None
            source_ip = _text(row, "source_ip")
            if not source_ip:
                continue

            # `auth_results` can hold several DKIM signatures. The one that
            # matters is a passing one, so a message signed by both a
            # forwarder and us is not reported as a failure.
            auth = record.find("auth_results")
            dkim_domain, dkim_pass = "", False
            if auth is not None:
                for dkim in auth.findall("dkim"):
                    domain = _text(dkim, "domain")
                    result = _text(dkim, "result").lower()
                    if result == "pass":
                        dkim_domain, dkim_pass = domain, True
                        break
                    if not dkim_domain:
                        dkim_domain = domain
            spf_domain = _text(auth, "spf/domain") if auth is not None else ""

            out.append(ParsedRecord(
                org_name=org_name,
                report_id=report_id,
                date_begin=date_begin,
                date_end=date_end,
                policy_domain=policy_domain,
                policy_p=policy_p,
                header_from=_text(record, "identifiers/header_from"),
                source_ip=source_ip,
                count=int(_text(row, "count", "0") or 0),
                disposition=_text(evaluated, "disposition"),
                # `policy_evaluated` is the authority: it reports the result
                # AFTER alignment, which is the only thing DMARC acts on. The
                # raw auth_results below can say "pass" for a domain that is
                # not ours, which is not a DMARC pass at all.
                dkim_aligned=_text(evaluated, "dkim").lower() == "pass",
                spf_aligned=_text(evaluated, "spf").lower() == "pass",
                dkim_domain=dkim_domain if dkim_pass or dkim_domain else "",
                spf_domain=spf_domain,
            ))
        except (AttributeError, ValueError) as exc:
            logger.warning("skipping malformed DMARC record in %s: %s", report_id, exc)
            continue

    return out


async def store(db: AsyncSession, records: list[ParsedRecord]) -> dict[str, int]:
    """Persist parsed records, skipping ones already seen.

    Providers resend a report when they think it was not received, and the
    mailbox may be polled more than once, so the same facts arrive repeatedly.
    Does not commit; the caller owns the transaction.
    """
    stored = skipped = 0
    for r in records:
        exists = (await db.execute(
            select(DmarcRecord.id).where(
                DmarcRecord.report_id == r.report_id,
                DmarcRecord.source_ip == r.source_ip,
                DmarcRecord.header_from == r.header_from,
            )
        )).scalar_one_or_none()
        if exists is not None:
            skipped += 1
            continue
        db.add(DmarcRecord(
            org_name=r.org_name, report_id=r.report_id,
            date_begin=r.date_begin, date_end=r.date_end,
            policy_domain=r.policy_domain, policy_p=r.policy_p,
            header_from=r.header_from, source_ip=r.source_ip, count=r.count,
            disposition=r.disposition,
            dkim_aligned=r.dkim_aligned, spf_aligned=r.spf_aligned,
            dkim_domain=r.dkim_domain, spf_domain=r.spf_domain,
        ))
        stored += 1
    return {"stored": stored, "skipped": skipped, "records": len(records)}
