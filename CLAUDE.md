# CLAUDE.md — Ashford & Briggs Website

Context file for Claude Code. Read this first, then `docs/HANDOFF.md` for current state.

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
5. **What are the real secrets?** `JWT_SECRET_KEY` and `ENCRYPTION_KEY` (fresh
   random values, never reused from dev — `ENCRYPTION_KEY` protects the stored
   SMTP and Mailgun credentials, so changing it later means re-entering them) and
   `ANTHROPIC_API_KEY` (the new owner's own key) must be supplied — none is
   committed to this repo (see `.gitignore`). Mailgun credentials are entered in
   the admin UI, not the environment.

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

Since 2026-09-09 it also contains an **email campaign analytics system** (admin →
Analytics): consented contacts, campaigns sent through Mailgun, tracking, and
statistics that label every figure with how far it can be trusted. Design:
`docs/EMAIL-ANALYTICS.md`. Setup path, with who does each step:
`docs/EMAIL-SETUP-RUNBOOK.md`.

## Stack
- **Frontend:** React 18 + Vite + TypeScript, React Router, Framer Motion,
  react-markdown. Design-forward dark aesthetic (see `frontend/src/styles/tokens.css`).
- **Backend:** FastAPI + async SQLAlchemy 2 (asyncpg) + Alembic, PostgreSQL.
  Stored credentials are encrypted with Fernet (`app/core/crypto.py`).
- **AI:** blog generation runs **server-side** via a FastAPI proxy to Anthropic
  (`backend/app/services/anthropic_service.py`) — the API key NEVER reaches the
  browser. Model: `claude-sonnet-4-6` (configurable via `ANTHROPIC_MODEL`).
- **Email:** demo-request replies go through the company's SMTP server; campaigns
  go through **Mailgun**, with SMTP as a fallback that cannot report delivery,
  bounces or complaints. Both are configured in admin → Settings.
- **Background worker:** `python -m app.worker` runs one pass and exits, driven by
  a systemd timer (`deploy/ubuntu/paladin-worker.service` + `.timer`). It sends due
  campaigns and runs the domain-trust checks; a Postgres advisory lock stops
  overlapping passes.
- **Deploy target:** Any Docker host. The single `Dockerfile` builds the frontend
  then serves it + the API from one FastAPI process on `$PORT` (healthcheck at
  `/api/health`) — nothing about the image is host-specific. A plain
  `docker build -t paladin . && docker run -p 8000:8000 --env-file backend/.env paladin`
  works on any server. **Self-managed Ubuntu/VPS: follow `docs/DEPLOY-UBUNTU.md`**
  (Docker Compose + Postgres + Caddy; files in `deploy/ubuntu/`; CI's
  `deploy-image` job builds and boots that exact image on every push). **The
  compose stack has no worker service** — add one per section 5.5, or campaigns
  never send. **If deploying under a domain other than
  `ashfordbriggs.com`**, update: `SITE_URL` in the backend env (feeds the dynamic
  `/sitemap.xml`), `frontend/public/robots.txt`'s `Sitemap:` line, and the
  hardcoded canonical/OG references in `frontend/index.html` and
  `frontend/src/components/Seo.tsx`.

## Monorepo layout
```
ashford-briggs/
├── backend/
│   ├── app/
│   │   ├── core/         config (asyncpg URL normalization), database, security (JWT+bcrypt),
│   │   │                 crypto (Fernet), ratelimit
│   │   ├── middleware/    auth.py — get_current_user + require_role RBAC guard
│   │   ├── models/        user, blog, demo_request, smtp_settings, sender_settings, contact,
│   │   │                  campaign, campaign_message, email_event, suppression, trust
│   │   │                  (+ __init__ imports ALL — cardinal)
│   │   ├── schemas/       pydantic contracts
│   │   ├── services/      anthropic_service (AI proxy), blog_service (slug/publish),
│   │   │                  email_service (SMTP); analytics: senders/ (mailgun, smtp),
│   │   │                  sender_service, campaign_service, contact_service,
│   │   │                  suppression_service, render_service, link_service, classifier,
│   │   │                  event_service, stats_service, dmarc_service, blocklist_service,
│   │   │                  seed_service, preflight_service, trust_service
│   │   ├── routers/       under /api: health, auth, blog_public, blog_admin, ai, demo,
│   │   │                  settings, sender_settings, contacts_admin, campaigns_admin,
│   │   │                  webhooks, analytics_admin, attribution, trust_admin;
│   │   │                  mounted at the root: sitemap, tracking (/t/*)
│   │   ├── worker.py      campaign sending + trust checks, one pass per run
│   │   └── main.py        app factory, CORS, router registration
│   ├── alembic/versions/  9 migrations: init, 3 for blog/SMTP settings, 5 for analytics
│   ├── tests/             279 unit tests (pytest)
│   ├── seed.py            creates first admin
│   ├── requirements.txt, requirements-dev.txt, .env.example
├── frontend/         React/Vite app
│   ├── src/
│   │   ├── pages/         Home, Product, HowItWorks, About, Contact, Blog*, admin/*,
│   │   │                  admin/analytics/* (Overview, Campaigns, CampaignEditor,
│   │   │                  CampaignDetail, Contacts, Trust)
│   │   ├── components/    Seo, MarkdownImage, RequireAuth, SenderSettings, …
│   │   ├── layouts/       PublicLayout, AdminLayout (role-aware sidebar)
│   │   ├── context/       AuthContext
│   │   ├── lib/api.ts     API client + aiApi (calls own backend proxy)
│   │   └── styles/tokens.css
│   ├── public/ab-beacon.js  landing-page script; running it is what marks a click as verified
│   ├── package.json, vite.config.ts, tsconfig*.json, index.html
├── deploy/ubuntu/    compose, Caddyfile, .env.example, paladin-worker.service + .timer
├── scripts/sync-docs.sh   copies docs/ to the partner docs repo
├── .github/workflows/     ci.yml, sync-docs.yml
└── docs/             OVERVIEW (partners' entry point), HANDOFF, ROADMAP, BUGS, TESTING,
                      CHANGELOG, AUDIT-LOG, EMAIL-ANALYTICS, EMAIL-SETUP-RUNBOOK,
                      DEPLOY-DEV-SERVER, DEPLOY-UBUNTU, DEPLOY-RAILWAY (history only)
    ├── original-snapshot/   FROZEN verbatim original copy (revert point)
    └── content/             expanded/sharpened marketing copy + SITEMAP.md
```

## Roles (RBAC)
Three roles, ranked author(1) < editor(2) < admin(3), enforced by
`require_role(minimum)`:
- **author** — create/edit/publish OWN posts; use AI generation
- **editor** — all posts + delete + demo-request inbox; in analytics: view
  campaigns, stats and the trust panel, draft campaigns, send tests, upload DMARC
  reports, run blocklist checks
- **admin** — everything + provision users (`POST /api/auth/users`); in analytics:
  send and delete campaigns, create/edit/import contacts, manage seed inboxes, and
  the SMTP and campaign sender settings

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

## Email analytics — things that will bite
- **Router order:** `tracking.router` must be registered *before* the SPA
  catch-all in `main.py`, or the React app swallows `/t/*`.
- **Migrations touching enums:** `drop_table` leaves Postgres enum types behind, so
  `downgrade()` needs an explicit `DROP TYPE IF EXISTS`. Round-trip down-then-up
  before committing any migration.
- **Two Mailgun credentials:** the API key sends; the HTTP webhook signing key
  verifies inbound events. The webhook fails closed without it.
- **Reply capture is not built (BUG-008).** Nothing creates `replied` events, and a
  *Reply domain* setting sends every reply to an address nothing reads. Keep it blank.
- **Send a test is untracked** — it uses a preview token. Rehearse with a real send
  to an internal tag.
- **Suppressions have no delete path, by design**, and there is no way to import
  past opt-outs yet (runbook F1).
- **Real campaigns go out from production only.** Sent links can't change and the
  unsubscribe must work for 30 days; dev rehearses on `devwww`.
- **DNS:** `*.ashfordbriggs.com` is a wildcard to the nginx web host, not the
  Paladin box, and a name that gains any record loses the wildcard's answer. Keep
  the sending domain (`updates.`) mail-only and serve tracking from `links.`.

## Local dev

**Manual install** (any OS — adjust the venv-activate line: `source .venv/bin/activate`
on Mac/Linux, `.venv\Scripts\activate` on Windows):
```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env          # fill JWT_SECRET_KEY, ENCRYPTION_KEY, ANTHROPIC_API_KEY
python -m seed                # create first admin (admin@ashfordbriggs.com / ChangeMe123!)
uvicorn app.main:app --reload # http://localhost:8000  (docs at /docs)
python -m pytest              # 279 unit tests
python -m app.worker          # one worker pass: sends due campaigns, runs trust checks

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173  (proxies /api -> :8000)
npm run lint
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
As of 2026-09-12 — the **email campaign analytics system** is built and documented:
- **Phases 1–5 built** on `feat/email-campaign-analytics` (**PR #1, open, not
  merged**) and deployed to the dev server with the worker timer: contacts and
  consent, suppression, campaigns and Mailgun sending, root-mounted tracking,
  honest engagement tiers with machine detection, A/B statistics, sender settings,
  and the domain-trust panel (DMARC ingestion, blocklists, seed inboxes, pre-flight).
- **279 backend unit tests**, 77 of them on the classifier. No HTTP-level, database
  or frontend tests yet — see `docs/TESTING.md`.
- **Docs reconciled and synced** to the partner repo. `docs/EMAIL-SETUP-RUNBOOK.md`
  was rebuilt as one ordered path (phases A–H) whose step codes match the
  developer's interactive runbook.
- **Found and logged:** BUG-008 (no reply capture; open) and BUG-009 (settings copy
  suggesting values that break campaigns; fixed 2026-09-12).
- **Owners' side:** `dmarc@ashfordbriggs.com` is live (2026-09-12) and both DMARC
  records report to it. 38 setup questions compiled for the owners, 5 answered so far.

Earlier (2026-07-07 and before): scaffold, security hardening (rate limiting, UUID
crash fixes, password rules), SEO/UX (per-page `<Seo>`, dynamic sitemap, 404,
token refresh), CI, and the blog editor completeness pass (Unpublish, captioned
images). Detail in `docs/CHANGELOG.md`.

## DEPLOYMENT — as of 2026-09-12
- **Where the site runs now:** only the dev/demo copy on the company server
  (see below). The Railway display deployment (puppyinfo.us) was **retired on
  2026-09-09**: its `Paladin` and `Postgres` services were deleted,
  puppyinfo.us no longer serves anything, and `railway.toml` was removed from
  the repo. History and the Railway-specific lessons are kept in
  `docs/DEPLOY-RAILWAY.md` in case Railway is ever used again.
- **The real domain comes later.** `ashfordbriggs.com` is still hardcoded in
  the frontend (canonical/OG in `Seo.tsx` and `index.html`, `robots.txt`,
  JSON-LD in `Home.tsx`/`About.tsx`, the copy-link in `admin/PostList.tsx`,
  Privacy/Terms text). That is deliberate — leave it. When the site moves to
  its final domain, only `SITE_URL` and `CORS_ORIGINS` in that deployment's
  environment need to change, unless the final domain is not `ashfordbriggs.com`.
- **Start path (any host):** the Dockerfile `CMD` runs `alembic upgrade head`,
  then `python -m seed` *only if* `SEED_ADMIN_PASSWORD` is set, then uvicorn
  with `--proxy-headers`. The dev server's systemd unit mirrors this sequence.
- **Partner-facing docs repo:** github.com/Vybecode-LTD/ashfordbriggs-docs is a
  synced copy of `docs/` + `deploy/ubuntu/` (folder `paladin-website/`). Never
  edit it there. After changing docs here, run `scripts/sync-docs.sh` (needs
  `../ashfordbriggs-docs` cloned) or let the `sync-docs` Action do it once the
  `DOCS_REPO_TOKEN` secret is set. `docs/OVERVIEW.md` is the partners' entry
  point; keep it current when environments or roles change.
- **Dev/demo server (live since 2026-09-09):** https://devwww.ashfordbriggs.com
  on the company's shared Ubuntu box `ab-webserver`, installed the manual way
  (venv + systemd `paladin.service` + existing Postgres 14 + Apache reverse
  proxy behind a front proxy that owns TLS), plus `paladin-worker.timer`. **That
  server also hosts PBX and other systems: touch only the Paladin footprint.** The
  Paladin vhost is bound to `10.0.0.80:80` (a request on any other address, such as
  Tailscale, reaches a different site), its `updates.` alias is provisional, and
  `.env` raises the rate limits because the front proxy forwards no client address.
  Everything about it, including the update procedure, is in
  `docs/DEPLOY-DEV-SERVER.md`.
- **Production (server being arranged by the owner):** expected to mirror the dev
  server's environment, so the dev layout is the likely install path, or
  `docs/DEPLOY-UBUNTU.md` if it has Docker (plus the worker, section 5.5). Runbook
  phase E covers it. CI's `deploy-image` job builds the image and boots it against
  Postgres (migrations, seeded admin login, health) on every push.
- **Rate limiting behind a proxy:** the Dockerfile starts uvicorn with
  `--proxy-headers --forwarded-allow-ips='*'` so slowapi keys on the real
  client IP. Without it every visitor shares one bucket. Safe only because
  port 8000 is never published directly.
- **Railway-specific gotchas** (start-command override, redeploy config
  snapshots, project-token limits) are recorded in `docs/DEPLOY-RAILWAY.md`.

## NEXT STEPS (for Claude Code)
1. **Merge PR #1** once reviewed — production installs from `main`.
2. **Work the setup runbook** (`docs/EMAIL-SETUP-RUNBOOK.md`). The owners' answers
   drive phase B; the tracking-host routing decision (B1) is the only open
   architectural question.
3. **Before the first real campaign:** build the past opt-out import (F1 — no
   endpoint exists), rehearse on dev (phase D), and deploy production with the
   worker (phase E).
4. **Reply capture** (G5, BUG-008): an endpoint for replies forwarded by a Mailgun
   route, matched by the token in the reply address. Until then Reply domain stays
   blank.
5. **Tests:** frontend (Vitest + RTL, currently zero), and backend HTTP-level and
   database tests — the 279 are unit tests.
6. **Move to the real domain (later, per the owner).** When the final domain is
   ready, set `SITE_URL` and `CORS_ORIGINS` for that deployment. The frontend's
   hardcoded canonical/OG/JSON-LD references already say `ashfordbriggs.com`, so
   they need editing only if the final domain is something else. Delete the dead
   static `frontend/public/sitemap.xml` at that point — the backend generates the
   real one and wins the route.
