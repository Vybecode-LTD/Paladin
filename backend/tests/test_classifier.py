"""Tests for the open and click classifier.

The first test in this file is the one that matters most. Everything else is
detail about which machine was spotted; that one pins the invariant the whole
tier system rests on, and it is the invariant a future change is most likely
to break by accident while trying to make the numbers look better.
"""
import pytest

from app.models.email_event import EventTier
from app.services.classifier import (
    PREFETCH_WINDOW_SECONDS, SWEEP_DISTINCT_LINKS, classify_click,
    classify_open, is_machine, looks_like_apple_mpp, scanner_fragment,
    scanner_referer,
)

CHROME = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
SAFARI = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
          "(KHTML, like Gecko) Version/17.1 Safari/605.1.15")
# Apple's relay sends the same WebKit string with the browser identity removed.
APPLE_MPP = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
             "(KHTML, like Gecko)")
GMAIL_PROXY = ("Mozilla/5.0 (Windows NT 5.1; rv:11.0) Gecko Firefox/11.0 "
               "(via ggpht.com GoogleImageProxy)")

LATER = 3600.0  # an hour after send: well outside every timing rule


# --- the invariant ------------------------------------------------------------


@pytest.mark.parametrize("ua", [CHROME, SAFARI, APPLE_MPP, GMAIL_PROXY, "", None])
@pytest.mark.parametrize("age", [0.0, 5.0, 60.0, LATER, None])
def test_an_open_is_never_verified(ua, age):
    """A pixel fetch is something a machine does perfectly. Nothing about one
    can prove a person, so no combination of inputs may ever produce a
    verified open — the beacon and a reply are the only sources of that tier."""
    tier, _ = classify_open(user_agent=ua, seconds_since_send=age)
    assert tier == EventTier.inferred


@pytest.mark.parametrize("ua", [CHROME, SAFARI, GMAIL_PROXY, "", None])
def test_a_click_is_never_verified_at_the_redirect(ua):
    """Same reasoning: a scanner can forward the recipient's own browser
    string, so the redirect cannot tell them apart. The landing-page beacon
    is what promotes a click."""
    tier, _ = classify_click(user_agent=ua, seconds_since_send=LATER)
    assert tier == EventTier.inferred


def test_every_decision_carries_a_reason():
    """The classification string is stored on the event so a wrong rule can be
    found against real data later. An empty one would make the row
    unaccountable."""
    for ua in (CHROME, GMAIL_PROXY, APPLE_MPP, "", None):
        _, why = classify_open(user_agent=ua, seconds_since_send=LATER)
        assert why


# --- proxies and scanners -----------------------------------------------------


def test_gmail_image_proxy_is_named_specifically():
    """Named rather than lumped in with scanners, because it is on every
    single Gmail open and its volume is worth seeing separately."""
    _, why = classify_open(user_agent=GMAIL_PROXY, seconds_since_send=LATER)
    assert why == "google-image-proxy"


@pytest.mark.parametrize(
    "ua",
    [
        "Mozilla/5.0 ms-office",
        "SecurityScan/1.0",
        "Mozilla/5.0 (compatible; BingPreview/1.0b)",
        "proofpoint-urldefense",
        "Mimecast Scanner",
        "curl/8.4.0",
        "python-requests/2.31.0",
        "Go-http-client/2.0",
    ],
)
def test_known_machine_agents_are_flagged(ua):
    _, why = classify_open(user_agent=ua, seconds_since_send=LATER)
    assert why.startswith("scanner:") or why in {"google-image-proxy", "yahoo-mail-proxy"}


@pytest.mark.parametrize("ua", [CHROME, SAFARI])
def test_real_browsers_are_not_flagged_as_scanners(ua):
    """The list of fragments ends with broad terms like "bot". A false
    positive here would silently discard real engagement, which is a worse
    failure than counting a scanner."""
    assert scanner_fragment(ua) is None


def test_rule_order_puts_the_specific_before_the_broad():
    """The Gmail proxy string would also match nothing else, but the ordering
    matters for agents that contain several fragments; this pins that the
    specific name wins rather than a generic `scanner:bot`."""
    _, why = classify_open(user_agent=GMAIL_PROXY, seconds_since_send=1.0)
    assert why == "google-image-proxy", "a named proxy must beat the timing rule too"


# --- Apple Mail Privacy Protection --------------------------------------------


def test_apple_relay_shape_is_recognised():
    assert looks_like_apple_mpp(APPLE_MPP)


def test_real_safari_is_not_mistaken_for_the_relay():
    """Safari carries Version/ and Safari/ tokens; the relay strips them.
    Getting this backwards would discard every genuine open from a Mac."""
    assert not looks_like_apple_mpp(SAFARI)


def test_chrome_is_not_mistaken_for_the_relay():
    assert not looks_like_apple_mpp(CHROME)


def test_apple_relay_is_classified_as_such():
    _, why = classify_open(user_agent=APPLE_MPP, seconds_since_send=LATER)
    assert why == "apple-mpp"


# --- timing -------------------------------------------------------------------


@pytest.mark.parametrize("age", [0.0, 1.0, PREFETCH_WINDOW_SECONDS])
def test_opens_inside_the_prefetch_window_are_machine_opens(age):
    _, why = classify_open(user_agent=CHROME, seconds_since_send=age)
    assert why == "prefetch-timing"


def test_opens_after_the_window_are_not_blamed_on_timing():
    _, why = classify_open(user_agent=CHROME, seconds_since_send=PREFETCH_WINDOW_SECONDS + 1)
    assert why == "unclassified"


def test_unknown_send_time_does_not_trigger_the_timing_rule():
    """A message with no sent_at is one the worker has not sent yet. Absent
    data must not be read as evidence."""
    _, why = classify_open(user_agent=CHROME, seconds_since_send=None)
    assert why == "unclassified"


def test_missing_user_agent_is_recorded_as_such():
    _, why = classify_open(user_agent="", seconds_since_send=LATER)
    assert why == "no-user-agent"


# --- clicks -------------------------------------------------------------------


@pytest.mark.parametrize(
    "referer",
    [
        "https://urldefense.proofpoint.com/v2/url?u=...",
        "https://eur01.safelinks.protection.outlook.com/?url=...",
        "https://linkprotect.cudasvc.com/url?a=...",
        "https://protect-us.mimecast.com/s/abc",
    ],
)
def test_a_scanner_referer_is_caught_even_with_a_real_browser_string(referer):
    """The case user-agent checks miss entirely: a security product that
    forwards the recipient's own browser string but still leaves its own
    rewriting host in the referer."""
    assert scanner_referer(referer) is not None
    _, why = classify_click(user_agent=CHROME, referer=referer, seconds_since_send=LATER)
    assert why.startswith("scanner-referer:")


def test_an_ordinary_referer_is_not_a_scanner():
    assert scanner_referer("https://mail.google.com/") is None


def test_sweeping_several_links_at_once_is_a_scanner():
    """No person clicks three different links in one message within thirty
    seconds; a product scanning the message walks all of them."""
    _, why = classify_click(
        user_agent=CHROME, seconds_since_send=LATER,
        distinct_links_recently=SWEEP_DISTINCT_LINKS,
    )
    assert why == "scanner-sweep"


def test_one_or_two_links_is_still_a_plausible_person():
    for count in range(SWEEP_DISTINCT_LINKS):
        _, why = classify_click(
            user_agent=CHROME, seconds_since_send=LATER, distinct_links_recently=count,
        )
        assert why == "click-unconfirmed"


def test_a_plausible_click_says_it_is_unconfirmed_not_that_it_is_human():
    """The wording is the point: the system has no evidence either way until
    the beacon reports, and the stored reason should not claim otherwise."""
    _, why = classify_click(user_agent=CHROME, seconds_since_send=LATER)
    assert why == "click-unconfirmed"


# --- reporting helper ----------------------------------------------------------


@pytest.mark.parametrize(
    "classification",
    ["google-image-proxy", "yahoo-mail-proxy", "apple-mpp", "prefetch-timing",
     "scanner:curl/", "scanner-sweep", "scanner-referer:urldefense.com"],
)
def test_machine_classifications_are_recognised_as_machines(classification):
    assert is_machine(classification)


@pytest.mark.parametrize("classification", ["unclassified", "click-unconfirmed",
                                            "beacon-confirmed", "no-user-agent"])
def test_non_machine_classifications_are_not(classification):
    """`no-user-agent` is deliberately not counted as a machine: it is an
    absence of evidence, and treating it as proof would quietly discard real
    opens from clients that send no agent string."""
    assert not is_machine(classification)
