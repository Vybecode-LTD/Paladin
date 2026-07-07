from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models.blog import BlogPost, PostStatus

router = APIRouter()

STATIC_ROUTES = ["/", "/product", "/how-it-works", "/about", "/contact", "/blog"]


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap(db: AsyncSession = Depends(get_db)):
    """Generated at request time so published blog posts are always included —
    the static frontend/public/sitemap.xml only covers the fixed marketing
    routes and is what local frontend-only dev falls back to."""
    posts = (await db.execute(
        select(BlogPost.slug, BlogPost.published_at)
        .where(BlogPost.status == PostStatus.published)
        .order_by(desc(BlogPost.published_at))
    )).all()

    urls = [f"  <url><loc>{settings.site_url}{path}</loc></url>" for path in STATIC_ROUTES]
    for slug, published_at in posts:
        lastmod = f"<lastmod>{published_at.date().isoformat()}</lastmod>" if published_at else ""
        urls.append(f"  <url><loc>{settings.site_url}/blog/{slug}</loc>{lastmod}</url>")

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n"
        "</urlset>\n"
    )
    return Response(content=xml, media_type="application/xml")
