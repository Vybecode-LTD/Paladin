# Changelog — Ashford & Briggs / Paladin

All notable changes to this project, in date order. Not committed to git yet as
formal tags/releases — this log tracks work sessions, not package versions.

## 2026-09-09 (latest) — Dev server deployment + Ubuntu runbook + proxy-aware rate limits

**Retired (owner request):** the Railway display deployment. The `Paladin`
and `Postgres` services were deleted from the Railway project, puppyinfo.us
no longer serves anything, and the unused `railway.toml` was removed from the
repo. `docs/DEPLOY-RAILWAY.md` stays as history. The dev server
(devwww.ashfordbriggs.com) is now the only live copy of the site.

**Changed (owner decision, after BUG-007):** the demo-reply **sender address
is now configurable** in the admin Settings screen (`from_email`, migration
`d4a1c9e7b2f8`). It defaults to `info@ashfordbriggs.com` when blank, so
existing deployments behave as before. Reason: mail providers reject a From
address the authenticated account does not own, and the dev server's SMTP
account is not an ashfordbriggs.com mailbox. Regression tests cover the
fallback.

**Fixed (BUG-007, later that day):** the admin SMTP test on the dev server
ended in a 504 for a port-465 mail host. The Settings "Use TLS" switch only
ever meant STARTTLS, so port 465 got a plaintext connection that waited 30 s.
`smtp_tls_options()` now selects implicit TLS for 465 and STARTTLS otherwise,
the send timeout is 15 s so the real error beats the proxy timeout, and the
checkbox says what it does. Six regression tests. Live after deploy: the mail
host answers in ~1 s and rejects the fixed sender `info@ashfordbriggs.com`
because the configured account does not own it. Sending needs either an SMTP
account that owns that address or a decision to make the sender configurable.

**Documentation repo** for the partners: github.com/Vybecode-LTD/ashfordbriggs-docs
now carries a synced copy of `docs/` plus the `deploy/ubuntu` files under
`paladin-website/`. Source of truth stays here; `scripts/sync-docs.sh` (and the
`sync-docs` GitHub Action, once a `DOCS_REPO_TOKEN` secret exists) replaces
that folder wholesale. Added two partner-facing documents to `docs/`:
`OVERVIEW.md` (what the site is, environments, roles, stack, layout) and
`DEPLOY-RAILWAY.md` (the display deployment and its gotchas).

**Dev server follow-ups (2026-09-09, later):** the vhost is now `:80` only
(the expired-cert `:443` block was dropped), it logs every forwarded-address
header, and that log proved the front proxy sends none, so the app's per-IP
rate limits act as global caps there. Raised them in the dev `.env`
(60/min login, 60/hour demo, 200/hour AI) with the revert documented in
`DEPLOY-DEV-SERVER.md`.

**Deployed** the site to the company's shared dev server as
https://devwww.ashfordbriggs.com (details and update procedure in
`docs/DEPLOY-DEV-SERVER.md`). Manual path: Python 3.10 venv, systemd unit
running as a dedicated `paladin` user, own role/database on the existing
Postgres 14, Apache vhost reverse-proxying to 127.0.0.1:8000 behind a front
proxy that terminates TLS. Verified live: health, blog API, sitemap with the
devwww origin, all frontend routes, admin login, `X-Robots-Tag: noindex`.
Lesson recorded there: certbot cannot run on that box for devwww because the
front proxy answers the challenge; no certificate is needed locally.

Prepared the move from the Railway display deployment to a self-managed
Ubuntu server (pending partner approval).

**Added**
- `docs/DEPLOY-UBUNTU.md`: step-by-step runbook (server prep, Docker, code
  transfer, `.env`, launch, first login, backups/restore, updates, carrying
  content over from Railway, troubleshooting, a no-Docker appendix).
- `deploy/ubuntu/docker-compose.yml` (app + Postgres 17 + Caddy),
  `deploy/ubuntu/Caddyfile` (automatic HTTPS), `deploy/ubuntu/.env.example`
  (every variable with its generation command).
- CI job `deploy-image`: validates the compose file, builds the production
  image, boots it against Postgres and checks migrations ran, the seeded
  admin can log in, `/api/blog/posts` and `/` respond. This is the first
  automated end-to-end check of the deploy path.

**Fixed**
- CI `Backend` job had failed on every push since July: the `Run tests` step
  fires because `backend/tests/` exists, but pytest was never installed.
  Added `backend/requirements-dev.txt` (pytest) and install it in CI. The
  7 existing SVG-sanitizer tests pass.
- `Dockerfile`: uvicorn now runs with `--proxy-headers
  --forwarded-allow-ips='*'`. slowapi keys rate limits on
  `request.client.host`; behind Railway's edge (and behind Caddy on the VPS)
  that was the proxy's address, so the login (10/min) and demo-request
  (5/hour) limits were shared by every visitor. Applies to the Railway
  deployment as well.

## 2026-09-08 — First production deploy (Railway)

Redeployed the whole site into a fresh Railway project ("Ashford & Briggs")
and got it live on the generated Railway URL (since replaced — see the
2026-09-09 notes below).

**Changed**
- `railway.toml`: removed `startCommand` and `preDeployCommand`. The
  `startCommand` overrode the Dockerfile CMD, so `alembic upgrade head` never
  ran on Railway and every DB-backed route returned 500 with
  `relation "blog_posts" does not exist`; `preDeployCommand` was ignored by
  Railway entirely (service manifest showed `null`). The Dockerfile CMD is
  now the single start path on any Docker host.
- `Dockerfile`: CMD now runs migrations, then `python -m seed` only when
  `SEED_ADMIN_PASSWORD` is set (idempotent — skips an existing user), then
  uvicorn. Needed because Railway project tokens cannot `railway ssh` to run
  the seed as a one-off.

**Infra (Railway, not in git)**
- Postgres plugin added; `DATABASE_URL` referenced as
  `${{Postgres.DATABASE_URL}}`.
- Fresh production `JWT_SECRET_KEY` and `ENCRYPTION_KEY`; `ANTHROPIC_API_KEY`,
  `ANTHROPIC_MODEL`, `CORS_ORIGINS`, `SITE_URL`, `DEBUG=false` set on the
  `Paladin` service. A stale service-level `startCommand` was cleared via
  the API so the Dockerfile CMD applies.
- All three Alembic migrations applied; first admin created; seed variables
  removed afterwards.
- Verified live: `/`, `/blog`, `/api/blog/posts` (200 `[]`), `/sitemap.xml`
  (200, correct origin), admin login and authenticated admin routes (200).
- 2026-09-09: deleted the stray `frontend` and `backend` services (wrong
  build setup for this monorepo, failed on every push). Note: the GraphQL
  `serviceDelete` mutation is *not* authorized for a project token, but
  `railway service delete --service <name> --yes` (CLI ≥ 5.4x) is.
- 2026-09-09: owner attached **puppyinfo.us** as a temporary display domain
  and set `SITE_URL` / `CORS_ORIGINS` to it (the generated Railway domain was
  regenerated to `paladin-production-c90f`). Verified: sitemap emits
  puppyinfo.us URLs, CORS preflight allows the origin, all routes 200. The
  ashfordbriggs.com references in the frontend are intentionally untouched —
  that is the eventual production domain.

## 2026-07-07 — Blog editor completeness pass + deploy handoff docs

Verified the admin blog editor against a checklist (AI assistant, editing
published posts, image handling, formatting, unpublish/delete) rather than
assuming it was all there. Found and fixed two real gaps.

**Added**
- **Unpublish button** in `PostEditor.tsx` (`frontend/src/pages/admin/PostEditor.tsx`) —
  shown only for already-published posts, confirms before acting, PATCHes
  `status` back to `draft`. The backend already supported this transition;
  there was simply no UI control for it before now.
- **Insert image button** with caption support — a new "Insert image" button
  in the editor prompts for a URL and an optional caption, inserting
  `![alt](url "caption")` at the cursor. A new shared `MarkdownImage`
  component (`frontend/src/components/MarkdownImage.tsx`) renders that
  Markdown "title" as a real `<figure>/<figcaption>` instead of a native
  tooltip — wired into both the editor's Preview tab and the public
  `BlogPost.tsx` page, so captions render identically in both places.
- Relabeled the existing draft-save button to "Save changes" when editing an
  already-published post (it was ambiguously always labeled "Save draft"
  even when it wouldn't actually change status).
- A prominent handoff section at the top of `CLAUDE.md` instructing the next
  Claude session to stop and ask the new maintainer about their actual
  deployment environment (host, domain, DB, Docker availability, secrets)
  before doing any deploy work — this repo is being handed off for
  self-hosting on someone else's server.

**Verified**
- Confirmed the AI assistant (draft/titles/excerpt/SEO), editing an
  already-published post, and delete all already worked correctly.
- Live-tested the new Unpublish button against the real published post:
  backend status flips to `draft`, `published_at` is preserved, the button
  set correctly changes from Save/Unpublish/Update back to Save/Publish.
  Live-tested Insert image: prompts fire, Markdown is inserted at the cursor,
  Preview renders a real `<figure>/<figcaption>`. Restored the test post to
  its original published state and content afterward.
- `npx tsc --noEmit`, `npm run build`, and `npm run lint` all clean.

---

## 2026-07-07 (later) — UX/SEO sweep confirmed + follow-up fixes

The UX/SEO/accessibility pass referenced as "in progress" in the entry below
completed and was committed (`913d0f1`), alongside the security-hardening
commit (`575a9ec`). Four follow-up items from that pass's own review notes:

**Added**
- `GET /sitemap.xml` (`backend/app/routers/sitemap.py`) — generated at request
  time from the DB, so every published blog post is included, not just the
  static marketing routes. Registered at the site root (no `/api` prefix),
  ahead of the SPA catch-all so it wins over the static copy Vite copies from
  `frontend/public/sitemap.xml` in a production build. New `SITE_URL` setting
  (`backend/app/core/config.py`, `.env.example`) drives the absolute URLs —
  change it when deploying under a different domain.
- `max_length` caps on `DemoRequestCreate` (`backend/app/schemas/demo.py`),
  mirrored exactly from the `DemoRequest` DB column limits, so an oversized
  field is a clean 422 instead of a raw `StringDataRightTruncationError` 500
  (confirmed this was a real gap: a 250-char `full_name` previously reached
  the DB and crashed before hitting any length check).

**Fixed**
- `npm audit` in `frontend/`: bumped `vite` 5.4.21 → 6.4.3, resolving the
  moderate/high `esbuild` dev-server advisory. Deliberately did *not* take
  `npm audit fix --force`'s suggested jump straight to `vite@8` — v6 already
  pulls in the patched `esbuild` (`^0.25.0`) with much less breaking-change
  risk. Build, lint, and the dev server proxy all reverified clean afterward.
- Root `CLAUDE.md` was stale — still described the original scaffold as the
  current state and listed the Alembic migration and OG images as pending
  (both were already done). Refreshed to reflect actual current state and
  generalized the deploy section: this project is being handed off to be
  self-hosted on someone else's own server, so the Dockerfile/deploy notes
  are no longer framed as Railway-only.

**Verified**
- `/sitemap.xml` live-checked: includes the one published post with a
  `<lastmod>` tag, static marketing routes still present.
- Oversized-field demo-request live-checked: 422 with a clean Pydantic
  `string_too_long` error, not a 500.
- `npm audit`: 0 vulnerabilities. `npm run build`, `npm run lint`, and a fresh
  `vite` dev server all confirmed working post-bump.

---

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
