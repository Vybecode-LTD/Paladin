"""Tests for click-link extraction and rewriting.

Two failures here are worse than losing the metric. Rewriting the unsubscribe
link would put an extra failure point in front of the one action a recipient
is legally entitled to complete. And a URL corrupted by a careless replacement
sends someone to a broken page from mail that can never be corrected.
"""
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.services.link_service import (
    click_url, extract_links, pixel_tag, pixel_url, rewrite_html, rewrite_text,
)
from app.services.render_service import body_links, render_html, render_text

BASE = "https://updates.example.com"
TOKEN = "tok123"
UNSUB = f"{BASE}/t/u/{TOKEN}"
POSTAL = "Ashford & Briggs, Jacksonville, FL"


def _campaign(body: str) -> Campaign:
    return Campaign(
        name="C", subject="S", preheader="", body_markdown=body,
    )


def _contact() -> Contact:
    return Contact(email="bob@example.com", full_name="Bob Hathcoat", company="Acme")


# --- extraction ---------------------------------------------------------------


def test_links_are_extracted_in_document_order():
    html = '<a href="https://a.example">a</a> <a href="https://b.example">b</a>'
    assert extract_links(html) == ["https://a.example", "https://b.example"]


def test_the_same_destination_twice_is_one_link():
    """A button and a text link to the same page is one link that was
    clicked, not two, and both must map to the same index."""
    html = '<a href="https://a.example">one</a> <a href="https://a.example">two</a>'
    assert extract_links(html) == ["https://a.example"]


def test_non_http_schemes_are_left_alone():
    """A rewritten mailto: is simply broken."""
    html = ('<a href="mailto:x@example.com">mail</a>'
            '<a href="tel:+15550100">call</a>'
            '<a href="https://a.example">web</a>')
    assert extract_links(html) == ["https://a.example"]


def test_excluded_urls_are_skipped_regardless_of_trailing_slash():
    html = '<a href="https://a.example/">a</a><a href="https://b.example">b</a>'
    assert extract_links(html, exclude={"https://a.example"}) == ["https://b.example"]


def test_escaped_ampersands_are_unescaped_for_storage():
    """Markdown renders `&` in a query string as `&amp;`. Storing the escaped
    form would send visitors to a URL with a literal &amp; in it."""
    html = '<a href="https://a.example/?x=1&amp;y=2">a</a>'
    assert extract_links(html) == ["https://a.example/?x=1&y=2"]


# --- rewriting ----------------------------------------------------------------


def test_html_links_are_pointed_at_the_redirect():
    html = '<a href="https://a.example">a</a>'
    out = rewrite_html(html, ["https://a.example"], BASE, TOKEN)
    assert click_url(BASE, TOKEN, 0) in out
    assert 'href="https://a.example"' not in out


def test_a_url_with_query_parameters_is_matched_despite_escaping():
    """The failure this prevents: every link with more than one parameter
    silently not being tracked, because the attribute holds `&amp;` while the
    stored URL holds `&`."""
    html = '<a href="https://a.example/?x=1&amp;y=2">a</a>'
    links = ["https://a.example/?x=1&y=2"]
    out = rewrite_html(html, links, BASE, TOKEN)
    assert click_url(BASE, TOKEN, 0) in out


def test_links_not_in_the_list_are_left_untouched():
    html = '<a href="https://a.example">a</a><a href="https://other.example">o</a>'
    out = rewrite_html(html, ["https://a.example"], BASE, TOKEN)
    assert 'href="https://other.example"' in out


def test_a_url_that_is_a_prefix_of_another_is_not_corrupted():
    """Replacing the shorter first would rewrite it *inside* the longer one
    and break both. Ordering by length is what prevents it."""
    text = "Root: https://a.example and page: https://a.example/deep/page"
    links = ["https://a.example", "https://a.example/deep/page"]
    out = rewrite_text(text, links, BASE, TOKEN)
    assert click_url(BASE, TOKEN, 0) in out
    assert click_url(BASE, TOKEN, 1) in out
    assert "https://a.example/deep/page" not in out.replace(click_url(BASE, TOKEN, 1), "")


def test_rewriting_is_a_no_op_without_a_tracking_url():
    """A campaign sent before the tracking host is configured must still be a
    valid message, just an unmeasured one."""
    html = '<a href="https://a.example">a</a>'
    assert rewrite_html(html, ["https://a.example"], "", TOKEN) == html


# --- the unsubscribe link is structurally safe --------------------------------


def test_body_links_never_include_the_unsubscribe_url():
    """Not a rule someone has to remember: the unsubscribe lives in the footer
    template, and body_links only ever looks at the Markdown body, so it
    cannot be picked up for rewriting."""
    campaign = _campaign("Hello [site](https://a.example).")
    assert body_links(campaign) == ["https://a.example"]


def test_rendered_unsubscribe_link_is_not_rewritten():
    campaign = _campaign("Hello [site](https://a.example).")
    html = render_html(
        campaign, _contact(), unsubscribe=UNSUB, postal=POSTAL,
        links=["https://a.example"], tracking_base_url=BASE, token=TOKEN,
    )
    assert UNSUB in html, "the unsubscribe must survive rewriting verbatim"
    assert click_url(BASE, TOKEN, 0) in html, "the body link must be rewritten"


# --- the pixel ----------------------------------------------------------------


def test_pixel_is_embedded_only_when_asked():
    campaign = _campaign("Hello.")
    with_pixel = render_html(
        campaign, _contact(), unsubscribe=UNSUB, postal=POSTAL,
        tracking_base_url=BASE, token=TOKEN, embed_pixel=True,
    )
    without = render_html(
        campaign, _contact(), unsubscribe=UNSUB, postal=POSTAL,
        tracking_base_url=BASE, token=TOKEN, embed_pixel=False,
    )
    assert pixel_url(BASE, TOKEN) in with_pixel
    assert pixel_url(BASE, TOKEN) not in without


def test_a_message_without_a_pixel_is_otherwise_identical():
    """A contact who has not consented to open tracking receives the same
    message, not a lesser one."""
    campaign = _campaign("Hello [site](https://a.example).")
    args = dict(
        unsubscribe=UNSUB, postal=POSTAL, links=["https://a.example"],
        tracking_base_url=BASE, token=TOKEN,
    )
    with_pixel = render_html(campaign, _contact(), embed_pixel=True, **args)
    without = render_html(campaign, _contact(), embed_pixel=False, **args)
    # Removing the pixel tag from one must yield the other exactly: the
    # difference between a tracked and an untracked message is the pixel and
    # nothing else, so the recipient sees identical content either way.
    assert with_pixel.replace(pixel_tag(BASE, TOKEN), "") == without
    assert click_url(BASE, TOKEN, 0) in without, "links are still tracked without a pixel"


def test_pixel_carries_explicit_dimensions():
    """Outlook ignores CSS on images often enough that a bare styled image can
    render as a visible broken-image box in the middle of the message."""
    tag = pixel_tag(BASE, TOKEN)
    assert 'width="1"' in tag and 'height="1"' in tag
    assert 'alt=""' in tag


def test_text_part_is_rewritten_too():
    campaign = _campaign("Visit https://a.example today.")
    text = render_text(
        campaign, _contact(), unsubscribe=UNSUB, postal=POSTAL,
        links=["https://a.example"], tracking_base_url=BASE, token=TOKEN,
    )
    assert click_url(BASE, TOKEN, 0) in text
    assert UNSUB in text
