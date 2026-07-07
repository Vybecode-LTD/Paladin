# Changelog — Ashford & Briggs / Paladin

All notable changes to this project, in date order. Not committed to git yet as
formal tags/releases — this log tracks work sessions, not package versions.

## 2026-07-07 — Security hardening pass

Backend security-hardening batch, verified live against the running dev server.
Not yet committed to git (working tree has uncommitted changes to the files
listed below).

**Added**
- Rate limiting via `slowapi`: login endpoint limited to 10/min, demo-request
  submission limited to 5/hour. Wired through `backend/app/core/ratelimit.py`
  (a `Limiter` keyed by remote address) and registered in `backend/app/main.py`
  (`app.state.limiter`, `RateLimitExceeded` handler, `SlowAPIMiddleware`).
- Password length validation (8-128 chars) in `backend/app/schemas/auth.py`.
- Self-service password-change endpoint: `PATCH /api/auth/me/password`.
- Admin user-management endpoint: `PATCH /api/auth/users/{user_id}`.
- `max_length` caps on AI request schemas (`backend/app/schemas/ai.py`) to
  guard against unbounded prompt payloads to the Anthropic proxy.
- `AIServiceError` exception type in `backend/app/services/anthropic_service.py`,
  raised on Anthropic API failure and caught in `backend/app/routers/ai.py` to
  return a clean 502 instead of an unhandled 500.

**Fixed**
- Three unguarded `uuid.UUID()` calls that crashed with a raw unhandled 500 on
  malformed IDs, now returning clean 404/401:
  - `backend/app/middleware/auth.py` (`get_current_user`)
  - `backend/app/routers/auth.py` (`refresh`)
  - `backend/app/routers/blog_admin.py` (`_load_owned`, `admin_delete`)
  - See `docs/BUGS.md` BUG-001/002/003 for root cause and verification detail.
- `backend/.env.example` now defaults `DEBUG=false` instead of `DEBUG=true`
  (was shipping an insecure default for anyone copying the example file).

**Verified**
- Rate limiter confirmed live: 6th demo-request submission within an hour from
  the same client returns 429.
- Malformed UUIDs confirmed live: crafted bad-UUID inputs against all three
  fixed call sites return 404/401, not 500.
- Short passwords confirmed live: sub-8-character passwords rejected with 422.
- See `docs/TESTING.md` for full detail on how these were checked (manual
  curl-based verification against the local dev server — no automated test
  suite exists yet).

**Also this date (in progress, separate parallel effort — not part of this
entry's scope):** a UX/SEO/accessibility polish pass covering per-page SEO meta
tags, `robots.txt`/`sitemap.xml`/JSON-LD, a frontend 404 route, admin
sidebar/grid responsive CSS, click-to-copy in the admin post list, frontend
access-token refresh, Contact/How It Works content-parity fixes, and a GitHub
Actions CI pipeline. Not reflected as complete here — see `docs/ROADMAP.md`
phase 3 for status.

---

## 2026-07-06 (approx.) — Initial scaffold

Full project scaffold, built and verified compiling/rendering.

**Added**
- Backend: FastAPI app factory, async SQLAlchemy 2 (asyncpg) models (user,
  blog, demo_request), Alembic wiring, JWT + bcrypt auth
  (`backend/app/core/security.py`), RBAC middleware (`require_role`), routers
  for health/auth/blog (public + admin)/ai/demo, `anthropic_service.py` as a
  server-side proxy for AI blog generation, `seed.py` to create the first admin.
- Frontend: React 18 + Vite + TypeScript app. Five marketing pages (Home,
  Product, HowItWorks, About, Contact), blog reader (index + post), and a full
  admin surface (Login, Dashboard, PostList, DemoInbox, AI-assisted PostEditor).
  Dark-theme design system in `frontend/src/styles/tokens.css`.
- Docs: original single-page copy frozen verbatim in `docs/original-snapshot/`
  as a revert point; expanded/sharpened marketing copy drafted in
  `docs/content/` alongside a `SITEMAP.md`.
- Deploy scaffolding: `Dockerfile` + `railway.toml` for a single-service Railway
  deploy (FastAPI serves the built frontend as static files).

**Verified**
- Every backend Python file compiles clean (`python -m py_compile`).
- `__pycache__` cleaned before commit. 69 files total in the initial scaffold.

**Not done yet at this point:** dependencies not installed, `.env` not created,
no admin seeded, no live request against either server, no migration generated
(dev mode relies on lifespan auto-create-tables), no images/OG assets wired, not
deployed.
