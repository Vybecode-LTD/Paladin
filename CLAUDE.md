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
- **Deploy target:** Railway (Dockerfile + railway.toml present, healthcheck at
  `/api/health`).

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
Full scaffold complete and verified in the web session:
- Backend fully written; every Python file compiles clean (`python -m py_compile`).
- All frontend pages built (5 marketing pages + working demo form + blog reader +
  full admin: Login, Dashboard, PostList, DemoInbox, and the AI-assisted PostEditor).
- Original copy frozen in `docs/original-snapshot/`; expanded copy in `docs/content/`.
- `__pycache__` cleaned. 69 files total.

## NEXT STEPS (for Claude Code)
1. `cd backend && python -m pip install -r requirements.txt`; create `.env`;
   run `python -m seed`; start uvicorn. Confirm `/api/health` and `/docs`.
2. `cd frontend && npm install && npm run dev`. Confirm the site renders and the
   Contact demo form POSTs to `/api/demo-requests`.
3. Log into `/admin/login` with the seeded admin. Create a post via the AI
   composer (set `ANTHROPIC_API_KEY` first) and publish it; confirm it appears at
   `/blog`.
4. Generate the first real Alembic migration:
   `alembic revision --autogenerate -m "init"` then `alembic upgrade head`.
   (Dev mode auto-creates tables via lifespan; production relies on Alembic.)
5. Wire real images/OG assets (paths referenced in `index.html` + blog covers).
6. Deploy: push to Railway (Dockerfile + railway.toml ready); set env vars
   (DATABASE_URL auto-provided, JWT_SECRET_KEY, ANTHROPIC_API_KEY, CORS_ORIGINS).
   Point the frontend build at the deployed API and host it (static).
