"""The seam between "what to send" and "how it leaves the building".

Everything above this interface — campaign expansion, consent checks, link
rewriting, suppression — is provider-agnostic. Everything below it is one
vendor's API. That boundary is the reason a provider change is a settings
change rather than a rewrite, and it is why the SMTP path used for demo
replies can keep working untouched while campaigns go somewhere else.
"""
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class OutboundMessage:
    """One rendered message for one recipient.

    Already fully rendered: tracking links rewritten, pixel embedded or
    deliberately absent, unsubscribe footer present. A sender's only job is to
    put this on the wire — it never edits the body, because a sender that
    rewrites content would make two providers produce different mail from the
    same campaign.
    """
    to_email: str
    subject: str
    text_body: str
    html_body: str
    from_email: str
    to_name: str = ""
    from_name: str = ""
    # Per-message address so a reply can be matched to its campaign and
    # recipient without parsing the body.
    reply_to: str = ""
    # Extra headers. List-Unsubscribe and List-Unsubscribe-Post live here:
    # required for bulk mail by Gmail and Yahoo, and an easy unsubscribe is
    # what keeps people off the spam button.
    headers: dict[str, str] = field(default_factory=dict)
    # Metadata the provider echoes back on every event for this message, which
    # is how a delivery or bounce webhook finds its CampaignMessage row.
    # Providers that have no such concept simply ignore it.
    variables: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SendResult:
    """`provider_message_id` is stored on the CampaignMessage so later webhook
    events can be matched to it. Senders with no id of their own return the
    message id they generated themselves."""
    provider_message_id: str


class SenderError(Exception):
    """A send that did not happen.

    `retryable` separates "try again in a minute" (rate limited, provider 5xx,
    connection dropped) from "this will never work" (bad credentials, rejected
    address, malformed request). The worker retries only the first kind;
    retrying the second is how a queue spins forever on a message that can
    never leave.
    """

    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class Sender(Protocol):
    """Implemented by services/senders/smtp_sender.py and mailgun_sender.py."""

    name: str

    async def send(self, message: OutboundMessage) -> SendResult:
        """Put one message on the wire. Raises SenderError on failure."""
        ...

    async def verify(self) -> None:
        """Check credentials and configuration without sending mail to a real
        recipient. Backs the admin "test connection" button, so it must fail
        fast and with a message an admin can act on. Raises SenderError."""
        ...
