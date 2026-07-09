# Import EVERY model or Alembic autogenerate will DROP it. Cardinal rule.
from app.models.base import Base            # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.blog import BlogPost, PostStatus  # noqa: F401
from app.models.demo_request import DemoRequest    # noqa: F401
from app.models.smtp_settings import SmtpSettings  # noqa: F401
