# Handoff — Ashford & Briggs / Paladin

Written for whoever (human or Claude session) picks this project up next, cold.
Read this before touching code. `CLAUDE.md` at the repo root has the stack and
layout reference; this file is about *state*.

**Last updated: 2026-09-12.**

## What this project is

Marketing site + blog + AI-assisted admin backend for Ashford & Briggs
(Jacksonville, FL), makers of Paladin — real-time AI intelligence for recruiter
phone calls. Since 2026-09-09 it also contains an **email campaign analytics
system**, which is the current focus of work.

## Where things stand

| | |
|---|---|
| Current branch | `feat/email-campaign-analytics` — **open PR, not merged** |
| Live environment | Dev only: https://devwww.ashfordbriggs.com (company Ubuntu box) |
| Production | Does not exist yet. Server access being arranged by the owner. |
| Backend tests | 279, passing |
| Blocked on | Owner tasks in `EMAIL-SETUP-RUNBOOK.md` — Mailgun domain, DNS, and the routing decision |
| Owner setup done | DMARC report group `dmarc@ashfordbriggs.com` is live, with both DMARC records pointing at it (2026-09-12) |

## What is done

1. **Scaffold, security hardening, UX/SEO/accessibility** — all complete and
   verified. The July 2026 handoff described the UX/SEO pass as "in progress";
   it landed long ago. See `CHANGELOG.md`.
2. **Alembic migrations** — the init migration plus five for the analytics
   subsystem. Dev mode no longer relies on lifespan table creation.
3. **Deployment** — Railway display site stood up 2026-09-08 and **retired
   2026-09-09** (`DEPLOY-RAILWAY.md` is history only; `railway.toml` is gone).
   The dev/demo copy went live on the company server 2026-09-09
   (`DEPLOY-DEV-SERVER.md`).
4. **Email campaign analytics, phases 1–5** — complete, committed, deployed to
   the dev server. Contacts and consent, campaigns and sending via Mailgun,
   root-mounted tracking, honest engagement tiers, statistics with significance
   testing, and the domain-trust panel with pre-flight. See `EMAIL-ANALYTICS.md`
   for the design and `CHANGELOG.md` for the per-phase detail.
5. **A real test suite** — 279 backend tests, weighted toward the parts where
   being wrong is expensive (77 on the machine classifier alone). This closes
   what previous handoffs called the biggest structural gap in the project.

## What is next

1. **Merge the open PR.** It carries the whole analytics subsystem.
2. **The owners' setup tasks.** Nothing sends until these are done — they are
   account and DNS actions no developer can do. `EMAIL-SETUP-RUNBOOK.md` is the
   complete list, ordered, with verification commands.
3. **The routing decision (runbook step B1).** Which machine serves the
   tracking hostname. This is the only open architectural question, and the
   vhost line, the certificate and the Mailgun webhook URL all wait on it.
4. **Production server.** Being arranged. `DEPLOY-UBUNTU.md` is the runbook.
   Note that server access and DNS access are separate grants — root on the
   production box does not let anyone publish the Mailgun records.
5. **Frontend tests.** Still zero. The backend is well covered; Vitest + RTL for
   `AuthContext`, the analytics pages and `PostEditor` is the remaining gap.

## Things that will trip you up

- **`models/__init__.py` must import every model.** Alembic autogenerate silently
  drops any table whose model is not imported there. This is the cardinal rule of
  this repo.
- **Postgres enum types survive `drop_table`.** `sa.Enum` creates the type as a
  side effect of `create_table`, and `drop_table` does not remove it — so a
  downgrade followed by an upgrade dies on "type already exists". Both analytics
  migrations hit this. Every migration touching an enum needs an explicit
  `DROP TYPE IF EXISTS` loop in `downgrade()`. **Round-trip down-then-up before
  committing a migration**; that is the only way this gets caught.
- **Router order in `main.py`.** `tracking.router` must be registered *before*
  the SPA catch-all, or the React app swallows every tracking URL.
- **Two different Mailgun credentials.** The API key sends; the HTTP webhook
  signing key verifies inbound events. They are on different pages and are easy
  to confuse. The webhook verifier fails closed.
- **The dev server is shared.** It also runs PBX and three other websites. Touch
  only the Paladin footprint listed in `DEPLOY-DEV-SERVER.md`.
- **`sites-enabled/` on that box holds a real file, not an `a2ensite` symlink.**
  Editing `sites-available/www.ashfordbriggs.com.conf` changes nothing — that
  copy is a stale version of the old static site and still has a `:443` block.
- **The DNS wildcard.** `*.ashfordbriggs.com` resolves to the nginx host, which
  is *not* the machine Paladin runs on. And a wildcard stops answering for any
  name that gains a record of any type. Both facts matter before touching DNS —
  see the runbook.
- **The Reply domain setting loses replies.** Nothing records replies yet (BUG-008).
  With a reply domain set, every reply goes to `replies+<token>@<domain>`, which
  nothing reads. Keep it blank; replies then go to the From address.
- **Send a test is not tracked.** Test sends use a preview token, so opens, clicks
  and unsubscribes from them record nothing. Rehearse with a real send to an internal
  tag.
- **Paladin's dev vhost is bound to `10.0.0.80:80`.** A request reaching the box on
  any other address, such as its Tailscale address, is served by a different site.
  A proxy that forwards there needs that address added to the vhost.
- **Real campaigns go out from production only.** Links in sent mail cannot be
  changed, and the unsubscribe must keep working for at least 30 days. Dev rehearses
  with internal addresses, using `devwww` as its tracking URL.

## Known gaps and risks

- **No frontend tests.** Regressions in the admin UI would go undetected.
- **Rate limiting is degraded in the dev deployment.** The proxy in front of
  Paladin sends no forwarding headers, so every visitor shares one bucket and
  the per-IP limits act as global caps. Fixed by adding `X-Forwarded-For` at
  whichever proxy ends up in front — see runbook step E3.
- **The root domain and `mail.` are both at `p=none`.** DMARC reports but
  enforces nothing. `mail.ashfordbriggs.com` has its own record, so it is staged
  separately from the root. The staged path is in the runbook; the Trust panel
  gates it.
- **Automatic DMARC report collection is not built, and needs a mailbox first.**
  Reports can be uploaded to the panel today, which is enough to use it. The
  report address, `dmarc@ashfordbriggs.com`, is a Google Group, which has no
  inbox software can sign into, so automation needs one member of the group
  that is a real mailbox. That is a decision for the Workspace admin, not code.
- **No reply capture** (BUG-008, runbook G5) and **no way to load past opt-outs**
  (runbook F1). Past opt-outs must be loaded before the first real campaign; reply
  capture can follow, since replies are forwarded to a person meanwhile.
- **The account-wide Mailgun API key is in use.** A sending-only key would fail the
  connection check, which reads the domain's details; switching needs that check
  changed first (runbook G3).

## Where to look

- `EMAIL-ANALYTICS.md` — what the analytics system is and how it works.
- `EMAIL-SETUP-RUNBOOK.md` — the full setup path, in order, with who does each
  step. Start here if setup is the question.
- `OVERVIEW.md` — orientation for someone new to the whole project.
- `DEPLOY-DEV-SERVER.md` / `DEPLOY-UBUNTU.md` — the two live runbooks.
  `DEPLOY-RAILWAY.md` is history only.
- `ROADMAP.md`, `BUGS.md`, `TESTING.md`, `CHANGELOG.md`, `AUDIT-LOG.md`.
- `content/` — approved marketing copy. `original-snapshot/` is a frozen revert
  point, not current copy.
