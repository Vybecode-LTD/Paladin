from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.blog import BlogPost, PostStatus
from app.schemas.blog import PostOut, PostListItem

router = APIRouter()


@router.get("/blog/posts", response_model=list[PostListItem])
async def list_published(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=50),
    tag: str | None = None,
):
    q = select(BlogPost).where(BlogPost.status == PostStatus.published)
    if tag:
        q = q.where(BlogPost.tags.ilike(f"%{tag}%"))
    q = q.order_by(desc(BlogPost.published_at)).offset(skip).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [PostListItem.model_validate(r) for r in rows]


@router.get("/blog/posts/{slug}", response_model=PostOut)
async def get_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    q = select(BlogPost).where(
        BlogPost.slug == slug, BlogPost.status == PostStatus.published
    )
    post = (await db.execute(q)).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostOut.model_validate(post)
