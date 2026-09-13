# Paladin website — overview

The marketing website, blog, and AI-assisted admin backend for **Ashford &
Briggs** (Jacksonville, FL), makers of **Paladin**: real-time AI intelligence
for recruiting phone calls (skills-gap analysis, live prompts, on-call jargon
definitions, post-call summaries) delivered through the recruiter's existing
phone, with no app to install.

This document is the orientation page. The other documents in this folder
cover deployment, testing, the roadmap, and change history.

## Environments

| Purpose | URL | Where it runs | Notes |
|---|---|---|---|
| Display / demo on Railway | retired 2026-09-09 | Railway | Shut down; `DEPLOY-RAILWAY.md` is kept as history. |
| Dev (company server) | https://devwww.ashfordbriggs.com | `ab-webserver`, shared company Ubuntu box | See `DEPLOY-DEV-SERVER.md`. Not indexed by search engines. |
| Production | ashfordbriggs.com (planned) | A self-managed Ubuntu server | Runbook: `DEPLOY-UBUNTU.md` with the files in `deploy/ubuntu/`. |

Every environment runs the same code from the `main` branch of the
`Vybecode-LTD/Paladin` repository and the same single-process design: one
FastAPI process serves the API under `/api/*` and the built React site for
every other path.

## What the site does

- **Public site:** Home, Product, How It Works, About, Contact (with a
  demo-request form), Blog, Privacy, Terms. Per-page SEO metadata, JSON-LD
  structured data, `robots.txt`, and a dynamically generated `/sitemap.xml`
  that includes every published post.
- **Blog:** posts are written in Markdown with an optional cover image and
  captioned in-body images. Workflow is draft → published, reversible.
- **Admin (`/admin`):** sign-in, post editor with preview, an AI assistant
  that drafts posts, proposes titles, writes excerpts and SEO fields, a
  demo-request inbox with email replies, sender settings, and user management.
- **Analytics (`/admin/analytics`):** email campaigns to a consented contact
  list, and honest measurement of what happened to them. Every figure is
  labelled with how far it can be trusted, because roughly half of all tracked
  email opens industry-wide are machines rather than people — so opens and
  clicks are always shown split between the two, and a reply counts for more than a hundred opens (capturing replies is still to
  be built). Includes a domain-trust panel (DMARC reports, blocklist
  checks, inbox placement) and a pre-flight check that refuses to send a broken
  campaign. Full detail in `EMAIL-ANALYTICS.md`; the full setup path, and who does
  each step, is in `EMAIL-SETUP-RUNBOOK.md`.
- **AI:** all generation runs server-side through a proxy to Anthropic's API.
  The API key never reaches a browser. Model: `claude-sonnet-4-6`
  (configurable).

## Roles

Three roles, ranked. Each includes everything below it.

| Role | Can |
|---|---|
| author | create, edit, and publish their own posts; use the AI assistant |
| editor | manage all posts, delete posts, work the demo-request inbox |
| admin | manage users and settings |

The first admin is created at deploy time by a one-off seed step; further
users are created from the admin UI.

## Technology

| Layer | Choice |
|---|---|
| Frontend | React 18, Vite, TypeScript, React Router, Framer Motion, react-markdown |
| Backend | FastAPI, async SQLAlchemy 2 with asyncpg, Alembic migrations |
| Database | PostgreSQL (14 on the dev server, 17 in the production compose stack) |
| Auth | JWT access + refresh tokens, bcrypt password hashes, per-IP rate limiting on login, demo requests and AI calls |
| Email — transactional | The company's own SMTP server, configured in the admin Settings screen (host, port, TLS, account, sender address and name); the password is stored encrypted. The sender address must be one the account is allowed to send as; blank falls back to info@ashfordbriggs.com |
| Email — campaigns | Mailgun, configured in the admin Sender settings screen. Chosen because raw SMTP structurally cannot report delivery, bounces or spam complaints — the facts the analytics depend on. SMTP remains available as a fallback with that limitation. Credentials are encrypted at rest |
| Background work | A `paladin-worker` systemd service driven by a timer: sends due campaigns and runs the daily domain-trust checks. Holds a Postgres advisory lock so overlapping runs cannot double-send |
| Build / run | One Dockerfile builds the frontend and serves it with the backend; the same image is used by the production compose stack and CI's smoke test. The dev server runs the equivalent manual install. |

## Repository layout (`Vybecode-LTD/Paladin`)

```
backend/     FastAPI app: app/core (config, db, security), app/routers, app/models,
             app/schemas, app/services (Anthropic proxy, blog, email, and the
             campaign/tracking/trust services), app/worker.py, alembic/, seed.py
frontend/    React app: src/pages (incl. pages/admin/analytics), src/layouts,
             src/components, src/lib/api.ts, src/styles, public/ab-beacon.js
deploy/      Production deployment files (deploy/ubuntu: compose, Caddyfile,
             .env.example, paladin-worker.service, paladin-worker.timer)
docs/        This documentation (source of truth; the docs repo is a synced copy)
Dockerfile   Builds frontend + backend into one image; runs migrations, optional admin seed, then the server
.github/     CI: backend tests, frontend lint/build, and a deploy-image smoke test on every push
```

## Configuration

Every deployment is configured through environment variables; none are
committed. The domain-dependent ones are `SITE_URL` (feeds the sitemap) and
`CORS_ORIGINS`. Secrets are `JWT_SECRET_KEY`, `ENCRYPTION_KEY` (protects the
stored SMTP and Mailgun credentials), `ANTHROPIC_API_KEY`, and the database
connection. Each runbook lists the exact set with a generation command per secret.

The Mailgun credentials are entered through the admin UI rather than the
environment, and there are **two of them**: the **API key**, which sends, and the
**HTTP webhook signing key**, which verifies the delivery events Mailgun sends
back. They live on different pages of the Mailgun console and are easy to
confuse. Without the correct signing key the system rejects every incoming
event — deliberately, since accepting unverified webhooks would let anyone forge
delivery data.

The frontend carries `ashfordbriggs.com` as its canonical domain in a few
compiled-in places (canonical/Open Graph tags, structured data, `robots.txt`).
That is intentional for the eventual production domain; the display and dev
sites leave it as is.

## Where to look next

- **Setting up email campaigns (start here):** `EMAIL-SETUP-RUNBOOK.md` — the full ordered path from today's build to a first campaign, production and a locked-down domain, with who does each step, how to check it worked, and the nine mistakes nothing will warn you about.
- How the campaign analytics work: `EMAIL-ANALYTICS.md`.
- Deploying: `DEPLOY-UBUNTU.md` (production), `DEPLOY-DEV-SERVER.md` (dev box), `DEPLOY-RAILWAY.md` (the retired display deployment, history only).
- What is planned and what is open: `ROADMAP.md`, `BUGS.md`.
- What changed when: `CHANGELOG.md`.
- Test and security posture: `TESTING.md`, `AUDIT-LOG.md`.
- Picking up development: `HANDOFF.md`.
- Approved marketing copy: `content/`. The original single-page site copy is frozen in `original-snapshot/` as a revert point only.
