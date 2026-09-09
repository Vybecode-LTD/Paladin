import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.campaign import CampaignStatus


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    subject: str
    preheader: str
    body_markdown: str
    status: CampaignStatus
    segment: str
    variant_b_subject: str
    holdout_percent: int
    scheduled_for: datetime | None
    sent_at: datetime | None
    error: str
    created_at: datetime
    updated_at: datetime


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    subject: str = Field(default="", max_length=500)
    preheader: str = Field(default="", max_length=300)
    body_markdown: str = Field(default="", max_length=200_000)
    segment: str = Field(default="", max_length=100)
    variant_b_subject: str = Field(default="", max_length=500)
    # A holdout above half the list stops being a control and starts being the
    # campaign, so the ceiling is deliberate rather than arbitrary.
    holdout_percent: int = Field(default=0, ge=0, le=50)


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    subject: str | None = Field(default=None, max_length=500)
    preheader: str | None = Field(default=None, max_length=300)
    body_markdown: str | None = Field(default=None, max_length=200_000)
    segment: str | None = Field(default=None, max_length=100)
    variant_b_subject: str | None = Field(default=None, max_length=500)
    holdout_percent: int | None = Field(default=None, ge=0, le=50)


class AudienceMember(BaseModel):
    """One row of the send preview."""
    email: str
    full_name: str
    variant: str
    trackable: bool


class AudiencePreview(BaseModel):
    """What a send would actually do, before it does it.

    Exists because the alternative to previewing is discovering the audience
    was wrong by mailing it.

    The four exclusion counts are mutually exclusive and, with `eligible`, sum
    to `total_contacts` — so an admin can always account for the difference
    between "contacts carrying this tag" and "people who will receive this".
    """
    total_contacts: int
    eligible: int
    suppressed: int
    excluded_inactive: int
    excluded_no_consent: int
    holdout: int
    variant_a: int
    variant_b: int
    untrackable: int
    sample: list[AudienceMember] = Field(default_factory=list)


class CampaignSendRequest(BaseModel):
    """Scheduling is optional. Omitted, the campaign is queued immediately and
    the next worker run picks it up."""
    scheduled_for: datetime | None = None


class CampaignTestRequest(BaseModel):
    """Sends the real rendered campaign to one address, bypassing the audience
    entirely. Never touches the suppression list or creates message rows —
    this is a proof, not a send."""
    to_email: EmailStr


class CampaignStats(BaseModel):
    """Counts per campaign, split by the tier of the underlying events so the
    dashboard can show what is proven separately from what is inferred."""
    campaign_id: uuid.UUID
    messages: int
    holdout: int
    sent: int
    failed: int
    accepted: int
    delivered: int
    soft_bounced: int
    hard_bounced: int
    complained: int
    unsubscribed: int
    opened_inferred: int
    clicked_inferred: int
    replied: int
