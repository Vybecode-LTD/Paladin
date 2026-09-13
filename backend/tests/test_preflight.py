"""Tests for the pre-flight checks.

The blocker set is the part that matters. Those four findings are the
difference between a message that is legal and deliverable and one that is
not, and the send endpoint refuses on them — so a rule wrongly promoted to
blocker stops all sending, and one wrongly demoted lets an unlawful message
out. Everything else here is advice, and advice that fires too often gets
worked around.
"""
import pytest

from app.models.campaign import Campaign
from app.models.sender_settings import SenderSettings
from app.services.preflight_service import Severity, blockers, check


def _settings(**overrides) -> SenderSettings:
    defaults = {
        "from_email": "matt@updates.example.com",
        "tracking_base_url": "https://updates.example.com",
        "postal_address": "Ashford & Briggs, Jacksonville, FL",
        "reply_domain": "updates.example.com",
        "mailgun_domain": "updates.example.com",
        "from_name": "Matt",
    }
    return SenderSettings(**{**defaults, **overrides})


def _campaign(**overrides) -> Campaign:
    defaults = {
        "name": "Update",
        "subject": "Paladin is live for your team",
        "preheader": "What shipped this week",
        "body_markdown": (
            "Hi {{first_name}},\n\nPaladin is live. "
            "[Read what shipped](https://ashfordbriggs.com/product) when you have a moment.\n"
        ),
    }
    return Campaign(**{**defaults, **overrides})


def codes(findings) -> set[str]:
    return {f.code for f in findings}


# --- a good campaign ----------------------------------------------------------


def test_a_well_formed_campaign_has_no_blockers():
    assert blockers(check(_campaign(), _settings())) == []


def test_a_well_formed_campaign_is_quiet():
    """A checker that always complains is one people stop reading."""
    findings = check(_campaign(), _settings())
    assert [f for f in findings if f.severity != Severity.note] == []


# --- the blockers -------------------------------------------------------------


def test_no_sender_configured_blocks():
    assert "no-sender" in codes(blockers(check(_campaign(), None)))


@pytest.mark.parametrize(
    "missing,code",
    [
        ("from_email", "no-from-address"),
        ("tracking_base_url", "no-tracking-url"),
        ("postal_address", "no-postal-address"),
    ],
)
def test_each_required_setting_blocks_when_absent(missing, code):
    found = codes(blockers(check(_campaign(), _settings(**{missing: ""}))))
    assert code in found


def test_the_postal_address_blocker_says_why():
    """An admin who does not know it is a legal requirement will otherwise
    treat it as a nuisance field and put anything in it."""
    findings = check(_campaign(), _settings(postal_address=""))
    message = next(f.message for f in findings if f.code == "no-postal-address")
    assert "law" in message.lower()


def test_an_empty_subject_or_body_blocks():
    assert "no-subject" in codes(blockers(check(_campaign(subject=""), _settings())))
    assert "empty-body" in codes(blockers(check(_campaign(body_markdown="  "), _settings())))


def test_a_missing_reply_domain_warns_but_does_not_block():
    """Losing reply matching costs the most valuable B2B signal there is, but
    it does not make the message unlawful or undeliverable."""
    findings = check(_campaign(), _settings(reply_domain=""))
    assert "no-reply-domain" in codes(findings)
    assert "no-reply-domain" not in codes(blockers(findings))


# --- content warnings ---------------------------------------------------------


def test_a_shouting_subject_is_flagged():
    assert "shouting-subject" in codes(check(_campaign(subject="PALADIN IS LIVE NOW"), _settings()))


def test_a_normal_subject_with_an_acronym_is_not_flagged():
    """"Your AI update" must not trip the all-capitals rule."""
    assert "shouting-subject" not in codes(
        check(_campaign(subject="Your AI rollout update"), _settings())
    )


def test_excess_exclamation_marks_are_flagged():
    assert "excess-punctuation" in codes(
        check(_campaign(subject="Big news!!! Really!!"), _settings())
    )


def test_link_shorteners_are_flagged():
    campaign = _campaign(body_markdown="Read more at https://bit.ly/abc today.")
    assert "link-shortener" in codes(check(campaign, _settings()))


def test_plain_http_links_are_flagged():
    campaign = _campaign(body_markdown="See http://example.com/page for details.")
    assert "insecure-link" in codes(check(campaign, _settings()))


def test_a_link_whose_text_points_somewhere_else_is_flagged():
    """The classic phishing shape, and easy to produce by accident when
    editing a link target and forgetting its label."""
    campaign = _campaign(
        body_markdown="[https://ashfordbriggs.com](https://not-us.example/login)"
    )
    assert "mismatched-link" in codes(check(campaign, _settings()))


def test_an_ordinary_link_label_is_not_flagged_as_mismatched():
    assert "mismatched-link" not in codes(check(_campaign(), _settings()))


def test_an_image_only_body_is_flagged():
    campaign = _campaign(body_markdown="![banner](https://x.example/a.png)\n\nHi.")
    assert "image-heavy" in codes(check(campaign, _settings()))


def test_an_unknown_placeholder_is_flagged():
    """It would otherwise be sent literally, to the whole list."""
    campaign = _campaign(body_markdown="Hi {{frist_name}}, welcome.")
    assert "unknown-placeholder" in codes(check(campaign, _settings()))


def test_known_placeholders_are_not_flagged():
    campaign = _campaign(body_markdown="Hi {{first_name}} at {{company}}.")
    assert "unknown-placeholder" not in codes(check(campaign, _settings()))


def test_risky_phrases_are_a_note_not_a_warning():
    """Worth mentioning, not worth stopping anyone over."""
    campaign = _campaign(body_markdown="Act now for a risk free trial of Paladin.")
    findings = check(campaign, _settings())
    risky = next(f for f in findings if f.code == "risky-phrases")
    assert risky.severity == Severity.note


# --- ordering -----------------------------------------------------------------


def test_findings_are_returned_worst_first():
    findings = check(_campaign(subject="", body_markdown=""), _settings(postal_address=""))
    severities = [f.severity for f in findings]
    assert severities == sorted(severities, key=lambda s: [
        Severity.blocker, Severity.warning, Severity.note].index(s))
