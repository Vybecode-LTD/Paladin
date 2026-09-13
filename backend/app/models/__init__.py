# Import EVERY model or Alembic autogenerate will DROP it. Cardinal rule.
from app.models.base import Base            # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.blog import BlogPost, PostStatus  # noqa: F401
from app.models.demo_request import DemoRequest    # noqa: F401
from app.models.smtp_settings import SmtpSettings  # noqa: F401

# --- Email campaign analytics ------------------------------------------------
from app.models.contact import Contact, ConsentBasis, ContactStatus  # noqa: F401
from app.models.suppression import Suppression, SuppressionReason  # noqa: F401
from app.models.sender_settings import (  # noqa: F401
    SenderSettings, SenderProvider, MailgunRegion,
)
from app.models.campaign import Campaign, CampaignStatus  # noqa: F401
from app.models.campaign_message import CampaignMessage  # noqa: F401
from app.models.email_event import EmailEvent, EventType, EventTier  # noqa: F401
from app.models.trust import (  # noqa: F401
    DmarcRecord, SeedInbox, SeedPlacement, Placement, BlocklistResult,
)
