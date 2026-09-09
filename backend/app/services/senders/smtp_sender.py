"""SMTP implementation of the Sender interface, over the company SMTP
credentials already configured for demo replies.

Correct for internal test sends. NOT correct for campaigns to real
recipients, for reasons that are properties of the protocol and of the
account, not of this code:

  * SMTP reports only that the relay accepted the message. There is no
    delivery confirmation, no typed bounce and no spam-complaint feedback, so
    three of the four exact-tier metrics do not exist on this path.
  * The configured account is a Google Workspace mailbox. Workspace SMTP is
    for person-to-person mail; bulk sending through it is outside what the
    service is for, and it caps around 2,000 recipients a day.
  * Campaigns would send as a founder's own address on the root domain, so a
    complaint spike would land on the mailbox the founders use for business.

Kept, and kept working, because it costs almost nothing here and it means the
system can send to an internal seed segment before any provider exists — and
because the demo-reply path this borrows from must keep working untouched.
"""
from email.message import EmailMessage

import aiosmtplib

from app.services.email_service import smtp_tls_options
from app.services.senders.base import (
    OutboundMessage, SendResult, SenderError,
)

# Same rationale as email_service.SMTP_TIMEOUT_SECONDS: fail before the front
# proxy's ~30 s limit so the admin sees the real SMTP error.
SMTP_TIMEOUT_SECONDS = 15


class SmtpSender:
    name = "smtp"

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool,
        timeout: int = SMTP_TIMEOUT_SECONDS,
    ):
        if not host:
            raise SenderError("SMTP host is not set — configure it in Settings.")
        if not username or not password:
            raise SenderError("SMTP credentials are not set — configure them in Settings.")
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._timeout = timeout

    def _build(self, message: OutboundMessage) -> EmailMessage:
        email = EmailMessage()
        email["From"] = (
            f'"{message.from_name}" <{message.from_email}>'
            if message.from_name else message.from_email
        )
        email["To"] = (
            f'"{message.to_name}" <{message.to_email}>'
            if message.to_name else message.to_email
        )
        email["Subject"] = message.subject
        if message.reply_to:
            email["Reply-To"] = message.reply_to
        for key, value in message.headers.items():
            # Assigning to an existing key appends a duplicate header rather
            # than replacing it, which some receivers treat as malformed.
            if key in email:
                del email[key]
            email[key] = value

        # Plain text first, then HTML as the alternative. Order matters: a
        # client picks the LAST part it understands, so text-then-html gives
        # HTML clients the rich version and text clients a real body rather
        # than "this message has no content".
        email.set_content(message.text_body)
        if message.html_body:
            email.add_alternative(message.html_body, subtype="html")
        return email

    async def send(self, message: OutboundMessage) -> SendResult:
        email = self._build(message)
        try:
            await aiosmtplib.send(
                email,
                hostname=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                timeout=self._timeout,
                # Reused rather than reimplemented: this mapping is the fix
                # for BUG-007 (port 465 hung for 30 s on a plaintext socket)
                # and is pinned by tests/test_email_service.py.
                **smtp_tls_options(self._port, self._use_tls),
            )
        except aiosmtplib.SMTPRecipientsRefused as exc:
            raise SenderError(f"Recipient refused: {exc}")
        except aiosmtplib.SMTPAuthenticationError as exc:
            raise SenderError(
                "SMTP rejected the credentials. A Google account with 2-step "
                f"verification needs an app password, not the login password. {exc}"
            )
        except (aiosmtplib.SMTPException, OSError) as exc:
            # Transport-level failures are worth another attempt; auth and
            # recipient failures above are not, and are caught first.
            raise SenderError(f"Could not send email: {exc}", retryable=True)

        # SMTP returns no usable id, so the Message-Id the library generated
        # is what later correlation has to use.
        return SendResult(provider_message_id=str(email.get("Message-Id", "")))

    async def verify(self) -> None:
        """Connects and authenticates without sending anything. A campaign
        send must not be the first time we learn the password is wrong."""
        options = smtp_tls_options(self._port, self._use_tls)
        client = aiosmtplib.SMTP(
            hostname=self._host,
            port=self._port,
            timeout=self._timeout,
            use_tls=options["use_tls"],
        )
        try:
            await client.connect()
            if options["start_tls"]:
                await client.starttls()
            await client.login(self._username, self._password)
        except aiosmtplib.SMTPAuthenticationError as exc:
            raise SenderError(
                "SMTP rejected the credentials. A Google account with 2-step "
                f"verification needs an app password, not the login password. {exc}"
            )
        except (aiosmtplib.SMTPException, OSError) as exc:
            raise SenderError(f"Could not connect to the SMTP server: {exc}", retryable=True)
        finally:
            try:
                await client.quit()
            except (aiosmtplib.SMTPException, OSError):
                # The check already succeeded or failed on its own terms; a
                # noisy disconnect must not turn a good result into an error.
                pass
