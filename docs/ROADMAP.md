# Roadmap — Ashford & Briggs / Paladin

How this project is progressing from scaffold to production. Updated as phases
complete. **Last updated 2026-09-12.**

## Phases

### 1. Scaffold — COMPLETE
Backend (FastAPI + async SQLAlchemy + Alembic) and frontend (React + Vite + TS)
fully scaffolded. Five marketing pages, blog reader, full admin (login,
dashboard, post list, demo inbox, AI-assisted post editor). Original copy frozen
in `docs/original-snapshot/`, expanded copy in `docs/content/`.

### 2. Security hardening — COMPLETE (2026-07-07)
Rate limiting on login (10/min) and demo requests (5/hour); three unguarded
`uuid.UUID()` calls fixed (clean 401/404 instead of unhandled 500s); password
length validation; self-service password change and admin user management;
error handling around the Anthropic proxy; `max_length` caps on AI schemas;
`DEBUG=false` by default. Committed. See `BUGS.md` (BUG-001…003) and `CHANGELOG.md`.

### 3. UX / SEO / accessibility — COMPLETE
Per-page SEO metadata via a shared `<Seo>` component, `robots.txt`, a **dynamic**
backend-generated `/sitemap.xml` covering every published post, JSON-LD, a 404
route, responsive admin layout, click-to-copy in the post list, a real
access-token-refresh flow (closing BUG-004), content-parity fixes, and GitHub
Actions CI.

*(Earlier versions of this file listed this phase as in progress. It is done.)*

### 4. Deployment — COMPLETE for dev; production pending
- **Railway display site** — stood up 2026-09-08, **retired 2026-09-09** at the
  owner's request. `DEPLOY-RAILWAY.md` is kept as history; `railway.toml` removed.
- **Dev/demo server** — live since 2026-09-09 at https://devwww.ashfordbriggs.com
  on the shared company Ubuntu box, installed the manual way (venv + systemd +
  existing Postgres 14 + Apache reverse proxy behind a front proxy that owns
  TLS). Runbook: `DEPLOY-DEV-SERVER.md`. **That box also runs PBX and three
  other sites — touch only the Paladin footprint.**
- **Production** — does not exist yet; server access is being arranged by the
  owner. Runbook ready at `DEPLOY-UBUNTU.md` with the files in `deploy/ubuntu/`,
  and CI's `deploy-image` job boots that exact image on every push so the path
  stays continuously tested.

### 5. Email campaign analytics — COMPLETE (2026-09-09)
Built in five phases and deployed to the dev server. Design and architecture in
`EMAIL-ANALYTICS.md`; owner setup tasks in `EMAIL-SETUP-RUNBOOK.md`.

1. Contacts, consent basis and suppression.
2. Campaigns, Mailgun sending, root-mounted tracking, webhook ingestion.
3. Honest engagement tiers and machine detection.
4. Statistics, A/B significance testing, scorecards, sender settings.
5. Domain trust: DMARC ingestion, blocklists, seed inboxes, pre-flight.

**Not in production use yet** — sending is blocked on the owner tasks (Mailgun
sending domain, DNS records, and the tracking-host routing decision). One gap found since: nothing records replies
yet (BUG-008).

### 6. Automated tests — BACKEND COMPLETE, FRONTEND NOT STARTED
**279 backend tests**, weighted toward the parts where being wrong is expensive:
77 on the machine classifier, plus Mailgun event mapping, consent gates, link
rewriting, significance testing, the DMARC parser, pre-flight and the SVG
sanitizer. Plus CI's end-to-end `deploy-image` smoke test.

Frontend remains at zero. See `TESTING.md`.

## Backlog (prioritized)

Step codes refer to `EMAIL-SETUP-RUNBOOK.md`.

1. **Merge the open analytics PR.**
2. **Owner setup tasks** — nothing sends until these are done, and they are
   account/DNS actions no developer can perform. The DMARC report group is done
   (2026-09-12).
3. **The tracking-host routing decision** (B1) — the only open architectural
   question; the certificate, the vhost line and the webhook URL all depend on it.
4. **Production deployment** (phase E) once the server exists. Real campaigns go
   out from production only; dev is for rehearsal.
5. **Import past opt-outs** (F1) — no endpoint or screen exists, and it is needed
   before the first real campaign.
6. **Fix forwarded headers at the proxy** (E3) — Paladin currently sees every
   visitor as one IP, so per-visitor rate limits act as global caps.
7. **Reply capture** (G5, BUG-008) — nothing records replies. Until it exists the
   Reply domain setting must stay blank, and replies are forwarded to a person.
8. **Frontend test suite** (Vitest + RTL) — prioritize `AuthContext`, the
   analytics pages, and `PostEditor`.
9. **Automatic DMARC report collection** (G1) — the report address is a Google
   Group, which has no inbox to sign into, so this needs a real mailbox added as a
   member of `dmarc@ashfordbriggs.com` first. Upload works today.
10. **A sending-only Mailgun key** (G3) — the connection check reads the domain's
    details, which such a key cannot; change the check, then swap the key.
11. **Rotate the 1024-bit DKIM key** on `mail.ashfordbriggs.com` to 2048-bit (H1),
    carefully — it signs customer password emails.
12. **Advance the domain toward DMARC enforcement** (H3, H4) — staged, gated by the
    Trust panel's verdict. `mail.ashfordbriggs.com` has its own DMARC record and has
    to be advanced separately from the root.

## Non-goals (for now)

- No heavyweight doc-management framework — plain Markdown, hand-maintained.
- No multi-tenant support, no i18n — single marketing site, single company.
- **No Google Postmaster Tools integration** — needs domain-wide delegation and
  shows nothing below a few hundred Gmail messages a day. Revisit if the list
  grows an order of magnitude.
- **No SpamAssassin** — not a reasonable daemon to run on a shared box serving
  three other sites.
- **No way to remove an address from the suppression list.** Intentional.
