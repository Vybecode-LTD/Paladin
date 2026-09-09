import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.contact import ConsentBasis, ContactStatus


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    company: str
    country: str
    consent_basis: ConsentBasis
    consent_recorded_at: datetime | None
    consent_note: str
    tracking_consent: bool
    status: ContactStatus
    tags: list[str]
    engagement_score: int
    last_engaged_at: datetime | None
    created_at: datetime


class ContactCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(default="", max_length=200)
    company: str = Field(default="", max_length=200)
    country: str = Field(default="", max_length=2)
    consent_basis: ConsentBasis = ConsentBasis.unknown
    consent_note: str = Field(default="", max_length=2000)
    tracking_consent: bool = False
    tags: list[str] = Field(default_factory=list, max_length=20)


class ContactUpdate(BaseModel):
    """Every field optional — a PATCH sets only what it names. `status` is
    included so an admin can retire or reactivate someone deliberately, but
    setting it to anything is still subject to the suppression list, which no
    edit here can override."""
    full_name: str | None = Field(default=None, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    country: str | None = Field(default=None, max_length=2)
    consent_basis: ConsentBasis | None = None
    consent_note: str | None = Field(default=None, max_length=2000)
    tracking_consent: bool | None = None
    tags: list[str] | None = Field(default=None, max_length=20)
    status: ContactStatus | None = None


class ContactImportRow(BaseModel):
    email: EmailStr
    full_name: str = Field(default="", max_length=200)
    company: str = Field(default="", max_length=200)
    country: str = Field(default="", max_length=2)
    consent_basis: ConsentBasis = ConsentBasis.unknown
    consent_note: str = Field(default="", max_length=2000)
    tracking_consent: bool = False
    tags: list[str] = Field(default_factory=list, max_length=20)


class ContactImportRequest(BaseModel):
    # Capped at a size one HTTP request can carry comfortably and one
    # transaction can hold. Larger lists arrive as several calls, which also
    # gives the admin partial progress instead of one long silence.
    rows: list[ContactImportRow] = Field(min_length=1, max_length=1000)


class ContactImportResult(BaseModel):
    created: int
    updated: int
    skipped: int


class SuppressionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    reason: str
    note: str
    created_at: datetime
