from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from app.core.config import settings
from app.core.database import engine
from app.core.ratelimit import limiter
from app.models import Base
from app.routers import (
    health, auth, blog_public, blog_admin, ai, demo,
)

# Populated by the Docker build's frontend stage (COPY --from=frontend-build
# .../dist ./static). Absent in local dev, where the frontend runs separately
# via the Vite dev server — everything below is a no-op in that case.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev convenience: create tables. In production use Alembic exclusively.
    if settings.debug:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (health, auth, blog_public, blog_admin, ai, demo):
    app.include_router(r.router, prefix="/api")


if STATIC_DIR.exists():
    # Production: single service serves the built React app on this same
    # origin. Real files (JS/CSS bundles, favicon, images) are served as-is;
    # any other path falls back to index.html for client-side routing.
    # Registered after the /api routers, so those still take precedence.
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        return {"service": settings.app_name, "docs": "/docs"}
