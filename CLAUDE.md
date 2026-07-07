# CLAUDE.md — Ashford & Briggs Website

Context file for Claude Code. Read this first.

## What this is
Marketing website + blog with an AI-assisted admin backend for **Ashford & Briggs**
(Jacksonville, FL — founded 2026), makers of **Paladin**:
real-time AI intelligence for recruiting phone calls (skills-gap analysis, live
prompts, on-call jargon definitions, post-call summaries — through the recruiter's
existing phone, no app).

Expanded from an original single-page marketing site into a multi-page site + blog.
The verbatim original copy is frozen in `docs/original-snapshot/` as a revert point.

## Stack
- **Frontend:** React 18 + Vite + TypeScript, React Router, Framer Motion,
  react-markdown. Design-forward dark aesthetic (see `frontend/src/styles/tokens.css`).
- **Backend:** FastAPI + async SQLAlchemy 2 (asyncpg) + Alembic, Railway Postgres.
- **AI:** blog generation runs **server-side** via a FastAPI proxy to Anthropic
  (`backend/app/services/anthropic_service.py`) — the API key NEVER reaches the
  browser. Model: `claude-sonnet-4-6` (configurable via `ANTHROPIC_MODEL`).
- **Deploy target:** Any Docker host. The single `Dockerfile` builds the frontend
  then serves it + the API from one FastAPI process on `$PORT` (healthcheck at
  `/api/health`) — nothing about the image is Railway-specific. `railway.toml` is
  present for Railway specifically, but a plain
  `docker build -t paladin . && docker run -p 8000:8000 --env-file backend/.env paladin`
  works on any server. **If deploying under a domain other than
  `ashfordbriggs.com`**, update: `SITE_URL` in the backend env (feeds the dynamic
  `/sitemap.xml`), `frontend/public/robots.txt`'s `Sitemap:` line, and the
  hardcoded canonical/OG references in `frontend/index.html` and
  `frontend/src/components/Seo.tsx`.

## Monorepo layout
```
ashford-briggs/
├── backend/          FastAPI app (see backend/app/)
│   ├── app/
│   │   ├── core/         config (asyncpg URL normalization), db, security (JWT+bcrypt)
│   │   ├── middleware/    auth.py — get_current_user + require_role RBAC guard
│   │   ├── models/        user, blog, demo_request (+ __init__ imports ALL — cardinal)
│   │   ├── schemas/       pydantic contracts
│   │   ├── services/      anthropic_service (AI proxy), blog_service (slug/publish)
│   │   ├── routers/       health, auth, blog_public, blog_admin, ai, demo
│   │   └── main.py        app factory, CORS, routers under /api
│   ├── alembic/          async migrations
│   ├── seed.py           creates first admin
│   ├── Dockerfile, railway.toml, requirements.txt, .env.example
├── frontend/         React/Vite app
│   ├── src/
│   │   ├── pages/         Home, Product, HowItWorks, About, Contact, Blog*, admin/*
│   │   ├── layouts/       PublicLayout, AdminLayout (role-aware sidebar)
│   │   ├── context/       AuthContext
│   │   ├── lib/api.ts     API client + aiApi (calls own backend proxy)
│   │   └── styles/tokens.css
│   ├── package.json, vite.config.ts, tsconfig*.json, index.html
└── docs/
    ├── original-snapshot/   FROZEN verbatim original copy (revert point)
    └── content/             expanded/sharpened marketing copy + SITEMAP.md
```

## Roles (RBAC)
Three roles, ranked author(1) < editor(2) < admin(3), enforced by
`require_role(minimum)`:
- **author** — create/edit/publish OWN posts; use AI generation
- **editor** — all posts + delete + demo-request inbox
- **admin** — everything + provision users (`POST /api/auth/users`)

## Blog model
- Body stored as **Markdown**. Workflow is **draft → published** (two-state).
- `published_at` is stamped on first publish (`blog_service.apply_publish_transition`).
- Slugs auto-generated and de-duplicated (`blog_service.unique_slug`).

## Key conventions (per project owner)
- Use `python -m pip` / `python -m <module>` forms (bare `pip`/`python` not on PATH).
- Frontend AI calls hit our OWN backend proxy (`/api/admin/ai/*`), not Anthropic
  directly — the production-safe pattern; key stays server-side.
- `backend/app/models/__init__.py` imports EVERY model — never remove; Alembic
  autogenerate drops any unimported table.

## Local dev
```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env          # fill JWT_SECRET_KEY + ANTHROPIC_API_KEY
python -m seed                # create first admin (admin@ashfordbriggs.com / ChangeMe123!)
uvicorn app.main:app --reload # http://localhost:8000  (docs at /docs)

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173  (proxies /api -> :8000)
```

## AI blog generation endpoints (author+)
- `POST /api/admin/ai/draft`   {topic, tone, length} -> Markdown draft
- `POST /api/admin/ai/titles`  {topic} -> title options
- `POST /api/admin/ai/excerpt` {body_markdown} -> excerpt
- `POST /api/admin/ai/seo`     {title, body_markdown} -> {seo_title, seo_description}

---

## LAST COMPLETED TASK
As of 2026-07-07 — full scaffold, security hardening, and a UX/SEO/docs sweep
are all complete and verified (not just claimed):
- **Security hardening:** slowapi rate limiting (login 10/min, demo-request
  5/hour), three unguarded `uuid.UUID()` crash sites fixed (clean 401/404
  instead of unhandled 500s), password length validation + self-service
  password change + admin user-management endpoints, Anthropic proxy error
  handling, length caps on AI and demo-request request schemas.
- **SEO/UX/accessibility:** shared `<Seo>` component driving per-page
  title/description/canonical/JSON-LD, `robots.txt` + a **dynamic**
  `/sitemap.xml` (backend-generated — includes every published blog post,
  not just the static marketing routes), a 404 route, responsive admin
  sidebar/grids, a real access-token-refresh flow on the frontend, click-to-copy
  in the admin post list, Contact/How-It-Works content-parity fixes against
  `docs/content/`.
- **Infra/tooling:** GitHub Actions CI (`.github/workflows/ci.yml`), ESLint
  actually wired up (was referenced in `package.json` but never installed —
  fixed), `npm audit` clean (bumped Vite 5→6, not the major-breaking 5→8 jump
  `npm audit fix --force` suggested).
- **Already done, despite what older notes might imply:** the first Alembic
  migration (`109933857eb1_init`) is generated and applied to the dev DB;
  placeholder brand images/OG assets are in `frontend/public/images/`.
- Six project docs exist in `docs/`: `ROADMAP.md`, `BUGS.md`, `TESTING.md`,
  `CHANGELOG.md`, `HANDOFF.md`, `AUDIT-LOG.md` — read `docs/HANDOFF.md` first
  for full session-to-session state.

## NEXT STEPS (for Claude Code)
1. **Build the automated test suite** — this is the single biggest remaining
   gap. Zero automated tests exist for backend or frontend; every fix above
   was verified by hand (curl, browser checks), not by regression-safe tests.
   See `docs/TESTING.md` for the planned scope (pytest+httpx backend,
   Vitest+RTL frontend, ~45-65 cases).
2. **Deploy.** Being handed off to be self-hosted on someone else's own
   server — the Dockerfile is host-agnostic (see the Deploy target note
   above), so this is not Railway-only. Before deploying: set real env vars
   (`DATABASE_URL`, `JWT_SECRET_KEY`, `ANTHROPIC_API_KEY`, `CORS_ORIGINS`,
   `SITE_URL`), update the domain references listed above if not using
   `ashfordbriggs.com`, and run `python -m seed` once against the production
   DB to create the first admin login.
