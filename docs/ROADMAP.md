# Roadmap — Ashford & Briggs / Paladin

How this project is progressing from scaffold to production. Updated as phases complete.

## Phases

### 1. Scaffold — COMPLETE
Backend (FastAPI + async SQLAlchemy + Alembic) and frontend (React + Vite + TS)
fully scaffolded. Five marketing pages, blog reader, full admin (login, dashboard,
post list, demo inbox, AI-assisted post editor). Original copy frozen in
`docs/original-snapshot/`, expanded copy drafted in `docs/content/`.

### 2. Security hardening — COMPLETE (2026-07-07)
- Rate limiting on login (10/min) and demo-request submission (5/hour) via slowapi.
- Fixed three unguarded `uuid.UUID()` calls that raised unhandled 500s on malformed
  IDs — now clean 404/401.
- Password length validation (8-128 chars).
- Self-service password-change endpoint + admin user-management endpoint.
- Error handling around the Anthropic proxy call (clean 502 instead of 500).
- `max_length` caps on AI request schemas.
- `.env.example` now defaults `DEBUG=false`.

See `docs/BUGS.md` for the specific defects closed and `docs/CHANGELOG.md` for the
full entry. Not yet committed to git — working tree has uncommitted changes to the
affected backend files.

### 3. UX / SEO / accessibility polish — IN PROGRESS
Running in parallel with the security pass. Scope:
- Per-page SEO meta tags, `robots.txt`, `sitemap.xml`, JSON-LD structured data.
- 404 catch-all route on the frontend.
- Admin sidebar/grid responsive CSS fixes.
- Click-to-copy in the admin post list.
- Real access-token-refresh flow on the frontend (access tokens are 60 min and
  currently never refreshed on expiry/401 — user gets silently logged out).
- Content-parity fixes for Contact and How It Works pages against `docs/content/`.
- GitHub Actions CI pipeline.

Status of each item is not yet confirmed complete as of this writing — verify
against the actual diff before marking done.

### 4. Automated test suite — NOT STARTED
No automated tests exist for backend or frontend today. Planned:
- Backend: pytest + httpx (async client), targeting auth, RBAC guards, blog
  publish workflow, rate limiting, AI proxy error paths.
- Frontend: Vitest + React Testing Library for components/pages; consider
  Playwright for admin login → publish flow E2E.
- Estimated scope: 45-65 test cases across both.
- Target coverage: see `docs/TESTING.md` for current state — no threshold is
  enforced yet since no suite exists.

### 5. Deploy — NOT STARTED
Railway target. Dockerfile + `railway.toml` present (single-service pattern:
FastAPI serves the built frontend as static files from `backend/app/main.py`).
Not yet deployed to production. Blocked on: finishing UX/SEO polish, standing up
at minimum a smoke-test-level automated suite, and generating the first real
Alembic migration (`alembic revision --autogenerate -m "init"`).

## Backlog (prioritized)

1. **Finish UX/SEO/accessibility pass** (phase 3, in progress) — frontend token
   refresh is the highest-risk item in this batch (silent logout is a real UX bug).
2. **Generate first Alembic migration** — dev mode auto-creates tables via
   lifespan; production must not rely on that.
3. **Stand up backend test suite** (pytest + httpx) — prioritize auth/RBAC and
   rate-limit paths since those are security-critical.
4. **Stand up frontend test suite** (Vitest + RTL) — prioritize AuthContext,
   token refresh, and the admin PostEditor.
5. **GitHub Actions CI** — lint + test gate on PRs (tracked under phase 3 but
   also unblocks safe iteration once the test suite exists).
6. **Wire real images / OG assets** — paths are referenced in `index.html` and
   blog covers but real assets aren't in place yet.
7. **Commit the security-hardening changes** — currently uncommitted working
   tree changes; commit before starting phase 3 work lands on top of them.
8. **Railway deploy** — after the above, following `railway-deploy-playbook`.

## Non-goals (for now)

- No heavyweight doc-management framework — this file and its siblings are
  plain Markdown, hand-maintained.
- No multi-tenant support, no i18n — single marketing site, single company.
