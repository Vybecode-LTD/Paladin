import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class SmtpSettings(Base):
    """Company-wide SMTP connection config, used to send demo-request replies.
    Singleton in practice — the app only ever reads/writes a single row — but
    modeled as a normal table (not a KV blob) since it has a handful of
    typed fields. `encrypted_password` is Fernet-encrypted (app/core/crypto.py),
    never returned to the client in plaintext."""
    __tablename__ = "smtp_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    host: Mapped[str] = mapped_column(String(255), default="")
    port: Mapped[int] = mapped_column(Integer, default=587)
    username: Mapped[str] = mapped_column(String(255), default="")
    encrypted_password: Mapped[str | None] = mapped_column(String(500), nullable=True)
    use_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    from_name: Mapped[str] = mapped_column(String(200), default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
