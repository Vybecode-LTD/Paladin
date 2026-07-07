# Handoff — Ashford & Briggs / Paladin

Written for whoever (human or Claude session) picks this project up next, cold.
Read this before touching code.

## What this project is

Marketing site + blog + AI-assisted admin backend for Ashford & Briggs
(Jacksonville, FL), makers of Paladin — real-time AI intelligence for recruiter
phone calls. See `CLAUDE.md` at the repo root for the full stack/layout
reference; this file is about *state*, not architecture.

## What's done

1. **Full scaffold** (backend + frontend + docs structure) — complete, see
   `docs/CHANGELOG.md` 2026-07-06 entry.
2. **Security hardening pass** — complete as of 2026-07-07, verified live:
   - Rate limiting (slowapi): login 10/min, demo-request submission 5/hour.
   - Three unguarded `uuid.UUID()` crash sites fixed (auth middleware, refresh
     endpoint, blog_admin lookup/delete) — now clean 401/404 instead of 500.
   - Password length validation, self-service password-change endpoint, admin
     user-management endpoint.
   - Anthropic proxy call now has error handling (`AIServiceError` -> clean 502).
   - `max_length` caps on AI request schemas.
   - `.env.example` defaults `DEBUG=false`.
   - Full detail: `docs/BUGS.md` (closed bugs), `docs/CHANGELOG.md`, `docs/AUDIT-LOG.md`.

## What's active right now

A **UX/SEO/accessibility polish pass** is in progress (running as a separate,
parallel effort — its results were not visible to the session that wrote this
handoff, so treat it as in-progress, not confirmed complete). Scope:
- Per-page SEO meta tags, `robots.txt`, `sitemap.xml`, JSON-LD structured data.
- Frontend 404 catch-all route.
- Admin sidebar/grid responsive CSS.
- Click-to-copy in the admin post list.
- Frontend access-token-refresh flow (real gap today: 60-min access tokens are
  never refreshed on expiry/401 — see BUG-004 in `docs/BUGS.md`).
- Contact and How It Works content-parity fixes against `docs/content/`.
- GitHub Actions CI pipeline.

**Before continuing any of the above:** check the actual working tree diff and
`git log` (once committed) to see what that parallel pass actually landed,
rather than trusting this description as current fact — it was accurate at
write time only.

## What's next (in order)

1. **Commit the security-hardening changes.** As of this writing they are
   uncommitted in the working tree (backend files: `core/ratelimit.py`,
   `middleware/auth.py`, `routers/auth.py`, `routers/blog_admin.py`,
   `routers/ai.py`, `schemas/auth.py`, `schemas/ai.py`,
   `services/anthropic_service.py`, `.env.example`). Review the diff for
   secrets before staging (standard `VERSION_CONTROL.md` discipline from the
   parent `CLAUDE.md`), then commit.
2. **Reconcile with the parallel UX/SEO pass** once it's done — merge/rebase
   carefully since both passes may touch overlapping frontend auth code
   (token refresh) and backend routers.
3. **Generate the first real Alembic migration:**
   `alembic revision --autogenerate -m "init"` then `alembic upgrade head`.
   Dev mode currently auto-creates tables via the FastAPI lifespan hook when
   `DEBUG=true`; production must not depend on that.
4. **Stand up the automated test suite** (pytest+httpx backend, Vitest+RTL
   frontend) — see `docs/TESTING.md` for the planned scope (45-65 cases). This
   is the biggest structural gap in the project right now: zero automated
   coverage.
5. **Wire real images/OG assets** — paths are referenced in `index.html` and
   blog cover slots but real files aren't in place.
6. **Deploy to Railway** — Dockerfile + `railway.toml` are ready
   (single-service: FastAPI serves the built frontend as static). Not yet
   deployed. Use the `railway-deploy-playbook` skill when ready; set
   `JWT_SECRET_KEY`, `ANTHROPIC_API_KEY`, `CORS_ORIGINS` as env vars
   (`DATABASE_URL` is auto-provided by Railway Postgres).

## Blockers / risks to know about

- **No automated tests.** Every verification claim in `docs/BUGS.md` and
  `docs/CHANGELOG.md` for the 2026-07-07 pass is manual/curl-based against a
  local dev server, not a regression-safe test. Regressions on the three fixed
  UUID-crash bugs would go undetected until someone hits them again by hand.
- **Uncommitted security fixes.** If another session or person starts editing
  the same backend files without pulling in the current working tree state,
  work could be lost or conflict. Confirm git status before editing
  `middleware/auth.py`, `routers/auth.py`, `routers/blog_admin.py`,
  `routers/ai.py`, `services/anthropic_service.py`, or the `schemas/` files.
- **Frontend session bug (BUG-004).** Users past the 60-minute access-token
  window get silently broken sessions today — this is being worked in the
  parallel pass but isn't confirmed fixed yet. Don't assume it's resolved
  without checking.
- **Not deployed anywhere yet.** All of the above is local-dev-only. No
  production environment exists to worry about breaking.

## Where to look for detail

- `docs/ROADMAP.md` — phases and prioritized backlog.
- `docs/BUGS.md` — closed and open defects with root cause/fix/verification.
- `docs/TESTING.md` — current (zero) automated coverage state and the plan.
- `docs/CHANGELOG.md` — dated entries, most recent first... actually oldest
  first at the bottom, newest at top (standard changelog convention).
- `docs/AUDIT-LOG.md` — the 6-dimension audit that produced ~52 findings and
  today's remediation pass against the security-critical subset.
- `docs/content/` — approved marketing copy (source of truth for content-parity
  work). `docs/original-snapshot/` — frozen original single-page copy, revert
  point only, do not treat as current.
