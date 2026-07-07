import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.middleware.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.blog import BlogPost, PostStatus
from app.schemas.blog import PostCreate, PostUpdate, PostOut, PostListItem
from app.services.blog_service import unique_slug, apply_publish_transition

router = APIRouter()


@router.get("/admin/posts", response_model=list[PostListItem])
async def admin_list(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: PostStatus | None = Query(None, alias="status"),
):
    q = select(BlogPost)
    # Authors see only their own drafts; editors+ see everything.
    if user.role == UserRole.author:
        q = q.where(BlogPost.author_id == user.id)
    if status_filter:
        q = q.where(BlogPost.status == status_filter)
    q = q.order_by(desc(BlogPost.updated_at))
    rows = (await db.execute(q)).scalars().all()
    return [PostListItem.model_validate(r) for r in rows]


@router.post("/admin/posts", response_model=PostOut, status_code=201)
async def admin_create(payload: PostCreate,
                       user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    post = BlogPost(
        title=payload.title,
        slug=await unique_slug(db, payload.title),
        body_markdown=payload.body_markdown,
        excerpt=payload.excerpt,
        cover_image_url=payload.cover_image_url,
        status=payload.status,
        seo_title=payload.seo_title,
        seo_description=payload.seo_description,
        tags=payload.tags,
        author_id=user.id,
    )
    apply_publish_transition(post, payload.status)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return PostOut.model_validate(post)


def _parse_post_id(post_id: str) -> uuid.UUID:
    """uuid.UUID() raises a bare ValueError on malformed input — a mistyped
    or forged post_id in the URL should 404, not 500."""
    try:
        return uuid.UUID(post_id)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=404, detail="Post not found")


async def _load_owned(post_id: str, user: User, db: AsyncSession) -> BlogPost:
    post = (await db.execute(
        select(BlogPost).where(BlogPost.id == _parse_post_id(post_id))
    )).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    # Authors may only touch their own; editors+ may touch any.
    if user.role == UserRole.author and post.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not your post")
    return post


@router.get("/admin/posts/{post_id}", response_model=PostOut)
async def admin_get(post_id: str, user: User = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    return PostOut.model_validate(await _load_owned(post_id, user, db))


@router.patch("/admin/posts/{post_id}", response_model=PostOut)
async def admin_update(post_id: str, payload: PostUpdate,
                       user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    post = await _load_owned(post_id, user, db)
    data = payload.model_dump(exclude_unset=True)
    if "title" in data and data["title"] != post.title:
        post.slug = await unique_slug(db, data["title"], exclude_id=post.id)
    if "status" in data:
        apply_publish_transition(post, data["status"])
    for k, v in data.items():
        setattr(post, k, v)
    await db.commit()
    await db.refresh(post)
    return PostOut.model_validate(post)


@router.delete("/admin/posts/{post_id}", status_code=204)
async def admin_delete(post_id: str,
                       user: User = Depends(require_role(UserRole.editor)),
                       db: AsyncSession = Depends(get_db)):
    post = (await db.execute(
        select(BlogPost).where(BlogPost.id == _parse_post_id(post_id))
    )).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)
    await db.commit()
