# CLAUDE.md — Ashford & Briggs Website

Context file for Claude Code. Read this first.

## If you're picking this up on a new machine — read this before doing anything

This repo was handed off from its original developer to be **self-hosted by
someone else, on their own infrastructure.** Before you create files, run
Docker, edit config, or make any deployment decision, **stop and ask the person
running you these questions.** Do not assume Railway, do not assume any
specific domain, and do not guess:

1. **Where is this being hosted?** (a VPS, a home server, a specific PaaS,
   etc.) — determines whether the `Dockerfile` alone is enough or whether
   platform-specific config is also needed.
2. **What domain (if any) will this run under?** If it's not
   `ashfordbriggs.com`, update `SITE_URL` (backend env — feeds the dynamic
   `/sitemap.xml`), `frontend/public/robots.txt`'s `Sitemap:` line, and the
   hardcoded canonical/OG references in `frontend/index.html` and
   `frontend/src/components/Seo.tsx`.
3. **Is Postgres already available**, or does one need to be provisioned? Get
   the real `DATABASE_URL` — don't default to the localhost placeholder in
   `.env.example`.
4. **Is Docker available** on the target machine? If yes, the single
   `Dockerfile` handles the *entire* build automatically — `npm ci` for the
   frontend, `pip install -r requirements.txt` for the backend — with **zero
   manual dependency installation needed**. If Docker isn't available, do a
   manual install per "Local dev" below, on whatever OS the target machine
   actually runs (don't assume Windows just because the original dev machine
   was Windows).
5. **What are the real secrets?** `JWT_SECRET_KEY` (generate a fresh random
   value, never reuse a dev one) and `ANTHROPIC_API_KEY` (the new owner's own
   key) must be supplied — neither is committed to this repo (see
   `.gitignore`).

Only proceed with deployment work once you have real answers to the above.
For an Ubuntu server the answers map straight onto `docs/DEPLOY-UBUNTU.md`,
which is the runbook to follow rather than improvising.
Guessing at any of them is how a deploy silently breaks — wrong CORS origin,
sitemap pointing at the wrong domain, a `DATABASE_URL` that doesn't exist.

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
  works on any server. **Self-managed Ubuntu/VPS: follow `docs/DEPLOY-UBUNTU.md`**
  (Docker Compose + Postgres + Caddy; files in `deploy/ubuntu/`; CI's
  `deploy-image` job builds and boots that exact image on every push).
  **If deploying under a domain other than
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
- Body stored as **Markdown**. Workflow is **draft → published**, reversible —
  the admin editor (`PostEditor.tsx`) has explicit Save draft / Publish-Update /
  **Unpublish** actions; unpublishing just PATCHes `status` back to `draft` and
  does not clear `published_at` (kept as history of the original publish date).
- `published_at` is stamped on first publish (`blog_service.apply_publish_transition`)
  and never re-stamped or cleared on later status changes.
- Slugs auto-generated and de-duplicated (`blog_service.unique_slug`).
- In-body images support an optional caption: the editor's "Insert image" button
  writes `![alt](url "caption")` — the quoted Markdown title becomes a real
  `<figure>/<figcaption>` via the shared `MarkdownImage` component (used by both
  the editor's Preview tab and the public post page). The cover/header image is
  a separate field (`cover_image_url`), unrelated to in-body images.

## Key conventions (per project owner)
- Use `python -m pip` / `python -m <module>` forms (bare `pip`/`python` not on PATH).
- Frontend AI calls hit our OWN backend proxy (`/api/admin/ai/*`), not Anthropic
  directly — the production-safe pattern; key stays server-side.
- `backend/app/models/__init__.py` imports EVERY model — never remove; Alembic
  autogenerate drops any unimported table.

## Local dev

**Manual install** (any OS — adjust the venv-activate line: `source .venv/bin/activate`
on Mac/Linux, `.venv\Scripts\activate` on Windows):
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

**Or skip all manual installs entirely** — see the "Deploy target" note under
Stack above: `docker build` runs `npm ci` and `pip install` for you as part of
the image build, so a Docker-based deploy needs no manual dependency step at
all. Only `python -m seed` (to create the first admin) needs to be run once
against whatever database the container ends up pointed at.

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
- **Blog editor completeness pass:** verified end-to-end (AI draft/titles/
  excerpt/SEO generation, editing already-published posts, delete) and closed
  two real gaps found during that verification — an **Unpublish** button now
  exists in `PostEditor.tsx` (the backend already supported the transition;
  there was just no UI control for it), and an **Insert image** button now
  supports captioned in-body images (see Blog model above).

## DEPLOYMENT (live) — as of 2026-09-08
- **Host:** Railway project **"Ashford & Briggs"**
  (id `006280bb-57cc-4b59-bc3a-0acfcc3fa623`), environment `production`.
  Exactly two services: **`Paladin`** (built from this repo's root
  `Dockerfile`, GitHub-connected to `main`, auto-deploys on every push) and
  **`Postgres`** (Railway plugin). Two stray `frontend`/`backend` services
  that failed on every push were deleted on 2026-09-09 — do not recreate
  them; this monorepo deploys as one service.
- **URL (temporary display domain):** https://puppyinfo.us — attached as a
  Railway custom domain on 2026-09-09 for demo/display purposes only. The
  generated Railway domain is https://paladin-production-c90f.up.railway.app
  (the earlier `-bc0b` one was regenerated and is dead). Health at
  `/api/health`, admin at `/admin/login`.
- **The real domain comes later.** `ashfordbriggs.com` is still hardcoded in
  the frontend (canonical/OG in `Seo.tsx` and `index.html`, `robots.txt`,
  JSON-LD in `Home.tsx`/`About.tsx`, the copy-link in `admin/PostList.tsx`,
  Privacy/Terms text). That is deliberate — leave it. When the site moves to
  its final domain, only `SITE_URL` and `CORS_ORIGINS` on the `Paladin`
  service need to change, unless the final domain is not `ashfordbriggs.com`.
- **Env vars on `Paladin`:** `DATABASE_URL=${{Postgres.DATABASE_URL}}` (a
  Railway reference, not a pasted URL), `JWT_SECRET_KEY`, `ENCRYPTION_KEY`,
  `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `DEBUG=false`, the JWT expiry
  settings, and the only two domain-dependent ones:
  `SITE_URL=https://puppyinfo.us` (feeds the dynamic `/sitemap.xml`) and
  `CORS_ORIGINS=https://puppyinfo.us,https://www.puppyinfo.us,https://paladin-production-c90f.up.railway.app`.
  Production secrets were generated fresh (not the dev ones); none are in git.
- **Start path:** the Dockerfile `CMD` runs `alembic upgrade head`, then
  `python -m seed` *only if* `SEED_ADMIN_PASSWORD` is set, then uvicorn. The
  first admin (`admin@ashfordbriggs.com`) was created this way on 2026-09-08
  and the seed variables were removed afterwards.
- **Next host (Ubuntu server, once the partners approve):**
  `docs/DEPLOY-UBUNTU.md` is the exact runbook; `deploy/ubuntu/` holds the
  Compose file, Caddyfile and `.env.example`. CI's `deploy-image` job builds
  the image and boots it against Postgres (migrations, seeded admin login,
  health) on every push, so the runbook's path is continuously tested.
- **Rate limiting behind a proxy:** the Dockerfile starts uvicorn with
  `--proxy-headers --forwarded-allow-ips='*'` so slowapi keys on the real
  client IP. Without it every visitor shares one bucket. Safe only because
  port 8000 is never published directly.
- **Gotchas learned the hard way — do not repeat:**
  1. A `startCommand` in `railway.toml` *or* in the service's dashboard
     settings overrides the Dockerfile CMD and silently skips migrations
     (symptom: every DB route 500s with `relation "blog_posts" does not
     exist` while `/api/health` is green). Keep both empty. Railway also
     ignored `preDeployCommand` from `railway.toml` (manifest showed `null`).
  2. Removing `startCommand` from `railway.toml` does **not** clear a value
     already stored on the service — it had to be cleared through the API
     (`serviceInstanceUpdate` with `startCommand: ""`).
  3. `railway redeploy` reuses the previous deployment's config snapshot; a
     settings change only takes effect on a *new* deployment (a push,
     `railway up`, or the `serviceInstanceDeploy` mutation).
  4. Project tokens cannot `railway ssh` / `railway run` against the
     container — hence the env-gated seed step in the CMD instead of a
     one-off command.

## NEXT STEPS (for Claude Code)
1. **Build the automated test suite** — this is the single biggest remaining
   gap. As of 2026-09-09 there are 7 backend unit tests
   (`backend/tests/test_svg_sanitize.py`, run by CI via `requirements-dev.txt`)
   plus CI's `deploy-image` end-to-end smoke test; everything else was
   verified by hand (curl, browser checks), not by regression-safe tests.
   See `docs/TESTING.md` for the planned scope (pytest+httpx backend,
   Vitest+RTL frontend, ~45-65 cases).
2. **Move to the real domain (later, per the owner).** The site currently
   runs on the temporary display domain puppyinfo.us (see DEPLOYMENT above).
   The final host will be a self-managed Ubuntu server: `docs/DEPLOY-UBUNTU.md`.
   When the final domain is ready: add it as a custom domain on the `Paladin`
   service in Railway, then change `SITE_URL` and `CORS_ORIGINS` on that
   service to the new origin. The frontend's hardcoded canonical/OG/JSON-LD
   references already say `ashfordbriggs.com`, so they need editing only if
   the final domain is something else. Delete the dead static
   `frontend/public/sitemap.xml` at that point — the backend generates the
   real one and wins the route.
