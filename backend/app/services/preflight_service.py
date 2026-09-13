"""Checking a campaign before it can be sent.

Deliberately our own rules rather than a call out to SpamAssassin. Running
SpamAssassin means running its daemon, and this application lives on a shared
machine that also serves three other sites; adding a service there to score a
handful of messages a month is not a reasonable trade. More to the point, most
of what SpamAssassin scores is irrelevant to a small warm B2B list, while the
things that actually hurt this sender — a link shortener, an image-only body,
a missing plain-text part, a subject in capitals — are a short list that can be
checked exactly and explained in words an author can act on.

Every check returns a finding with a severity. `blocker` findings stop the
send; everything else is advice. The distinction matters: a tool that blocks
on style makes people work around it, and then it is not there for the case
that mattered.
"""
import re
from dataclasses import dataclass
from enum import Enum

from app.models.campaign import Campaign
from app.models.sender_settings import SenderSettings


class Severity(str, Enum):
    blocker = "blocker"
    warning = "warning"
    note = "note"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    code: str
    message: str


# Wrapped links hide the destination, which is exactly what a phishing message
# does, so filters weight them heavily. There is also no reason to use one:
# our own click tracking already shortens nothing and hides nothing.
SHORTENER_HOSTS = (
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "buff.ly",
    "is.gd", "rebrand.ly", "cutt.ly", "shorturl.at", "rb.gy",
)

# Phrases that were spam markers a decade ago and are still weighted. None of
# them belong in a deployment update to existing clients anyway, so flagging
# them costs nothing.
RISKY_PHRASES = (
    "act now", "click here now", "limited time offer", "risk free",
    "100% free", "guarantee", "no obligation", "winner", "congratulations you",
    "cash bonus", "credit card", "order now", "buy direct", "earn extra income",
)

_URL = re.compile(r"https?://([^/\s)\"'>]+)", re.IGNORECASE)
_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)")

MIN_BODY_CHARS = 40
MAX_SUBJECT_CHARS = 90
MAX_EXCLAMATIONS = 2


def check(campaign: Campaign, settings: SenderSettings | None) -> list[Finding]:
    """Everything wrong with this campaign, worst first."""
    findings: list[Finding] = []
    body = campaign.body_markdown or ""
    subject = (campaign.subject or "").strip()

    findings.extend(_configuration(settings))
    findings.extend(_subject(subject, campaign))
    findings.extend(_body(body))
    findings.extend(_links(body))

    order = {Severity.blocker: 0, Severity.warning: 1, Severity.note: 2}
    return sorted(findings, key=lambda f: order[f.severity])


def _configuration(settings: SenderSettings | None) -> list[Finding]:
    """The settings a message legally and practically cannot go out without."""
    if settings is None:
        return [Finding(
            Severity.blocker, "no-sender",
            "No campaign sender is configured. Set one up in Settings first.",
        )]
    out = []
    if not settings.from_email:
        out.append(Finding(
            Severity.blocker, "no-from-address",
            "No From address is set, so there is nothing to send as.",
        ))
    if not settings.tracking_base_url:
        out.append(Finding(
            Severity.blocker, "no-tracking-url",
            "No tracking URL is set. The unsubscribe link is built from it, and "
            "marketing email cannot go out without a working unsubscribe.",
        ))
    if not settings.postal_address:
        out.append(Finding(
            Severity.blocker, "no-postal-address",
            "No postal address is set. US law requires a valid physical address "
            "in the footer of every marketing message.",
        ))
    if not settings.reply_domain:
        out.append(Finding(
            Severity.warning, "no-reply-domain",
            "No reply domain is set, so replies cannot be matched back to this "
            "campaign. For a B2B list a reply is the most valuable signal there is.",
        ))
    return out


def _subject(subject: str, campaign: Campaign) -> list[Finding]:
    out = []
    if not subject:
        out.append(Finding(Severity.blocker, "no-subject", "The campaign has no subject."))
        return out

    letters = [c for c in subject if c.isalpha()]
    if len(letters) >= 8 and all(c.isupper() for c in letters):
        out.append(Finding(
            Severity.warning, "shouting-subject",
            "The subject is entirely in capitals, which filters weight heavily "
            "and recipients read as shouting.",
        ))
    if subject.count("!") > MAX_EXCLAMATIONS:
        out.append(Finding(
            Severity.warning, "excess-punctuation",
            f"The subject has {subject.count('!')} exclamation marks.",
        ))
    if len(subject) > MAX_SUBJECT_CHARS:
        out.append(Finding(
            Severity.note, "long-subject",
            f"The subject is {len(subject)} characters. Most inboxes cut off "
            f"around {MAX_SUBJECT_CHARS}, so the end will not be read.",
        ))
    if not (campaign.preheader or "").strip():
        out.append(Finding(
            Severity.note, "no-preheader",
            "No preview text. Without it, clients pull the first line of the "
            "body into the inbox preview, which is usually the greeting.",
        ))
    return out


def _body(body: str) -> list[Finding]:
    out = []
    stripped = body.strip()
    if not stripped:
        out.append(Finding(Severity.blocker, "empty-body", "The campaign has no body."))
        return out

    images = _IMAGE.findall(body)
    text_only = _IMAGE.sub("", body)
    text_only = _MD_LINK.sub(r"\1", text_only)
    words = len(re.findall(r"[A-Za-z']+", text_only))

    if len(stripped) < MIN_BODY_CHARS:
        out.append(Finding(
            Severity.warning, "very-short-body",
            "The body is very short. Filters treat a near-empty message with a "
            "link in it as the shape of a phishing attempt.",
        ))
    if images and words < 25:
        out.append(Finding(
            Severity.warning, "image-heavy",
            f"{len(images)} image(s) and only {words} words of text. Most clients "
            "block images by default, so this arrives nearly blank, and filters "
            "score image-only mail as spam.",
        ))

    lowered = body.lower()
    hits = [p for p in RISKY_PHRASES if p in lowered]
    if hits:
        out.append(Finding(
            Severity.note, "risky-phrases",
            "Contains phrases filters weight against: " + ", ".join(hits[:5]) + ".",
        ))
    if "{{" in _MD_LINK.sub("", body) and not re.search(
        r"\{\{\s*(first_name|full_name|company|email)\s*\}\}", body
    ):
        out.append(Finding(
            Severity.warning, "unknown-placeholder",
            "There is a {{ }} placeholder that is not one of first_name, "
            "full_name, company or email. It will be sent literally.",
        ))
    return out


def _links(body: str) -> list[Finding]:
    out = []
    hosts = [h.lower() for h in _URL.findall(body)]

    shorteners = sorted({h for h in hosts if any(s in h for s in SHORTENER_HOSTS)})
    if shorteners:
        out.append(Finding(
            Severity.warning, "link-shortener",
            "Uses link shorteners (" + ", ".join(shorteners) + "). They hide the "
            "destination, which is what phishing does, and click tracking already "
            "makes them pointless here.",
        ))

    insecure = sorted({m for m in re.findall(r"http://([^/\s)\"'>]+)", body, re.I)})
    if insecure:
        out.append(Finding(
            Severity.warning, "insecure-link",
            "Links to " + ", ".join(insecure) + " over plain http. Browsers warn "
            "on these and filters weight them.",
        ))

    # A link whose visible text is a *different* URL from its destination is
    # the classic phishing pattern, and it is easy to produce by accident when
    # editing a link's target and forgetting its label.
    for text, url in _MD_LINK.findall(body):
        text = text.strip()
        if text.lower().startswith(("http://", "https://")) and text.rstrip("/") != url.rstrip("/"):
            out.append(Finding(
                Severity.warning, "mismatched-link",
                f'A link reads "{text}" but points somewhere else. Filters treat '
                "that as deception, and so do recipients who notice.",
            ))
            break

    if not hosts:
        out.append(Finding(
            Severity.note, "no-links",
            "No links in the body, so there is nothing to measure beyond opens "
            "and replies — and opens are the least trustworthy figure here.",
        ))
    return out


def blockers(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == Severity.blocker]
