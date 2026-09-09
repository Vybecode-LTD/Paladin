"""Mailgun implementation of the Sender interface.

Chosen for campaigns because the company already operates Mailgun for the
product's password and PIN email, so there is no new vendor to approve, and
because its webhooks supply the three metrics raw SMTP cannot produce at all:
delivery confirmation, typed bounces, and spam complaints.

Campaigns MUST use a different sending domain from the product's transactional
mail. Sharing one merges campaign reputation with the most sensitive mail the
company sends; a complaint spike on a newsletter would then sit on the same
domain reputation that delivers a client's password reset.
"""
import hashlib
import hmac
import json
from typing import Any

import httpx

from app.models.sender_settings import MailgunRegion
from app.services.senders.base import (
    OutboundMessage, SendResult, SenderError,
)

BASE_URLS = {
    MailgunRegion.us: "https://api.mailgun.net",
    MailgunRegion.eu: "https://api.eu.mailgun.net",
}

# Matches the SMTP path's rationale: fail with a real error before the front
# proxy's ~30 s limit, so an admin clicking "test connection" sees what is
# actually wrong instead of an opaque gateway timeout.
REQUEST_TIMEOUT_SECONDS = 15.0


class MailgunSender:
    name = "mailgun"

    def __init__(
        self,
        *,
        domain: str,
        api_key: str,
        region: MailgunRegion = MailgunRegion.us,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ):
        if not domain:
            raise SenderError("Mailgun sending domain is not set — configure it in Settings.")
        if not api_key:
            raise SenderError("Mailgun API key is not set — configure it in Settings.")
        self._domain = domain
        self._api_key = api_key
        self._base = BASE_URLS[region]
        self._timeout = timeout

    # -- outbound -----------------------------------------------------------

    def _build_form(self, message: OutboundMessage) -> list[tuple[str, str]]:
        """Mailgun takes repeated form keys (several o:tag values, several
        recipients), so this is a list of pairs rather than a dict."""
        sender = (
            f'"{message.from_name}" <{message.from_email}>'
            if message.from_name else message.from_email
        )
        recipient = (
            f'"{message.to_name}" <{message.to_email}>'
            if message.to_name else message.to_email
        )
        form: list[tuple[str, str]] = [
            ("from", sender),
            ("to", recipient),
            ("subject", message.subject),
            ("text", message.text_body),
            # Mailgun's own open and click tracking is deliberately OFF. It
            # rewrites links onto a domain shared with its other customers,
            # whose behaviour we do not control and whose reputation we would
            # inherit inside our own mail. Tracking is served from our domain
            # instead (routers/tracking.py), which also keeps the tier
            # classification ours rather than a vendor's.
            ("o:tracking-opens", "no"),
            ("o:tracking-clicks", "no"),
        ]
        if message.html_body:
            form.append(("html", message.html_body))
        if message.reply_to:
            form.append(("h:Reply-To", message.reply_to))
        for key, value in message.headers.items():
            form.append((f"h:{key}", value))
        for key, value in message.variables.items():
            form.append((f"v:{key}", value))
        for tag in message.tags:
            form.append(("o:tag", tag))
        return form

    async def send(self, message: OutboundMessage) -> SendResult:
        url = f"{self._base}/v3/{self._domain}/messages"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    url, auth=("api", self._api_key), data=self._build_form(message),
                )
        except httpx.TimeoutException as exc:
            raise SenderError(f"Mailgun timed out: {exc}", retryable=True)
        except httpx.HTTPError as exc:
            raise SenderError(f"Could not reach Mailgun: {exc}", retryable=True)

        if response.status_code == 200:
            try:
                payload = response.json()
            except ValueError:
                raise SenderError("Mailgun accepted the message but returned no JSON.")
            message_id = str(payload.get("id", "")).strip()
            if not message_id:
                raise SenderError("Mailgun accepted the message but returned no id.")
            return SendResult(provider_message_id=message_id)

        raise _error_for(response)

    # -- configuration check ------------------------------------------------

    async def verify(self) -> None:
        """Confirms the key is valid AND the sending domain exists on this
        account, without sending mail. Checking the domain matters: a valid
        key with a typo'd domain fails only at the first real send, which on a
        campaign means discovering it in front of the whole list."""
        url = f"{self._base}/v3/domains/{self._domain}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, auth=("api", self._api_key))
        except httpx.TimeoutException as exc:
            raise SenderError(f"Mailgun timed out: {exc}", retryable=True)
        except httpx.HTTPError as exc:
            raise SenderError(f"Could not reach Mailgun: {exc}", retryable=True)

        if response.status_code == 200:
            return
        if response.status_code == 404:
            raise SenderError(
                f"Mailgun has no domain '{self._domain}' on this account. "
                "Check the sending domain, and that it is in the same region "
                "(US or EU) as the API key."
            )
        raise _error_for(response)


def _error_for(response: httpx.Response) -> SenderError:
    """Turn a non-200 into a SenderError whose retryable flag is right.

    401 and 400 are configuration mistakes; retrying them forever is how a
    queue jams. 429 and 5xx are worth another attempt.
    """
    detail = _detail_from(response)
    status = response.status_code
    if status == 401:
        return SenderError(
            "Mailgun rejected the API key. Check the key and its region "
            f"(US or EU). {detail}".strip()
        )
    if status == 429:
        return SenderError(f"Mailgun rate limit reached. {detail}".strip(), retryable=True)
    if status >= 500:
        return SenderError(f"Mailgun server error ({status}). {detail}".strip(), retryable=True)
    return SenderError(f"Mailgun rejected the request ({status}). {detail}".strip())


def _detail_from(response: httpx.Response) -> str:
    try:
        body: Any = response.json()
    except ValueError:
        return response.text[:200]
    if isinstance(body, dict):
        return str(body.get("message", ""))[:200]
    return str(body)[:200]


# -- inbound webhook verification -------------------------------------------


def verify_webhook_signature(
    *, signing_key: str, timestamp: str, token: str, signature: str,
) -> bool:
    """Mailgun signs every webhook: HMAC-SHA256 over timestamp+token, keyed
    with the HTTP webhook signing key.

    That key is a DIFFERENT credential from the API key — dashboard, Settings,
    API keys, HTTP webhook signing key — and using the API key here silently
    rejects every event.

    Compared in constant time. A plain `==` on a hex digest leaks how much of
    the signature matched, which is enough to forge one given enough tries,
    and a forged event could suppress a real contact or fake a delivery.
    """
    if not (signing_key and timestamp and token and signature):
        return False
    expected = hmac.new(
        key=signing_key.encode("utf-8"),
        msg=f"{timestamp}{token}".encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def parse_event(body: dict) -> dict:
    """Pull the event out of Mailgun's envelope.

    The POST body is {"signature": {...}, "event-data": {...}} — the parts
    this system cares about are inside event-data, and the signature block is
    consumed by verify_webhook_signature above.
    """
    data = body.get("event-data")
    return data if isinstance(data, dict) else {}


def dedupe_key_for(event: dict) -> str:
    """Mailgun retries a webhook until it gets a 200, so the same event can
    arrive several times. Its `id` is stable per event, which makes it the
    natural idempotency key; falling back to a hash of the whole body keeps a
    malformed event from colliding with a real one."""
    event_id = str(event.get("id", "")).strip()
    if event_id:
        return f"mailgun:{event_id}"
    digest = hashlib.sha256(
        json.dumps(event, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return f"mailgun:sha256:{digest}"
