import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class PostStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(300))
    slug: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    excerpt: Mapped[str] = mapped_column(String(500), default="")
    body_markdown: Mapped[str] = mapped_column(Text, default="")
    cover_image_url: Mapped[str] = mapped_column(String(500), default="")
    # AI-generated vector header (self-contained, sanitized <svg> markup). Kept
    # in its own Text column — an SVG far exceeds cover_image_url's String(500),
    # and separating them keeps "pasted photo URL" distinct from "generated
    # header." Rendered SVG-first, falling back to cover_image_url.
    cover_image_svg: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[PostStatus] = mapped_column(
        SAEnum(PostStatus, name="post_status"), default=PostStatus.draft, index=True
    )
    seo_title: Mapped[str] = mapped_column(String(300), default="")
    seo_description: Mapped[str] = mapped_column(String(500), default="")
    tags: Mapped[str] = mapped_column(String(500), default="")  # comma-separated

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    author = relationship("User", lazy="joined")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
