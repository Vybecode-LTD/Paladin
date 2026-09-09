# Bugs — Ashford & Briggs / Paladin

Defect log. Distinguish from `docs/ROADMAP.md`: this file is for concrete broken
behavior (crashes, wrong output, security holes), not for missing
features/polish/tests — those live on the roadmap backlog.

---

## CLOSED

### BUG-001 — Malformed user ID crashes `get_current_user` with unhandled 500
- **Location:** `backend/app/middleware/auth.py`
- **Root cause:** the JWT `sub` claim was passed straight into `uuid.UUID(sub)`
  with no exception handling. Any malformed or tampered token payload (not a
  valid UUID string) raised `ValueError` inside dependency resolution, which
  FastAPI surfaced as a raw unhandled 500 instead of an auth failure.
- **Fix:** wrapped the `uuid.UUID()` call in try/except; invalid UUIDs now fall
  through the normal "invalid credentials" path and return 401.
- **Verified:** live against the running dev server — a request with a crafted
  bearer token containing a non-UUID `sub` claim returned 401, not 500.

### BUG-002 — Malformed refresh-token subject crashes `/api/auth/refresh` with unhandled 500
- **Location:** `backend/app/routers/auth.py` (`refresh` endpoint)
- **Root cause:** same pattern as BUG-001 — the refresh endpoint decoded the
  refresh token and passed its subject directly into `uuid.UUID()` without
  guarding against a malformed value.
- **Fix:** wrapped in try/except; malformed subject now returns 401 instead of
  crashing.
- **Verified:** live — `curl -X POST /api/auth/refresh` with a doctored/invalid
  refresh token returned 401, not 500.

### BUG-003 — Malformed post ID crashes blog-admin post lookup/delete with unhandled 500
- **Location:** `backend/app/routers/blog_admin.py` (`_load_owned` helper, used
  by the edit/update path, and `admin_delete`)
- **Root cause:** the `post_id` path parameter was passed directly into
  `uuid.UUID()` before querying the database. A non-UUID path segment (e.g.
  `/api/admin/blog/not-a-uuid`) raised `ValueError` before the ownership/RBAC
  check ever ran, surfacing as a 500.
- **Fix:** wrapped both call sites in try/except; malformed IDs now return 404
  (post not found) rather than crashing, consistent with how a valid-but-absent
  UUID is already handled.
- **Verified:** live — `curl` against `/api/admin/blog/not-a-uuid` (both GET and
  DELETE, as an authenticated author) returned 404, not 500.

**How all three were verified (method):** manual curl-based checks against the
running local dev server (`uvicorn app.main:app --reload`) after the fix, each
confirming the endpoint now returns the intended clean status code (401/404)
instead of an unhandled 500/stack trace. This was manual/live verification, not
an automated regression test — see `docs/TESTING.md` for the gap and the plan to
backfill these three as actual pytest cases (malformed-UUID input is an easy,
high-value first regression test once the suite exists).

---

### BUG-007 — SMTP test on port 465 hangs, surfaces as "Gateway Time-out"
- **Location:** `backend/app/services/email_service.py`; label in
  `frontend/src/pages/admin/Settings.tsx`
- **Root cause:** the Settings screen's single "Use TLS" switch was passed to
  aiosmtplib as `start_tls` (STARTTLS) and nothing ever selected implicit TLS
  (`use_tls`). Port 465 speaks TLS before any SMTP greeting, so a 465
  configuration opened a plaintext connection and waited the full 30 s for a
  greeting. On the dev server the front proxy timed out first (504); the app's
  own 502 with the real message arrived after the browser had given up.
- **Fix:** `smtp_tls_options(port, use_tls)` maps port 465 to implicit TLS
  (never STARTTLS) and every other port to STARTTLS when the switch is on;
  the two modes are never both set. Send timeout is now 15 s so a real error
  beats a proxy timeout. The checkbox label states the behaviour.
- **Verified:** `backend/tests/test_email_service.py` (6 tests; collection
  error before the fix, all pass after). Live on the dev server after deploy:
  the SMTP test to mail.spacemail.com:465 completes in ~1 s and returns the
  server's real answer, `553 5.7.1 Sender address rejected: not owned by user`,
  because the configured account does not own the fixed sender
  `info@ashfordbriggs.com`. That is a mail-account configuration decision, not
  an application fault (see CHANGELOG 2026-09-09).

## OPEN

### BUG-004 — Access tokens never refresh on the frontend
- **Location:** frontend `AuthContext` / API client (`frontend/src/lib/api.ts`)
- **Symptom:** access tokens are issued with a 60-minute lifetime and stored on
  login, but nothing refreshes them on expiry or on a 401 response. A user mid-
  session past the hour mark gets silently logged out / requests start failing.
- **Status:** being addressed as part of the in-progress UX/SEO polish pass (see
  `docs/ROADMAP.md` phase 3). Tracked here because it's a functional defect
  (broken session continuity), not just missing polish.

### BUG-005 — No 404 route on the frontend
- **Location:** frontend router (`React Router` config)
- **Symptom:** unmatched paths have no defined catch-all; behavior falls through
  to whatever the router's default is rather than a real 404 page.
- **Status:** in progress, same UX/SEO pass.

### BUG-006 — Contact and How It Works pages drift from source copy
- **Location:** `frontend/src/pages/Contact.tsx`, `frontend/src/pages/HowItWorks.tsx`
  vs. `docs/content/contact.md`, `docs/content/how-it-works.md`
- **Symptom:** rendered page copy doesn't match the approved copy documents —
  content-parity gap, not a crash, but user-facing incorrect content.
- **Status:** in progress, same UX/SEO pass.

---

## Judgment calls

- The three UUID crashes are logged as closed bugs (they were genuine defects
  with clear root cause, fix, and verification) rather than as changelog-only
  items, because they represent real broken behavior a user/attacker could hit.
- Items still in the parallel UX/SEO pass (missing SEO tags, admin responsive
  CSS, click-to-copy, CI pipeline) are treated as roadmap/backlog work, not
  bugs — they're absent features, not broken ones. The two exceptions are
  BUG-004 (session silently breaks — a functional regression from the user's
  point of view) and BUG-006 (shipped content is factually wrong relative to
  the source of truth), which are logged here as open bugs even though their
  fix is bundled into the same in-progress pass.
- No severity/priority scheme is imposed beyond OPEN/CLOSED — this project
  doesn't run a formal triage process, so keep it to what's broken and what
  isn't.
