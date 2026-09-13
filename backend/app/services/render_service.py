"""Turns a campaign plus one contact into the message that actually goes out.

Two rules shape everything here.

**The footer is not optional.** US law requires a valid physical postal
address on every marketing message, and Gmail and Yahoo require a working
one-click unsubscribe on bulk mail. Both are appended by this module rather
than left to whoever writes the campaign, because a footer that depends on an
author remembering it is a footer that will eventually be missing.

**Personalisation degrades, never breaks.** A missing first name renders a
neutral greeting; it never renders "Hi ," or "Hi {{first_name}},". The list is
imported data and some rows will be incomplete.
"""
import html as html_escape
import re

import markdown as markdown_lib

from app.models.campaign import Campaign
from app.models.contact import Contact
from app.services import link_service

# `extra` covers tables and fenced code; `sane_lists` stops a stray newline
# collapsing two lists into one, which is the most common surprise when a
# non-technical author writes the body.
MARKDOWN_EXTENSIONS = ["extra", "sane_lists"]

# Fallback when a contact has no first name. Chosen over "Hi," because a
# trailing comma with nothing before it reads as a bug to the recipient.
GREETING_FALLBACK = "there"

_PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")


def personalize(body: str, contact: Contact) -> str:
    """Substitute {{first_name}}, {{full_name}}, {{company}}, {{email}}.

    An unknown placeholder is left exactly as written rather than blanked:
    seeing `{{compnay}}` survive into a test send is how the author finds
    their typo, whereas silently emptying it hides the mistake until it
    reaches the list.
    """
    values = {
        "first_name": first_name_of(contact),
        "full_name": (contact.full_name or "").strip() or GREETING_FALLBACK,
        "company": (contact.company or "").strip(),
        "email": contact.email,
    }

    def replace(match: re.Match) -> str:
        key = match.group(1)
        return values.get(key, match.group(0))

    return _PLACEHOLDER.sub(replace, body)


def first_name_of(contact: Contact) -> str:
    full = (contact.full_name or "").strip()
    if not full:
        return GREETING_FALLBACK
    return full.split()[0]


def unsubscribe_url(tracking_base_url: str, token: str) -> str:
    """Served by routers/tracking.py. Built from the campaign subdomain, not
    the marketing site, so an unsubscribe link never depends on the main site
    being up and never carries campaign traffic onto it."""
    return f"{tracking_base_url.rstrip('/')}/t/u/{token}"


def list_unsubscribe_headers(url: str) -> dict[str, str]:
    """RFC 8058 one-click unsubscribe.

    Both headers are required together: List-Unsubscribe alone gives the
    client a link, but only the -Post header makes Gmail and Yahoo render the
    single-click control they now expect from bulk senders. An easy
    unsubscribe is what keeps people off the spam button, which is the
    heaviest negative signal a mailbox provider weighs.
    """
    return {
        "List-Unsubscribe": f"<{url}>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }


def body_links(campaign: Campaign) -> list[str]:
    """Trackable destinations in the body, in document order.

    Computed from the body alone, which is why the unsubscribe link can never
    be caught up in click tracking: it lives in the footer template, not in
    the Markdown, so it is not in what this function looks at. That is a
    structural guarantee rather than a rule someone has to remember.
    """
    rendered = markdown_lib.markdown(
        campaign.body_markdown or "", extensions=MARKDOWN_EXTENSIONS
    )
    return link_service.extract_links(rendered)


def render_text(
    campaign: Campaign,
    contact: Contact,
    *,
    unsubscribe: str,
    postal: str,
    links: list[str] | None = None,
    tracking_base_url: str = "",
    token: str = "",
) -> str:
    """Markdown source doubles as the plain-text part.

    Converting the HTML back to text would be lossy and produce artefacts;
    well-written Markdown already reads correctly as plain text, which is the
    reason the format won for email in the first place.
    """
    body = personalize(campaign.body_markdown or "", contact)
    if links and tracking_base_url and token:
        body = link_service.rewrite_text(body, links, tracking_base_url, token)
    footer = ["", "-" * 40]
    if postal:
        footer.append(postal)
    footer.append(f"Unsubscribe: {unsubscribe}")
    return body.rstrip() + "\n" + "\n".join(footer) + "\n"


def render_html(
    campaign: Campaign,
    contact: Contact,
    *,
    unsubscribe: str,
    postal: str,
    links: list[str] | None = None,
    tracking_base_url: str = "",
    token: str = "",
    embed_pixel: bool = False,
) -> str:
    """Markdown to an email-safe HTML document.

    Deliberately plain: a centred single column, inline styles, no external
    stylesheet and no web fonts. Every one of those is stripped or ignored by
    at least one major client, and a message that renders identically
    everywhere beats one that looks better in half the inboxes.

    `embed_pixel` is decided by the caller from the contact's tracking
    consent, never assumed here. A contact outside the US who has not agreed
    to open tracking receives the identical message with no pixel in it.
    """
    body = personalize(campaign.body_markdown or "", contact)
    rendered = markdown_lib.markdown(body, extensions=MARKDOWN_EXTENSIONS)
    if links and tracking_base_url and token:
        rendered = link_service.rewrite_html(rendered, links, tracking_base_url, token)

    pixel = (
        link_service.pixel_tag(tracking_base_url, token)
        if embed_pixel and tracking_base_url and token else ""
    )

    preheader = (campaign.preheader or "").strip()
    # Hidden preview text. Without it, clients pull the first line of the body
    # into the inbox preview, which is almost always the greeting.
    preheader_block = (
        f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;">'
        f"{html_escape.escape(preheader)}</div>"
        if preheader else ""
    )

    postal_block = (
        f'<div style="margin-bottom:8px;">{html_escape.escape(postal)}</div>'
        if postal else ""
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_escape.escape(campaign.subject or "")}</title>
</head>
<body style="margin:0;padding:0;background:#f4f7fb;">
{preheader_block}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f4f7fb;">
  <tr>
    <td align="center" style="padding:24px 12px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
             style="max-width:600px;background:#ffffff;border-radius:8px;">
        <tr>
          <td style="padding:32px 28px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;font-size:16px;line-height:1.55;color:#1a1c1f;">
{rendered}
          </td>
        </tr>
        <tr>
          <td style="padding:0 28px 28px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;font-size:12px;line-height:1.5;color:#6b6e72;border-top:1px solid #dee1e5;padding-top:20px;">
{postal_block}
            <div><a href="{html_escape.escape(unsubscribe)}" style="color:#0076d1;">Unsubscribe from these emails</a></div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
{pixel}
</body>
</html>
"""
