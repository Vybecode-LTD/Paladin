from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.sender_settings import MailgunRegion, SenderProvider


class SenderSettingsOut(BaseModel):
    """Secrets are never returned. `api_key_set` and `webhook_secret_set` tell
    the admin UI whether one is already stored, so it can show "leave blank to
    keep existing" — same contract as SmtpSettingsOut."""
    provider: SenderProvider
    mailgun_domain: str
    mailgun_region: MailgunRegion
    api_key_set: bool
    webhook_secret_set: bool
    from_name: str
    from_email: str
    reply_domain: str
    tracking_base_url: str
    postal_address: str
    updated_at: datetime | None = None


class SenderSettingsUpdate(BaseModel):
    provider: SenderProvider = SenderProvider.smtp
    mailgun_domain: str = Field(default="", max_length=255)
    mailgun_region: MailgunRegion = MailgunRegion.us
    # Omitted, None or empty means "keep what is stored", matching the SMTP
    # password field the admin UI already behaves this way for.
    api_key: str | None = Field(default=None, max_length=500)
    webhook_secret: str | None = Field(default=None, max_length=500)

    from_name: str = Field(default="", max_length=200)
    from_email: EmailStr | Literal[""] = ""
    reply_domain: str = Field(default="", max_length=255)
    tracking_base_url: str = Field(default="", max_length=500)
    postal_address: str = Field(default="", max_length=500)

    @field_validator("tracking_base_url")
    @classmethod
    def _no_trailing_slash(cls, v: str) -> str:
        """Stored without a trailing slash so every caller can concatenate a
        path without producing a double slash, which some mail clients
        mangle and some proxies redirect."""
        return v.strip().rstrip("/")

    @field_validator("mailgun_domain", "reply_domain")
    @classmethod
    def _bare_domain(cls, v: str) -> str:
        """A bare hostname, not a URL. Pasting the dashboard URL in here is
        the obvious mistake, and it fails only at the first real send."""
        v = v.strip().lower()
        if v.startswith("http://") or v.startswith("https://"):
            raise ValueError("Enter a bare domain such as updates.example.com, not a URL.")
        return v.rstrip("/")


class SenderTestRequest(BaseModel):
    """Optional recipient. Omitted, this only verifies credentials and
    configuration without sending anything, which is what an admin usually
    wants and never bothers a real inbox."""
    to_email: EmailStr | None = None
