import uuid
from datetime import datetime, timezone
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.blog import BlogPost, PostStatus


async def unique_slug(db: AsyncSession, title: str,
                      exclude_id: uuid.UUID | None = None) -> str:
    base = slugify(title) or "post"
    slug = base
    n = 2
    while True:
        q = select(BlogPost).where(BlogPost.slug == slug)
        if exclude_id:
            q = q.where(BlogPost.id != exclude_id)
        exists = (await db.execute(q)).scalar_one_or_none()
        if not exists:
            return slug
        slug = f"{base}-{n}"
        n += 1


def apply_publish_transition(post: BlogPost, new_status: PostStatus) -> None:
    """Stamp published_at on first publish."""
    if new_status == PostStatus.published and post.published_at is None:
        post.published_at = datetime.now(timezone.utc)
