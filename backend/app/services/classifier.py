"""Deciding whether an open or a click was a person or a machine.

This module is the reason the system exists. Roughly half of all tracked opens
industry-wide are Apple's automatic prefetch, and corporate security tools —
Microsoft Defender Safe Links, Proofpoint URL Defense, Mimecast URL Protect,
Barracuda — fetch every link in an email before the recipient ever sees it. A
dashboard that reports those as engagement is not measuring anything.

Two rules hold throughout, and both are deliberate:

**Nothing here ever returns `verified`.** A pixel fetch and a link redirect are
both things a machine can do perfectly. Verification only ever comes from
evidence a machine does not produce: the landing-page beacon, which needs
JavaScript to run, or a reply, which needs a person to write one. This module's
job is to sort the inferred pile, not to promote anything out of it.

**Every decision carries a reason string.** `classification` is stored on the
event so a wrong rule can be found and fixed later against real data, rather
than being a number nobody can account for. A heuristic nobody can audit is
worse than no heuristic.

Everything here is a pure function of the request, so the rules can be tested
without a database, a network, or a fixture.
"""
from app.models.email_event import EventTier

# Opens arriving within this window of the send are the mail system fetching
# images on delivery, not a person reading. Ten seconds is the figure the
# deliverability literature converges on; a human who opens that fast has
# almost certainly not read anything either.
PREFETCH_WINDOW_SECONDS = 10

# A scanner sweeping a message hits several distinct links in a few seconds.
# One person clicking two links that fast is possible but rare; four is not.
SWEEP_DISTINCT_LINKS = 3
SWEEP_WINDOW_SECONDS = 30

# Matched case-insensitively against the user agent. Deliberately a plain
# tuple: this list will need extending as vendors change, and the change
# should be one obvious line rather than a new branch in a function.
SCANNER_UA_FRAGMENTS = (
    "googleimageproxy",      # Gmail's image proxy, on every Gmail open
    "yahoomailproxy",
    "ms-office",             # Outlook / Microsoft 365 safe-attachment scanning
    "securityscan",
    "bingpreview",
    "proofpoint",
    "mimecast",
    "barracuda",
    "symantec",
    "messagelabs",
    "forcepoint",
    "trendmicro",
    "microsoftpreview",
    "skypeuripreview",
    "slackbot",              # link unfurling in a forwarded message
    "discordbot",
    "whatsapp",
    "telegrambot",
    "facebookexternalhit",
    "twitterbot",
    "linkedinbot",
    "curl/",
    "wget/",
    "python-requests",
    "python-httpx",
    "go-http-client",
    "okhttp",
    "java/",
    "libwww-perl",
    "headlesschrome",
    "phantomjs",
    "bot",                   # last: broad, so more specific rules run first
    "spider",
    "crawler",
)

# Hosts that appear as the referer when a security product's rewritten link
# sends a request our way. A referer we did not put there is strong evidence
# the click came through a scanner's infrastructure.
SCANNER_REFERER_HOSTS = (
    "urldefense.proofpoint.com",
    "urldefense.com",
    "safelinks.protection.outlook.com",
    "linkprotect.cudasvc.com",
    "protect-us.mimecast.com",
    "protect.mimecast.com",
    "clicktime.symantec.com",
    "protection.office.com",
)


def _ua(user_agent: str | None) -> str:
    return (user_agent or "").strip().lower()


def scanner_fragment(user_agent: str | None) -> str | None:
    """The first scanner signature found in the user agent, or None."""
    ua = _ua(user_agent)
    if not ua:
        return None
    for fragment in SCANNER_UA_FRAGMENTS:
        if fragment in ua:
            return fragment
    return None


def scanner_referer(referer: str | None) -> str | None:
    """The scanner host in the referer, or None."""
    value = (referer or "").strip().lower()
    if not value:
        return None
    for host in SCANNER_REFERER_HOSTS:
        if host in value:
            return host
    return None


def looks_like_apple_mpp(user_agent: str | None) -> bool:
    """Apple's Mail Privacy Protection relay, as best as it can be spotted.

    The relay sends a WebKit user agent with the browser identity stripped:
    no `Version/` and no `Safari/` token, which a real Safari always carries.
    Apple deliberately makes this hard, rotates the source addresses, and does
    not want to be identified — so this is a heuristic that will miss some of
    the traffic, and the honest handling is that opens stay inferred anyway.
    """
    ua = _ua(user_agent)
    if "applewebkit" not in ua:
        return False
    return "safari/" not in ua and "version/" not in ua and "chrome/" not in ua


def classify_open(
    *, user_agent: str | None, seconds_since_send: float | None,
) -> tuple[EventTier, str]:
    """Sort one pixel fetch. Always inferred — see the module docstring.

    Rules run most-specific first, so a Gmail proxy fetch is reported as
    exactly that rather than being swallowed by the broad `bot` fragment or
    by the timing rule.
    """
    fragment = scanner_fragment(user_agent)
    if fragment == "googleimageproxy":
        return EventTier.inferred, "google-image-proxy"
    if fragment == "yahoomailproxy":
        return EventTier.inferred, "yahoo-mail-proxy"
    if fragment is not None:
        return EventTier.inferred, f"scanner:{fragment}"

    if looks_like_apple_mpp(user_agent):
        return EventTier.inferred, "apple-mpp"

    if seconds_since_send is not None and seconds_since_send <= PREFETCH_WINDOW_SECONDS:
        return EventTier.inferred, "prefetch-timing"

    if not _ua(user_agent):
        # Every real mail client sends one. Its absence is not proof of a
        # machine, but it is not evidence of a person either.
        return EventTier.inferred, "no-user-agent"

    # Plausibly a person, and still only inferred: nothing about a pixel fetch
    # can prove one. A later click with a beacon, or a reply, is what turns
    # this recipient's engagement into something verified.
    return EventTier.inferred, "unclassified"


def classify_click(
    *,
    user_agent: str | None,
    referer: str | None = None,
    seconds_since_send: float | None = None,
    distinct_links_recently: int = 0,
) -> tuple[EventTier, str]:
    """Sort one redirect hit. Always inferred; the beacon is what promotes it.

    `distinct_links_recently` is how many different links in THIS message have
    been hit inside the sweep window. A security product opening a message
    walks every link in it within seconds, which is a pattern no person
    produces and which no user-agent check would catch on a scanner that
    forwards the recipient's own browser string.
    """
    fragment = scanner_fragment(user_agent)
    if fragment is not None:
        return EventTier.inferred, f"scanner:{fragment}"

    host = scanner_referer(referer)
    if host is not None:
        return EventTier.inferred, f"scanner-referer:{host}"

    if distinct_links_recently >= SWEEP_DISTINCT_LINKS:
        return EventTier.inferred, "scanner-sweep"

    if seconds_since_send is not None and seconds_since_send <= PREFETCH_WINDOW_SECONDS:
        return EventTier.inferred, "prefetch-timing"

    # A plausible human click. It stays inferred until the landing page's
    # beacon confirms a browser actually rendered the page, because a scanner
    # that forwards the recipient's user agent is indistinguishable from the
    # recipient at exactly this point.
    return EventTier.inferred, "click-unconfirmed"


def is_machine(classification: str) -> bool:
    """Whether a stored classification names a machine rather than a person.

    Used by reporting to split the inferred pile into "probably a person" and
    "definitely not", without re-running the rules over historic rows — the
    reason the classification is stored as a string rather than recomputed.
    """
    return (
        classification.startswith("scanner")
        or classification in {"google-image-proxy", "yahoo-mail-proxy", "apple-mpp", "prefetch-timing"}
    )
