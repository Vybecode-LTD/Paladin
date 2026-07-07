# Audit Log — Ashford & Briggs / Paladin

Dated record of project-wide audits and the remediation work they triggered.
This is a log of *events*, not a live task tracker — see `docs/ROADMAP.md` for
current priorities and `docs/BUGS.md` for the live defect list.

---

## 2026-07-07 — 6-dimension project audit + security remediation pass

### Audit

A project-wide audit was run across six dimensions: security, correctness,
UX/accessibility, SEO, testing, and documentation. It surfaced roughly **52
findings** in total, spanning everything from missing SEO meta tags to unguarded
crash paths in backend request handling.

No claim is made here that all 52 findings are individually enumerated in this
log — this entry records the audit as an event and tracks where its findings
ended up:
- **Security-critical findings** (the subset most likely to be exploited or to
  cause outright crashes) were triaged as the first remediation batch and are
  the subject of the "Remediation" section below.
- **UX/accessibility/SEO findings** were bundled into a second, parallel
  in-progress pass — see `docs/ROADMAP.md` phase 3 for scope (SEO meta
  tags/robots.txt/sitemap/JSON-LD, 404 route, admin responsive CSS, click-to-
  copy, frontend token refresh, content-parity fixes, CI pipeline).
- **Testing findings** reduce to one overarching gap: no automated suite exists
  at all. Tracked in `docs/TESTING.md` and roadmap phase 4.
- **Documentation findings** are addressed by the creation of this documentation
  set itself (`docs/ROADMAP.md`, `docs/BUGS.md`, `docs/TESTING.md`,
  `docs/CHANGELOG.md`, `docs/HANDOFF.md`, and this file), written the same day.

### Remediation (security-critical subset)

Completed same day, verified live against the running local dev server:

| Finding | Fix | File(s) |
|---|---|---|
| No rate limiting on login | slowapi limiter, 10/min | `backend/app/core/ratelimit.py`, `backend/app/main.py` |
| No rate limiting on demo-request submission | slowapi limiter, 5/hour | same as above |
| Unhandled 500 on malformed UUID in auth dependency | try/except -> 401 | `backend/app/middleware/auth.py` |
| Unhandled 500 on malformed UUID in refresh endpoint | try/except -> 401 | `backend/app/routers/auth.py` |
| Unhandled 500 on malformed UUID in blog-admin lookup/delete | try/except -> 404 | `backend/app/routers/blog_admin.py` |
| No password length validation | 8-128 char bounds | `backend/app/schemas/auth.py` |
| No self-service password change | new `PATCH /api/auth/me/password` endpoint | `backend/app/routers/auth.py` |
| No admin user-management path | new `PATCH /api/auth/users/{user_id}` endpoint | `backend/app/routers/auth.py` |
| Anthropic proxy call had no error handling (unhandled 500 on upstream failure) | `AIServiceError` raised and caught as clean 502 | `backend/app/services/anthropic_service.py`, `backend/app/routers/ai.py` |
| AI request schemas had no size bound (unbounded prompt payloads) | `max_length` caps added | `backend/app/schemas/ai.py` |
| `.env.example` defaulted `DEBUG=true` | flipped to `false` | `backend/.env.example` |

**Verification method:** manual curl-based checks against the running dev
server (not an automated test — no suite exists yet, see `docs/TESTING.md`):
- Rate limiter: 6th demo-request within an hour from the same client returned
  429.
- Malformed UUIDs: crafted invalid-UUID inputs against all three fixed call
  sites returned 404/401, not 500.
- Password validation: sub-8-character password rejected with 422.

Full defect-level detail (root cause, fix, verification) is in `docs/BUGS.md`
under BUG-001 through BUG-003. Full change detail is in `docs/CHANGELOG.md`
under the 2026-07-07 entry.

**State at time of this log entry:** none of the above remediation is committed
to git yet — working tree has uncommitted changes to the listed backend files.
Commit before starting further work on top of it (see `docs/HANDOFF.md`
"what's next").

### Not yet remediated / in progress

The UX/SEO/accessibility/CI portion of the audit's findings is being worked in
a separate, parallel session and was not verified complete at the time this
entry was written. Do not mark it done in this log until confirmed — check
`docs/ROADMAP.md` phase 3 and the actual working tree/git history for current
status.

The testing-dimension findings (no automated suite) remain fully open; no
remediation has started as of this entry. See `docs/TESTING.md` and roadmap
phase 4.

---

## Prior audits

None recorded. This is the first formal audit pass on this project since the
initial scaffold (`docs/CHANGELOG.md`, 2026-07-06 entry).
