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
  demo-request inbox with email replies, SMTP settings, and user management.
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
| Email | The company's own SMTP server, configured in the admin Settings screen (host, port, TLS, account, sender address and name); the password is stored encrypted. The sender address must be one the account is allowed to send as; blank falls back to info@ashfordbriggs.com |
| Build / run | One Dockerfile builds the frontend and serves it with the backend; the same image is used by the production compose stack and CI's smoke test. The dev server runs the equivalent manual install. |

## Repository layout (`Vybecode-LTD/Paladin`)

```
backend/     FastAPI app: app/core (config, db, security), app/routers, app/models,
             app/schemas, app/services (Anthropic proxy, blog, email), alembic/, seed.py
frontend/    React app: src/pages, src/layouts, src/components, src/lib/api.ts, src/styles
deploy/      Production deployment files (deploy/ubuntu: compose, Caddyfile, .env.example)
docs/        This documentation (source of truth; the docs repo is a synced copy)
Dockerfile   Builds frontend + backend into one image; runs migrations, optional admin seed, then the server
.github/     CI: backend tests, frontend lint/build, and a deploy-image smoke test on every push
```

## Configuration

Every deployment is configured through environment variables; none are
committed. The domain-dependent ones are `SITE_URL` (feeds the sitemap) and
`CORS_ORIGINS`. Secrets are `JWT_SECRET_KEY`, `ENCRYPTION_KEY` (protects the
stored SMTP password), `ANTHROPIC_API_KEY`, and the database connection. Each
runbook lists the exact set with a generation command per secret.

The frontend carries `ashfordbriggs.com` as its canonical domain in a few
compiled-in places (canonical/Open Graph tags, structured data, `robots.txt`).
That is intentional for the eventual production domain; the display and dev
sites leave it as is.

## Where to look next

- Deploying: `DEPLOY-UBUNTU.md` (production), `DEPLOY-DEV-SERVER.md` (dev box), `DEPLOY-RAILWAY.md` (the retired display deployment, history only).
- What is planned and what is open: `ROADMAP.md`, `BUGS.md`.
- What changed when: `CHANGELOG.md`.
- Test and security posture: `TESTING.md`, `AUDIT-LOG.md`.
- Picking up development: `HANDOFF.md`.
- Approved marketing copy: `content/`. The original single-page site copy is frozen in `original-snapshot/` as a revert point only.
