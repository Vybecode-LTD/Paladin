# Testing — Ashford & Briggs / Paladin

**Last updated 2026-09-09.**

## Current state

| | |
|---|---|
| Backend tests | **279**, passing |
| Frontend tests | **0** |
| Level | Service/unit only — no HTTP-route or database integration tests |
| End-to-end | One: CI's `deploy-image` job |

Run them:

```bash
cd backend && python -m pytest
```

*(Earlier versions of this document said no automated suite existed and that
`python -m pytest` would fail. That has not been true since 2026-09-09.)*

## Backend suite — what is covered

| File | Tests | Covers |
|---|---:|---|
| `test_classifier.py` | 77 | Machine vs human detection: scanner user agents, Apple MPP shape detection, gateway referers, the 10-second prefetch window, link-sweep detection at threshold |
| `test_mailgun_sender.py` | 24 | Request construction, webhook HMAC verification, event parsing, dedupe keys |
| `test_event_mapping.py` | 24 | Mailgun event → event type and trust tier |
| `test_contact_consent.py` | 24 | Consent basis, mailability, tracking-consent gating, protected statuses on import |
| `test_render_service.py` | 21 | Personalisation, link extraction, unsubscribe URLs, `List-Unsubscribe` headers |
| `test_preflight.py` | 21 | The four send-time blockers, plus warnings and notes |
| `test_significance.py` | 17 | Two-proportion z-test, and refusing a verdict below the sample threshold |
| `test_dmarc_parser.py` | 17 | gzip / zip / bare XML by magic bytes, alignment read from `policy_evaluated` |
| `test_link_rewriting.py` | 16 | HTML and text link rewriting, pixel tag construction |
| `test_campaign_variants.py` | 13 | Salted-hash variant and holdout assignment, stability |
| `test_email_service.py` | 11 | SMTP TLS mode selection, including implicit TLS on port 465 (BUG-007) |
| `test_suppression.py` | 7 | Normalisation, lookup, filtering |
| `test_svg_sanitize.py` | 7 | AI header-image SVG sanitizer |

The weighting is deliberate. The classifier carries a third of the suite because
it is the component where being quietly wrong is most expensive — a
misclassification does not throw an error, it silently reports a machine as a
person and corrupts every number built on top of it.

## What these tests do *not* cover

Being explicit, because the count alone would mislead:

- **No HTTP-level tests.** Nothing exercises the FastAPI routes through an ASGI
  client. Auth, RBAC boundaries, and the tracking and webhook endpoints are
  verified only through their underlying services, plus manual curl checks.
- **No database integration tests.** No test opens a session against real
  Postgres, so migrations, constraints, the `dedupe_key` unique index and the
  `FOR UPDATE SKIP LOCKED` claim path are not covered by automation. Migrations
  are verified by hand-running a down-then-up round trip before commit — which
  is how both enum-drop defects were caught.
- **No frontend tests at all.**

## Deploy-path smoke test (CI, since 2026-09-09)

The `deploy-image` job in `.github/workflows/ci.yml` is the only automated
end-to-end check. On every push it validates
`deploy/ubuntu/docker-compose.yml`, builds the production image from the root
`Dockerfile`, boots it against a throwaway Postgres 17, and asserts that the
Alembic migrations ran, the seeded admin was created and can log in, `/api/health`
and `/api/blog/posts` return 200, and `/` serves the built React app.

It does not replace a unit suite; it proves the deploy path itself.

## Verified by hand, not by tests

Recorded here so the distinction stays honest:

- **The 2026-07-07 security pass** — rate limiting returning 429, malformed
  UUIDs returning clean 401/404, short passwords rejected with 422. Confirms
  BUG-001…003 by curl against a running dev server, with no regression test
  behind them.
- **The 2026-09-09 dev deployment** — admin routes 401 without a token, tracking
  routes return 200/302, the Mailgun webhook returns 403 when unsigned (failing
  closed), and the other three sites on the shared box were unaffected.
- **DMARC ingestion against a real report** — a gzipped report with three
  sources parsed, deduplicated on resend, sorted worst-first, and correctly
  refused to clear the domain for enforcement while one source was failing.

## Planned — frontend (Vitest + React Testing Library)

Not started. Priority order:

1. `AuthContext` — login, logout, token storage, refresh-on-401.
2. The analytics pages — the tier labelling in particular, since presenting an
   `inferred` figure as though it were `exact` is the exact failure the whole
   subsystem exists to prevent.
3. Admin `PostEditor` — draft/publish transitions, AI calls mocked at the API
   client boundary.
4. Public pages — smoke renders, catching content-parity regressions (BUG-006).
5. Contact form — submission, validation, error states.

Roughly 15–25 cases, plus an optional Playwright path (admin login → create post
→ publish → visible on `/blog`).

## Filling the backend gaps

In rough priority, if someone picks this up:

1. **HTTP-level tests** with httpx `AsyncClient` + `ASGITransport` — auth, RBAC
   boundaries on every protected route, and the tracking/webhook endpoints.
2. **A database fixture** — transactional rollback per test — so the claim path,
   dedupe constraint and migrations get real coverage.

## Coverage thresholds

None enforced. `CLAUDE.md`'s general gates (85% PR / 95% deploy) are aspirational
here and not wired into CI. Treat coverage as informational until an HTTP-level
suite exists, since the current number would measure only the service layer.
