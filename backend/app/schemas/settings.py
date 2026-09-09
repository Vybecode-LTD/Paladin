from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class SmtpSettingsOut(BaseModel):
    """Password is never returned — `password_set` tells the admin UI whether
    one is already stored, so it can show "leave blank to keep existing"."""
    host: str
    port: int
    username: str
    password_set: bool
    use_tls: bool
    from_name: str
    from_email: str
    updated_at: datetime | None = None


class SmtpSettingsUpdate(BaseModel):
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    username: str = Field(default="", max_length=255)
    # Omitted/None -> keep the existing stored password. Empty string is
    # treated the same as omitted (clearing a password via UI = leave blank).
    password: str | None = Field(default=None, max_length=500)
    use_tls: bool = True
    from_name: str = Field(default="", max_length=200)
    # Sender address for demo replies. Must be one the SMTP account may send
    # as; "" means "use the default" (email_service.DEMO_REPLY_FROM).
    from_email: EmailStr | Literal[""] = ""


class SmtpTestRequest(BaseModel):
    to_email: EmailStr
