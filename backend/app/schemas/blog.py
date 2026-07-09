import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.blog import PostStatus


class PostCreate(BaseModel):
    title: str
    body_markdown: str = ""
    excerpt: str = ""
    cover_image_url: str = ""
    cover_image_svg: str = ""
    status: PostStatus = PostStatus.draft
    seo_title: str = ""
    seo_description: str = ""
    tags: str = ""


class PostUpdate(BaseModel):
    title: str | None = None
    body_markdown: str | None = None
    excerpt: str | None = None
    cover_image_url: str | None = None
    cover_image_svg: str | None = None
    status: PostStatus | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    tags: str | None = None


class PostOut(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    excerpt: str
    body_markdown: str
    cover_image_url: str
    cover_image_svg: str
    status: PostStatus
    seo_title: str
    seo_description: str
    tags: str
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    class Config:
        from_attributes = True


class PostListItem(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    excerpt: str
    cover_image_url: str
    cover_image_svg: str
    status: PostStatus
    tags: str
    published_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
