# Changelog — Ashford & Briggs / Paladin

All notable changes to this project, in date order. Not committed to git yet as
formal tags/releases — this log tracks work sessions, not package versions.

## 2026-07-07 (latest) — Blog editor completeness pass + deploy handoff docs

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
