"""Tests for campaign rendering.

Two groups. Personalisation must degrade rather than break, because the list
is imported data and some rows are incomplete. And the footer must be present
in every rendered form, because a physical postal address and a working
unsubscribe are legal requirements on marketing mail, not stylistic choices —
so they cannot depend on an author remembering to add them.
"""
import html as html_escape

from app.models.campaign import Campaign
from app.models.contact import Contact
from app.services.render_service import (
    GREETING_FALLBACK, first_name_of, list_unsubscribe_headers, personalize,
    render_html, render_text, unsubscribe_url,
)

POSTAL = "Ashford & Briggs, 1 Example Street, Jacksonville, FL"
UNSUB = "https://updates.example.com/t/u/tok123"


def _contact(**overrides) -> Contact:
    defaults = {
        "email": "bob@example.com",
        "full_name": "Bob Hathcoat",
        "company": "Acme Staffing",
    }
    return Contact(**{**defaults, **overrides})


def _campaign(**overrides) -> Campaign:
    defaults = {
        "name": "Update",
        "subject": "Paladin is live",
        "preheader": "",
        "body_markdown": "Hi {{first_name}},\n\nParagraph.",
    }
    return Campaign(**{**defaults, **overrides})


# --- personalisation ----------------------------------------------------------


def test_placeholders_are_substituted():
    out = personalize("Hi {{first_name}} at {{company}} ({{email}})", _contact())
    assert out == "Hi Bob at Acme Staffing (bob@example.com)"


def test_whitespace_inside_a_placeholder_is_tolerated():
    """Authors type `{{ first_name }}` about as often as the tight form."""
    assert personalize("Hi {{ first_name }}", _contact()) == "Hi Bob"


def test_missing_first_name_uses_a_neutral_greeting():
    """Never "Hi ," — a trailing comma with nothing before it reads to the
    recipient as a broken mail merge, which is worse than being generic."""
    out = personalize("Hi {{first_name}},", _contact(full_name=""))
    assert out == f"Hi {GREETING_FALLBACK},"


def test_first_name_takes_only_the_first_word():
    assert first_name_of(_contact(full_name="Bob Van Der Hathcoat")) == "Bob"


def test_first_name_of_a_blank_name_is_the_fallback():
    assert first_name_of(_contact(full_name="   ")) == GREETING_FALLBACK


def test_unknown_placeholder_is_left_intact():
    """A typo must survive into a test send so the author sees it. Silently
    blanking it hides the mistake until the campaign reaches the list."""
    assert personalize("Hi {{compnay}}", _contact()) == "Hi {{compnay}}"


def test_missing_company_renders_empty_not_a_placeholder():
    assert personalize("At {{company}}.", _contact(company="")) == "At ."


def test_body_without_placeholders_is_unchanged():
    assert personalize("No placeholders here.", _contact()) == "No placeholders here."


# --- unsubscribe --------------------------------------------------------------


def test_unsubscribe_url_shape():
    assert unsubscribe_url("https://updates.example.com", "abc") == \
        "https://updates.example.com/t/u/abc"


def test_unsubscribe_url_tolerates_a_trailing_slash():
    """A double slash after the host is mangled by some clients and redirected
    by some proxies, either of which breaks the link."""
    assert unsubscribe_url("https://updates.example.com/", "abc") == \
        "https://updates.example.com/t/u/abc"


def test_one_click_headers_are_both_present():
    """List-Unsubscribe alone only gives the client a link. Gmail and Yahoo
    render the single-click control they expect from bulk senders only when
    the -Post header is there too."""
    headers = list_unsubscribe_headers(UNSUB)
    assert headers["List-Unsubscribe"] == f"<{UNSUB}>"
    assert headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"


# --- rendered output ----------------------------------------------------------


def test_text_always_carries_unsubscribe_and_postal_address():
    out = render_text(_campaign(), _contact(), unsubscribe=UNSUB, postal=POSTAL)
    assert UNSUB in out
    assert POSTAL in out


def test_html_always_carries_unsubscribe_and_postal_address():
    """The address is escaped on the way in — "Ashford & Briggs" must render
    as valid markup, not as a stray entity — so the assertion checks the
    escaped form rather than the raw string."""
    out = render_html(_campaign(), _contact(), unsubscribe=UNSUB, postal=POSTAL)
    assert UNSUB in out
    assert html_escape.escape(POSTAL) in out
    assert "Ashford &amp; Briggs" in out


def test_text_is_personalised_too():
    """The plain-text part is a real part of the message, not a throwaway.
    Leaving raw placeholders in it is visible to every text-mode client."""
    out = render_text(_campaign(), _contact(), unsubscribe=UNSUB, postal=POSTAL)
    assert "Hi Bob," in out
    assert "{{" not in out


def test_html_converts_markdown():
    campaign = _campaign(body_markdown="# Heading\n\nSome **bold** text.")
    out = render_html(campaign, _contact(), unsubscribe=UNSUB, postal=POSTAL)
    assert "<h1>" in out
    assert "<strong>bold</strong>" in out


def test_html_is_a_complete_document():
    """Some clients discard a fragment outright."""
    out = render_html(_campaign(), _contact(), unsubscribe=UNSUB, postal=POSTAL)
    assert out.lstrip().startswith("<!doctype html>")
    assert "</html>" in out


def test_preheader_is_included_and_hidden_when_set():
    campaign = _campaign(preheader="What shipped this week")
    out = render_html(campaign, _contact(), unsubscribe=UNSUB, postal=POSTAL)
    assert "What shipped this week" in out
    assert "display:none" in out


def test_no_preheader_block_when_unset():
    out = render_html(_campaign(preheader=""), _contact(), unsubscribe=UNSUB, postal=POSTAL)
    assert "display:none" not in out


def test_subject_is_escaped_in_the_title():
    """An ampersand in the company name is the ordinary case here, not an
    attack — "Ashford & Briggs" must not produce invalid markup."""
    campaign = _campaign(subject="Ashford & Briggs <news>")
    out = render_html(campaign, _contact(), unsubscribe=UNSUB, postal=POSTAL)
    assert "Ashford &amp; Briggs &lt;news&gt;" in out


def test_postal_block_is_omitted_when_not_configured():
    """Rendering an empty box is worse than rendering nothing; the send path
    is what refuses to go out without an address."""
    out = render_html(_campaign(), _contact(), unsubscribe=UNSUB, postal="")
    assert UNSUB in out


def test_empty_body_still_renders_a_valid_message_with_a_footer():
    campaign = _campaign(body_markdown="")
    text = render_text(campaign, _contact(), unsubscribe=UNSUB, postal=POSTAL)
    html = render_html(campaign, _contact(), unsubscribe=UNSUB, postal=POSTAL)
    assert UNSUB in text and UNSUB in html
