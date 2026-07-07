# Testing — Ashford & Briggs / Paladin

## Current state: no automated test suite

There is **no automated test suite** for either the backend or the frontend as
of this writing. This is an honest, known gap — not a claim of coverage. Every
verification described below was done manually against a running dev server,
not via a repeatable test harness.

Frameworks per `CLAUDE.md` conventions (Python/FastAPI and React/TypeScript)
are not yet installed or configured in this repo.

## What has actually been verified (manual/live, 2026-07-07)

As part of today's security-hardening pass, the following was checked by hand
against the local dev server (`uvicorn app.main:app --reload`), using curl:

- **Rate limiting works and returns 429.** Hammered `POST /api/demo-requests`
  seven times in under an hour from the same client; the 6th request onward
  returned `429 Too Many Requests` (limit: 5/hour). Same pattern confirmed for
  login at 10/min.
- **Malformed UUIDs return clean errors, not 500s.** Crafted requests with
  non-UUID identifiers against the three previously-crashing call sites
  (`get_current_user` via a bad JWT `sub`, `POST /api/auth/refresh` with a bad
  refresh-token subject, and `/api/admin/blog/{post_id}` GET/DELETE with a
  non-UUID path segment) each returned the intended 401 or 404 instead of an
  unhandled 500/stack trace.
- **Short passwords are rejected.** Submitted a password under 8 characters to
  the registration/password-change path; got a clean `422` validation error
  instead of being silently accepted.

These checks confirm the specific fixes in `docs/BUGS.md` (BUG-001 through
BUG-003) and the security batch in `docs/CHANGELOG.md`. They are not
repeatable/regression-safe — nothing prevents these same bugs from being
reintroduced by a future change, because there's no test asserting the
behavior. That's the primary argument for phase 4 below.

## Planned automated suite (not started)

### Backend — pytest + httpx
- Async test client against the FastAPI app (httpx `AsyncClient` +
  `ASGITransport`), isolated test database (or transactional rollback per test).
- Priority areas, roughly in order:
  1. Auth: login, refresh, malformed-token/UUID paths (direct regression tests
     for BUG-001/002/003), password length validation, password-change endpoint.
  2. RBAC guard (`require_role`): author/editor/admin boundary checks on every
     protected route.
  3. Blog workflow: draft creation, publish transition (`published_at`
     stamping), slug uniqueness/de-duplication, ownership checks on edit/delete.
  4. Rate limiting: confirm 429 behavior on login and demo-request endpoints
     (can toggle `rate_limit_enabled=False` in config for tests that don't care
     about limits, per slowapi's `enabled` flag pattern).
  5. AI proxy error handling: mock the Anthropic call to raise, confirm clean
     502 (`AIServiceError` path) rather than 500.
  6. Demo request submission: validation, persistence, inbox listing.
- Estimated: roughly 30-40 test cases for the backend alone.

### Frontend — Vitest + React Testing Library
- Component/page-level tests, priority order:
  1. `AuthContext` — login, logout, token storage, and (once built) the
     refresh-on-401 flow.
  2. Admin `PostEditor` — draft/publish state transitions, AI-assist calls
     mocked at the API-client boundary.
  3. Public pages — smoke render tests for Home/Product/HowItWorks/About/Contact
     (catches content-parity regressions like BUG-006).
  4. Contact form — submission, validation, error states.
- Consider Playwright for one true end-to-end path (admin login -> create post
  -> publish -> confirm visible on `/blog`) once the component-level suite
  exists; not started, not committed to yet.
- Estimated: roughly 15-25 test cases for the frontend, plus the optional E2E flow.

### Target coverage

No coverage threshold is enforced today because no suite exists to measure
against. Once the initial suite lands, treat coverage numbers as informational
until they stabilize — don't gate merges on a threshold before there's a
baseline. `CLAUDE.md`'s general quality-gate numbers (85% PR / 95% deploy) are
aspirational for this project, not yet wired into CI (CI itself is also part of
the in-progress UX/SEO/polish phase — see `docs/ROADMAP.md`).

## How to run tests today

There is nothing to run yet. `python -m pytest` and `npm run test` will both
fail (no test files, no test runner configured) until phase 4 of the roadmap
is executed.
