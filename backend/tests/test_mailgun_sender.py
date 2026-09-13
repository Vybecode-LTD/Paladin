"""Tests for the Mailgun sender: webhook signature verification, event
parsing, and the outbound form.

Signature verification is security-critical — a forged event could suppress a
real contact or fabricate a delivery — and the form assertions pin the two
settings that are easy to lose in a refactor and silently wrong afterwards:
Mailgun's own open and click tracking must stay OFF, because it rewrites
links onto a domain shared with its other customers.
"""
import hashlib
import hmac

import pytest

from app.models.sender_settings import MailgunRegion
from app.services.senders.base import OutboundMessage, SenderError
from app.services.senders.mailgun_sender import (
    BASE_URLS, MailgunSender, dedupe_key_for, parse_event,
    verify_webhook_signature,
)

SIGNING_KEY = "test-webhook-signing-key"


def _sign(timestamp: str, token: str, key: str = SIGNING_KEY) -> str:
    return hmac.new(
        key=key.encode("utf-8"),
        msg=f"{timestamp}{token}".encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


# --- webhook signature --------------------------------------------------------


def test_valid_signature_is_accepted():
    ts, token = "1770920772", "e0b5477167110d68991efc6b9f89f0a11066af27834600e123"
    assert verify_webhook_signature(
        signing_key=SIGNING_KEY, timestamp=ts, token=token, signature=_sign(ts, token)
    )


def test_signature_from_a_different_key_is_rejected():
    """The webhook signing key is a different credential from the API key.
    Using the API key here would reject every real event, so this pins that
    the key actually participates in the result."""
    ts, token = "1770920772", "abc123"
    wrong = _sign(ts, token, key="the-api-key-not-the-signing-key")
    assert not verify_webhook_signature(
        signing_key=SIGNING_KEY, timestamp=ts, token=token, signature=wrong
    )


def test_tampered_timestamp_is_rejected():
    ts, token = "1770920772", "abc123"
    signature = _sign(ts, token)
    assert not verify_webhook_signature(
        signing_key=SIGNING_KEY, timestamp="1770920773", token=token, signature=signature
    )


def test_tampered_token_is_rejected():
    ts, token = "1770920772", "abc123"
    signature = _sign(ts, token)
    assert not verify_webhook_signature(
        signing_key=SIGNING_KEY, timestamp=ts, token="abc124", signature=signature
    )


@pytest.mark.parametrize("missing", ["signing_key", "timestamp", "token", "signature"])
def test_any_missing_field_fails_closed(missing):
    """An unconfigured signing key must reject every event rather than wave
    them through. Failing open here would let anyone POST a complaint for any
    address and have it suppressed."""
    args = {
        "signing_key": SIGNING_KEY,
        "timestamp": "1770920772",
        "token": "abc123",
    }
    args["signature"] = _sign(args["timestamp"], args["token"])
    args[missing] = ""
    assert not verify_webhook_signature(**args)


def test_signature_of_the_wrong_length_is_rejected_not_raised():
    """compare_digest raises on mismatched types, not lengths, but a truncated
    hex string is the shape a naive forgery attempt takes — it must return
    False rather than blow up inside the webhook route."""
    ts, token = "1770920772", "abc123"
    assert not verify_webhook_signature(
        signing_key=SIGNING_KEY, timestamp=ts, token=token, signature="deadbeef"
    )


# --- event parsing ------------------------------------------------------------


def test_parse_event_unwraps_the_envelope():
    body = {
        "signature": {"token": "t", "timestamp": "1", "signature": "s"},
        "event-data": {"event": "delivered", "recipient": "bob@example.com"},
    }
    assert parse_event(body) == {"event": "delivered", "recipient": "bob@example.com"}


def test_parse_event_on_a_malformed_body_returns_empty():
    assert parse_event({}) == {}
    assert parse_event({"event-data": "not-a-dict"}) == {}


def test_dedupe_key_uses_the_event_id():
    """Mailgun retries a webhook until it gets a 200, so the same event
    arrives repeatedly and must collapse to one row."""
    assert dedupe_key_for({"id": "YusK9KhoTwe2C00iRxsEqQ"}) == "mailgun:YusK9KhoTwe2C00iRxsEqQ"


def test_dedupe_key_is_stable_without_an_id():
    event = {"event": "delivered", "recipient": "bob@example.com", "timestamp": 1.5}
    assert dedupe_key_for(event) == dedupe_key_for(dict(reversed(list(event.items()))))


def test_dedupe_keys_differ_for_different_events():
    a = dedupe_key_for({"event": "delivered", "recipient": "a@example.com"})
    b = dedupe_key_for({"event": "delivered", "recipient": "b@example.com"})
    assert a != b


# --- outbound form ------------------------------------------------------------


def _sender() -> MailgunSender:
    return MailgunSender(domain="updates.example.com", api_key="key-abc", region=MailgunRegion.us)


def _form(message: OutboundMessage) -> list[tuple[str, str]]:
    return _sender()._build_form(message)


BASE_MESSAGE = OutboundMessage(
    to_email="bob@example.com",
    subject="Deployment update",
    text_body="Hello.",
    html_body="<p>Hello.</p>",
    from_email="matt@updates.example.com",
)


def test_mailgun_tracking_is_always_disabled():
    """Ours is served from our own domain (routers/tracking.py). Mailgun's
    rewrites links onto a shared domain whose reputation we do not control,
    inside our own mail."""
    form = _form(BASE_MESSAGE)
    assert ("o:tracking-opens", "no") in form
    assert ("o:tracking-clicks", "no") in form


def test_friendly_names_are_quoted_when_present():
    message = OutboundMessage(
        **{**BASE_MESSAGE.__dict__, "from_name": "Matt", "to_name": "Bob"}
    )
    form = dict(_form(message))
    assert form["from"] == '"Matt" <matt@updates.example.com>'
    assert form["to"] == '"Bob" <bob@example.com>'


def test_bare_addresses_when_no_name():
    form = dict(_form(BASE_MESSAGE))
    assert form["from"] == "matt@updates.example.com"
    assert form["to"] == "bob@example.com"


def test_html_is_omitted_when_empty_rather_than_sent_blank():
    """An empty html part makes some clients render nothing at all instead of
    falling back to the text part."""
    text_only = OutboundMessage(**{**BASE_MESSAGE.__dict__, "html_body": ""})
    assert "html" not in dict(_form(text_only))
    assert "html" in dict(_form(BASE_MESSAGE))


def test_variables_are_prefixed_so_they_come_back_on_events():
    message = OutboundMessage(
        **{**BASE_MESSAGE.__dict__, "variables": {"message_token": "abc123"}}
    )
    assert ("v:message_token", "abc123") in _form(message)


def test_headers_are_prefixed():
    message = OutboundMessage(
        **{**BASE_MESSAGE.__dict__,
           "headers": {"List-Unsubscribe": "<https://x.example/u/1>"}}
    )
    assert ("h:List-Unsubscribe", "<https://x.example/u/1>") in _form(message)


def test_reply_to_is_sent_as_a_header():
    message = OutboundMessage(
        **{**BASE_MESSAGE.__dict__, "reply_to": "replies+abc@updates.example.com"}
    )
    assert ("h:Reply-To", "replies+abc@updates.example.com") in _form(message)


def test_multiple_tags_are_repeated_keys_not_joined():
    """Mailgun takes repeated form keys. Joining them with commas produces one
    tag literally named "a,b"."""
    message = OutboundMessage(**{**BASE_MESSAGE.__dict__, "tags": ["campaign-7", "ab-a"]})
    tags = [v for k, v in _form(message) if k == "o:tag"]
    assert tags == ["campaign-7", "ab-a"]


# --- configuration ------------------------------------------------------------


def test_regions_map_to_different_hosts():
    """An EU key against the US host fails with a confusing 401, so the region
    has to be a real setting rather than an assumption."""
    assert BASE_URLS[MailgunRegion.us] != BASE_URLS[MailgunRegion.eu]
    assert "eu" in BASE_URLS[MailgunRegion.eu]


def test_missing_domain_or_key_is_a_clear_error_at_construction():
    """Fail while building the sender, not on the first message of a campaign."""
    with pytest.raises(SenderError):
        MailgunSender(domain="", api_key="key-abc")
    with pytest.raises(SenderError):
        MailgunSender(domain="updates.example.com", api_key="")
