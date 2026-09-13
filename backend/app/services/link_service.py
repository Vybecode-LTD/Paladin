"""Rewriting the links in a campaign so clicks can be counted.

Links are numbered per campaign, not per recipient: everyone receives the same
body, so link 3 is the same destination for all of them and the number can be
stored once on the campaign. The redirect then needs only the recipient's
message token and that index, which keeps the URL short — it appears in mail
that can never be edited again.

Two things are deliberately never rewritten. The unsubscribe link, because
wrapping a compliance-critical link puts an extra failure point in front of
the one action a recipient is legally entitled to complete, and because an
unsubscribe is not marketing engagement to be counted. And anything that is
not http or https, because a rewritten `mailto:` is simply broken.
"""
import html as html_escape
import re

# Matches the href of an anchor in the rendered HTML. The body is produced by
# our own Markdown renderer rather than pasted in, so the shape is predictable
# and a parser would be more machinery than the job needs.
_HREF = re.compile(r'href="([^"]*)"', re.IGNORECASE)

TRACKABLE_SCHEMES = ("http://", "https://")


def _is_trackable(url: str) -> bool:
    return url.lower().startswith(TRACKABLE_SCHEMES)


def extract_links(html: str, *, exclude: set[str] | None = None) -> list[str]:
    """Ordered, de-duplicated list of trackable destinations in the body.

    De-duplicated because the same destination appearing twice — a button and
    a text link to the same page — is one link that was clicked, not two. The
    order is document order, so the numbering is stable for as long as the
    body is, and a campaign's body is frozen once it is queued.
    """
    skip = {u.rstrip("/") for u in (exclude or set())}
    seen: list[str] = []
    for raw in _HREF.findall(html):
        url = html_escape.unescape(raw).strip()
        if not _is_trackable(url):
            continue
        if url.rstrip("/") in skip:
            continue
        if url not in seen:
            seen.append(url)
    return seen


def click_url(tracking_base_url: str, token: str, index: int) -> str:
    return f"{tracking_base_url.rstrip('/')}/t/c/{token}/{index}"


def pixel_url(tracking_base_url: str, token: str) -> str:
    """`.png` on the end purely so it looks like an image to anything
    inspecting the URL; the endpoint serves a GIF, which is the smallest
    thing every client renders."""
    return f"{tracking_base_url.rstrip('/')}/t/o/{token}.png"


def beacon_url(tracking_base_url: str, token: str) -> str:
    return f"{tracking_base_url.rstrip('/')}/t/b/{token}"


def rewrite_html(html: str, links: list[str], tracking_base_url: str, token: str) -> str:
    """Point every tracked anchor at the redirect.

    Matching is done on the escaped form as it appears in the attribute, since
    the Markdown renderer turns `&` into `&amp;` inside a query string and a
    comparison against the raw URL would silently miss every link that has
    more than one parameter.
    """
    if not links or not tracking_base_url:
        return html
    index_of = {url: i for i, url in enumerate(links)}

    def replace(match: re.Match) -> str:
        raw = match.group(1)
        url = html_escape.unescape(raw).strip()
        index = index_of.get(url)
        if index is None:
            return match.group(0)
        return f'href="{html_escape.escape(click_url(tracking_base_url, token, index))}"'

    return _HREF.sub(replace, html)


def rewrite_text(text: str, links: list[str], tracking_base_url: str, token: str) -> str:
    """Same substitution for the plain-text part.

    Longest URL first, so a link that is a prefix of another — a site root and
    a page beneath it — cannot have the shorter one replaced inside the longer
    one and corrupt both.
    """
    if not links or not tracking_base_url:
        return text
    for url in sorted(links, key=len, reverse=True):
        text = text.replace(url, click_url(tracking_base_url, token, links.index(url)))
    return text


def pixel_tag(tracking_base_url: str, token: str) -> str:
    """The open pixel.

    `width`/`height` attributes as well as the style, because Outlook ignores
    CSS on images often enough that a bare styled image can render as a
    visible broken-image box in the middle of the message. `alt=""` keeps a
    screen reader from announcing it.
    """
    src = html_escape.escape(pixel_url(tracking_base_url, token))
    return (
        f'<img src="{src}" alt="" width="1" height="1" border="0" '
        f'style="display:block;width:1px;height:1px;border:0;outline:none;" />'
    )
