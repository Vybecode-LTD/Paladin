"""Finding out where our own mail actually landed.

Delivery events say a provider accepted the message. They say nothing about
whether it reached an inbox, a spam folder, or Gmail's Promotions tab, and
that difference is invisible from the sending side. Mailboxes we own, that
receive every campaign, are the only way to see it — and to see it before a
client mentions it.

IMAP is blocking, so every call here runs in a worker thread. It is a handful
of connections a few times a day, which is not worth an async IMAP dependency.
"""
import asyncio
import imaplib
import logging

from app.core.crypto import decrypt_secret
from app.models.trust import Placement, SeedInbox

logger = logging.getLogger(__name__)

IMAP_TIMEOUT_SECONDS = 20

# The spam folder is called something different everywhere, and Gmail's
# Promotions is not a folder at all — it is a category, reachable only through
# Gmail's own search extension.
FOLDERS: dict[str, dict[str, str]] = {
    "gmail": {
        "inbox": "INBOX",
        "spam": "[Gmail]/Spam",
    },
    "outlook": {
        "inbox": "INBOX",
        "spam": "Junk",
    },
    "other": {
        "inbox": "INBOX",
        "spam": "Junk",
    },
}

DEFAULT_HOSTS = {
    "gmail": "imap.gmail.com",
    "outlook": "outlook.office365.com",
}


def imap_host_for(inbox: SeedInbox) -> str:
    return inbox.imap_host or DEFAULT_HOSTS.get(inbox.provider, "")


def _escape(value: str) -> str:
    """IMAP quoted strings escape backslash and double quote, nothing else."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _find_in_folder(client: imaplib.IMAP4_SSL, folder: str, subject: str) -> bool:
    try:
        status, _ = client.select(f'"{folder}"', readonly=True)
        if status != "OK":
            return False
        status, data = client.search(None, "SUBJECT", f'"{_escape(subject)}"')
        if status != "OK" or not data:
            return False
        return bool(data[0].split())
    except imaplib.IMAP4.error as exc:
        logger.info("could not search %s: %s", folder, exc)
        return False


def _check_blocking(
    *, host: str, port: int, username: str, password: str,
    provider: str, subject: str,
) -> tuple[Placement, str]:
    """One inbox, one campaign. Runs in a thread."""
    folders = FOLDERS.get(provider, FOLDERS["other"])
    client = None
    try:
        client = imaplib.IMAP4_SSL(host, port, timeout=IMAP_TIMEOUT_SECONDS)
        client.login(username, password)

        if _find_in_folder(client, folders["inbox"], subject):
            # Gmail delivers Promotions to INBOX but hides it behind a tab, so
            # a message can be "in the inbox" and still never be seen. Only
            # Gmail's own search extension can tell the difference.
            if provider == "gmail":
                try:
                    client.select('"INBOX"', readonly=True)
                    status, data = client.search(
                        None, "X-GM-RAW", f'"category:promotions subject:{subject}"'
                    )
                    if status == "OK" and data and data[0].split():
                        return Placement.promotions, "Gmail Promotions tab"
                except imaplib.IMAP4.error:
                    # The extension is unavailable on some accounts. Inbox is
                    # still the honest answer; it is just less specific.
                    pass
            return Placement.inbox, ""

        if _find_in_folder(client, folders["spam"], subject):
            return Placement.spam, ""

        return Placement.missing, "Not found in the inbox or the spam folder."
    except imaplib.IMAP4.error as exc:
        # Explicitly NOT `missing`. "We could not look" and "it did not
        # arrive" are different facts, and merging them would put a false
        # delivery alarm on the trust panel every time a password expires.
        return Placement.error, f"IMAP error: {exc}"
    except (OSError, TimeoutError) as exc:
        return Placement.error, f"Could not connect: {exc}"
    finally:
        if client is not None:
            try:
                client.logout()
            except (imaplib.IMAP4.error, OSError):
                pass


async def check_placement(inbox: SeedInbox, subject: str) -> tuple[Placement, str]:
    """Where `subject` landed in this seed inbox."""
    host = imap_host_for(inbox)
    if not host or not inbox.imap_username or not inbox.encrypted_password:
        return Placement.error, "This seed inbox is not fully configured."
    try:
        password = decrypt_secret(inbox.encrypted_password)
    except ValueError as exc:
        return Placement.error, f"Could not decrypt the password: {exc}"

    return await asyncio.to_thread(
        _check_blocking,
        host=host, port=inbox.imap_port or 993,
        username=inbox.imap_username, password=password,
        provider=inbox.provider, subject=subject,
    )
