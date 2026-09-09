# Audit Log — Ashford & Briggs / Paladin

Dated record of project-wide audits and the remediation work they triggered.
This is a log of *events*, not a live task tracker — see `docs/ROADMAP.md` for
current priorities and `docs/BUGS.md` for the live defect list.

---

## 2026-09-09 — Documentation reconciliation

Triggered by the email-analytics build completing and being deployed to the dev
server. The code had moved a long way ahead of the documentation, and the docs
in this folder are synced to the partner-facing repo — so drift here is drift
the owners read.

### What was wrong

- **`HANDOFF.md` and `ROADMAP.md` were roughly two months stale.** Both still
  described the UX/SEO pass as in progress (it had long landed), listed the
  test suite as not started (279 tests exist), and listed deployment as "NOT
  STARTED — Railway target" — when Railway had been stood up *and retired*, and
  a dev server had gone live. Neither mentioned the analytics subsystem at all.
- **`TESTING.md` opened by stating no automated suite existed** and that
  `python -m pytest` would fail. It had not been true for some time.
- **The entire analytics subsystem was undocumented.** No description of what it
  does, and no record of the owner setup tasks it depends on.
- **`DEPLOY-UBUNTU.md` never mentioned the campaign worker.** Following it would
  produce a production deployment where campaigns are written, scheduled, and
  silently never sent — the compose stack has no worker service.
- **The earlier setup runbook was internally inconsistent about the network.**
  It described `89.187.170.160` as the front proxy for the Paladin box and told
  the owners to point the sending subdomain there *and* add a vhost alias on the
  Paladin machine. Live DNS shows those are two different hosts, so following it
  would have sent tracking traffic to the wrong server.
- **`BUGS.md` listed BUG-004 and BUG-005 as open** when both were fixed.

### What was done

- Wrote `EMAIL-ANALYTICS.md` (what the system is, the trust-tier model, machine
  detection, architecture) and `EMAIL-SETUP-RUNBOOK.md` (the ordered owner
  tasks, the three traps with fixes and verification commands, and the staged
  DMARC enforcement path).
- Rewrote `HANDOFF.md`, `ROADMAP.md` and `TESTING.md` against verified state —
  test counts taken from an actual `pytest --collect-only` run, not from memory.
- Added section 5.5 to `DEPLOY-UBUNTU.md` covering the worker, with both a
  compose service and a systemd option, and verification commands. The compose
  file itself was deliberately **not** modified: CI boots it on every push, and
  changing a tested deployment artifact during a documentation pass is how a
  green pipeline turns red for unrelated reasons. The gap is documented and
  flagged instead.
- Corrected the network description everywhere it appeared, and marked the
  `updates.ashfordbriggs.com` vhost alias as provisional pending the routing
  decision.
- Closed BUG-004 and BUG-005 against verified code. **Held BUG-006 open** — the
  spot check found the approved sections present, but that is heading-level
  evidence, and closing a content-parity bug on partial evidence is how wrong
  copy ships.

### Verified, not assumed

Test counts from `pytest --collect-only` (279, with the per-file breakdown in
`TESTING.md`); the absence of HTTP-level and database tests by grepping the
suite for `AsyncClient` / `ASGITransport` / `AsyncSession` (none); BUG-004 and
BUG-005 by reading the implementations; and every DNS claim against both a
public resolver and the dev server's own, including a live demonstration on the
zone that a name holding any record loses the wildcard's answer.

### Still open

Frontend test coverage is still zero. BUG-006 needs a full parity diff. The
tracking-host routing decision is unmade, and the owner setup tasks in
`EMAIL-SETUP-RUNBOOK.md` are untouched — nothing sends until they are done.

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

> **Superseded 2026-09-09.** Both paragraphs above were accurate when written
> and are not any more, kept because this is a log of events rather than a live
> tracker. The UX/SEO/CI work landed, and the testing findings are substantially
> remediated — 279 backend tests, though the frontend is still at zero. See the
> 2026-09-09 reconciliation entry at the top of this file.

---

## Prior audits

None recorded. This is the first formal audit pass on this project since the
initial scaffold (`docs/CHANGELOG.md`, 2026-07-06 entry).
