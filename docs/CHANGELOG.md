# Changelog — Ashford & Briggs / Paladin

All notable changes to this project, in date order. Not committed to git yet as
formal tags/releases — this log tracks work sessions, not package versions.

## 2026-09-09 (latest) — Documentation reconciliation

**Added:** the two documents the analytics subsystem never had, and a pass to
stop the rest of the folder contradicting the code. These docs sync to the
partner-facing repo, so drift here is drift the owners read.

- **`EMAIL-ANALYTICS.md`** — what the system is and how it works: the trust-tier
  model, the machine-detection rules and their thresholds, the architecture, and
  the things deliberately not built with the reasoning for each.
- **`EMAIL-SETUP-RUNBOOK.md`** — the ordered owner tasks, with the three traps
  that cause real damage, how to fix each, how to verify, and how to recover.
  Also the staged path from `p=none` to `p=reject` on the root domain.
- **`HANDOFF.md` and `ROADMAP.md` rewritten.** Both were roughly two months
  stale: they described the UX/SEO pass as in progress, the test suite as not
  started, and deployment as "NOT STARTED — Railway target", when Railway had
  been stood up *and* retired and a dev server was live. Neither mentioned the
  analytics subsystem.
- **`TESTING.md` rewritten** against a real `pytest --collect-only` run. It had
  opened by saying no automated suite existed and that `python -m pytest` would
  fail. It now carries the per-file breakdown and — more usefully — an explicit
  statement of what the 279 tests *do not* cover: no HTTP-level tests, no
  database integration, no frontend tests. A count without that caveat misleads.
- **`DEPLOY-UBUNTU.md` section 5.5** — the production runbook never mentioned the
  campaign worker, and the compose stack has no worker service. Following it
  would produce a deployment where campaigns are written, scheduled, and
  silently never sent. Documented with both a compose service and a systemd
  option, plus commands to verify it is actually running, because the failure
  mode here is silence rather than an error.

**Corrected a real inconsistency in the earlier runbook.** It described
`89.187.170.160` as the front proxy for the Paladin box and told the owners to
point the sending subdomain at it while also adding a vhost alias on the Paladin
machine. Live DNS shows those are two different hosts — the wildcard target is
an nginx server hosting the public website, while Paladin is reached through
`104.48.125.58`. Following the old instruction would have sent tracking traffic
to the wrong server. The choice between them is now an explicit task.

**Changed the recommendation on the tracking hostname.** Serving web traffic
from the Mailgun sending domain forces that name to hold both mail records and
an A record — and a DNS wildcard stops answering for any name that gains a
record of any type, so publishing the SPF record would silently remove its
address. Demonstrated on the live zone: `_dmarc.ashfordbriggs.com` holds a TXT
record and returns nothing for an A query, while an invented name still
resolves. Keeping the sending domain mail-only and serving tracking from a
separate name removes the trap entirely, and needs no new DNS record at all.
The `updates.ashfordbriggs.com` vhost alias is marked provisional pending that
decision.

**Not changed on purpose:** `deploy/ubuntu/docker-compose.yml`. CI boots it on
every push, and editing a tested deployment artifact during a documentation pass
is how a green pipeline turns red for unrelated reasons. The missing worker is
documented and flagged rather than silently added.

**BUG-004 and BUG-005 closed** against verified implementations. **BUG-006 held
open** — a spot check found the approved copy sections present, but that is
heading-level evidence, and closing a content-parity bug on partial evidence is
how wrong copy ships.

## 2026-09-09 — Email campaign analytics: the trust panel

**Added:** the domain's standing on one screen, and the pre-flight check that
stops a campaign going out broken. Completes the five-phase build.

- **DMARC report ingestion** (migration `a132dbcacc3b`). The parser reads the
  gzipped, zipped or bare XML every mailbox provider sends daily, and the panel
  groups it by sending source. Alignment is read from `policy_evaluated`, not
  from the raw auth results — the difference matters: a forged message can show
  DKIM "pass" for the forger's own domain, and reading the raw result would
  report it as a healthy sender.
- **The panel carries the verdict that gates real work:** whether it is safe to
  tighten the domain policy. It refuses while any source is still failing,
  because enforcing before the failing sources are told apart is how a company
  silently stops receiving its own mail. Worst source is listed first.
- **Blocklist checks** over plain DNS, no account or key. A Spamhaus refusal —
  which is what a public resolver gets — is reported as an error rather than a
  listing, so a resolver problem never appears on the panel as a reputation
  problem.
- **Seed inbox placement** over IMAP, including Gmail's Promotions tab, which
  is not a folder and needs Gmail's own search extension to detect. "Could not
  check" is deliberately a distinct result from "never arrived", and only the
  latter is stored, so an expired password does not freeze a false delivery
  alarm into the record.
- **Pre-flight**, our own rules rather than SpamAssassin: running its daemon on
  a shared machine that serves three other sites is not a reasonable trade, and
  the things that actually hurt this sender are a short list that can be checked
  exactly and explained in words an author can act on. Four blockers — no
  sender, no From address, no tracking URL, no postal address — are enforced at
  send time, not merely offered as advice. Everything else is a warning or a
  note, because a checker that blocks on style is one people work around.
- **The worker now runs the daily checks** as well as campaigns, rate-limited
  by when the last check actually ran rather than by a second timer unit.
- **38 new tests** (279 total) on the DMARC parser and the pre-flight rules.

**Deliberately not built: the Google Postmaster Tools API.** It needs a service
account and domain-wide delegation to set up, and Google shows no data below
roughly a few hundred messages a day to Gmail — far above what this company
sends. It would be an OAuth integration displaying an empty panel. The DMARC
reports and seed inboxes answer the same questions and do work at this volume.
Worth revisiting if the list grows an order of magnitude.

**Not yet automated: polling the dmarc mailbox.** Reports can be uploaded to
the panel today, which is enough to use it. Automatic collection needs IMAP
credentials for that mailbox, which is a decision about who owns it rather than
a piece of code — the same shape as the seed inboxes, and it reuses their
mechanism when the answer exists.

**Fixed before shipping:** the generated migration's downgrade omitted the
`seed_placement` enum type, the same defect found in the analytics migration.
Caught by round-tripping again.

**Verified against real data:** a gzipped report with three sources — Google
passing, a Mailgun subdomain passing, and an address forging the domain —
parsed, deduplicated on resend, sorted worst-first, and correctly refused to
call enforcement safe until the forging source was removed. Blocklist checks
ran against the real domain over real DNS and came back clear on both lists.

## 2026-09-09 — Email campaign analytics: the Analytics tab

**Added:** the dashboard, and the endpoint the product reports conversions to.
One sidebar entry at `/admin/analytics` with its own tab bar — Overview,
Campaigns, Contacts — rather than five more entries in a sidebar that already
had five.

- **Every figure carries its tier, and the inferred ones are drawn as a
  split.** Opens and clicks are never shown as a single total, because a
  single total is about half automatic prefetch and a number with a percent
  sign next to it gets believed. The bar and the named breakdown underneath
  ("Gmail image proxy 9", "Apple privacy prefetch 7") are the product.
- **The open rate is deliberately not shown as a rate.** Recipients who never
  consented to open tracking carried no pixel, so they were never measurable
  and cannot be counted as people who did not open. The scorecard says so in
  words rather than quietly dividing by the wrong denominator.
- **A/B tests refuse to name a winner they cannot support.** Below about
  thirty per variant the answer is "not enough recipients to tell", with the
  number needed. Measured on verified clicks, not opens: a subject line is
  meant to influence opens, but testing on them would measure which subject
  the prefetchers preferred. Two-proportion z-test via `math.erf`, so no new
  dependency.
- **The audience preview reconciles.** In the editor, contacts in the segment
  minus each exclusion equals the number that will actually be sent to, so
  nobody disappears without a reason visible on screen.
- **Attribution** at `POST /api/attribution` (migration `f63fe229a69a` adds the
  `converted` event type). The product reports a demo booked or a first login
  against a message token; the token is the credential, because holding one
  requires having received that message, and the worst a recipient can do is
  over-report their own engagement. Deduped per action per message so a
  product that reports every login does not turn one person into a hundred
  conversions.
- **Send-time recommendation** built from verified engagement only, and it
  refuses below twenty observations. Built from inferred opens it would
  recommend whenever Apple's servers happen to prefetch.
- **17 new tests** (241 total) covering the significance arithmetic — the one
  piece here that can be silently wrong and still look right, producing a
  confident sentence about a coin toss.

**Verified in the running app** against seeded data on a real database: the
scorecard's figures reconcile (34 sent, 25 opens split 16 machine and 9
possibly human, 19 clicks split 12 and 7, per-link totals summing to the
click total), the A/B block correctly refused on 19 against 15 recipients, the
send-time panel correctly refused on 7 observations, and the audience preview
reconciled 46 minus 4 minus 1 to 41. TypeScript, ESLint at zero warnings, and
the production build are clean.

**Note on the local dev database:** it now holds a seeded example campaign and
46 synthetic contacts on `@example.com` addresses, left in place so the
dashboard has something to show. Nothing was sent; the send path used a stub.

## 2026-09-09 — Email campaign analytics: track and classify

**Added:** open and click tracking on our own domain, and the classifier that
decides whether either was a person or a machine. This is the phase the whole
tier system was designed around.

- **Two invariants hold everywhere, and both are pinned by tests.** Nothing in
  the tracking path ever records `verified` except the landing-page beacon and
  an unsubscribe — a pixel fetch and a redirect hit are both things a machine
  does perfectly, so neither can prove a person. And every classification
  carries a reason string, stored on the event, so a wrong rule can be found
  against real data later instead of leaving a number nobody can account for.
- **The classifier** (`services/classifier.py`) names Gmail's image proxy and
  Yahoo's separately from generic scanners because they appear on every open
  through those providers; spots Apple's Mail Privacy Protection relay by the
  browser identity it strips from an otherwise ordinary WebKit agent; matches
  around thirty machine agent fragments; reads the rewriting hosts of
  Defender Safe Links, Proofpoint, Mimecast and Barracuda out of the referer;
  and treats an open inside ten seconds of the send as the mail system
  fetching images rather than a person reading.
- **Sweep detection catches the case user-agent checks cannot.** A security
  product forwarding the recipient's own browser string is invisible at the
  redirect — but it walks every link in the message within seconds, which no
  person does. Three distinct links inside thirty seconds is a sweep.
- **The landing-page beacon is the only thing that promotes a click.**
  Scanners fetch pages; they do not run scripts. `frontend/public/ab-beacon.js`
  is a few lines that fire an image request when a real browser renders the
  page, and it derives the tracking host from the referrer so the domain is
  configured in exactly one place — the app's settings — rather than
  duplicated into a file where it would silently go stale. It also strips the
  token back out of the address bar, so a message identifier does not travel
  into whatever the visitor copies, shares or bookmarks.
- **Links are numbered per campaign** and frozen on first expansion (migration
  `fdd908ed97a5`). A click URL carries only an index, which keeps it short —
  it is printed in mail that can never be edited — and re-numbering after a
  send would point old links at the wrong destinations.
- **The unsubscribe link is structurally safe from rewriting.** It lives in the
  footer template, and link extraction only ever looks at the Markdown body,
  so it cannot be picked up. That is a property of the arrangement rather than
  a rule someone has to remember.
- **The pixel is embedded per recipient**, from the contact's tracking consent,
  and `pixel_embedded` is recorded on the message as a historical fact — so an
  open rate can state honestly how much of the audience was measurable at the
  time, even after someone's consent changes. Removing the pixel from a
  message changes nothing else about it, which a test asserts by byte
  comparison.
- **93 new tests** (224 total), plus an end-to-end pass against real Postgres
  covering the sweep rule's wiring, which the unit tests cannot reach: the
  query that reads link indices back out of JSONB payloads. Three clicks read
  as human, the fourth is caught at exactly the threshold, and nothing is ever
  discarded — machine clicks stay recorded and separable rather than deleted.

**Fixed during verification:** the first version of the sweep test used a
campaign with two links against a threshold of three, so the rule could never
fire and the test passed while proving nothing. Rewritten with five links, and
it now asserts the sweep is caught *at* the threshold rather than merely at
some point.

**Not yet done:** IP-based classification. The front proxy on the dev server
forwards no client address, so every request appears to come from one IP.
Until it sends `X-Forwarded-For`, the datacentre-range check that would catch
scanners with unremarkable agent strings cannot be written honestly, and the
classifier degrades to user agent, referer and timing. Task C2 in the setup
runbook.

## 2026-09-09 — Campaign sender settings screen

**Added:** a settings screen for the campaign sender, brought forward from the
Analytics phase. The API for it shipped with the foundation work below; without
a screen, configuring it meant an admin making an authenticated API call by
hand, which is not a reasonable thing to ask.

- **Lives on the existing Settings page**, which is where an admin already goes
  for mail configuration, so it needs no new route or sidebar entry. It moves
  into the Analytics tab later if that reads better there.
- **The page now has two labelled sections**, "Demo replies" and "Campaign
  sending", each saying what it is for. Two mail configurations on one screen
  is a reasonable thing to be confused by, and the answer — one is a person
  answering a single request, the other is a campaign to a list, and they
  should send from different domains — is worth stating rather than leaving to
  be inferred.
- **Provider-conditional fields.** Choosing SMTP hides the Mailgun fields and
  explains that the path reports no delivery, bounce or complaint data and
  suits internal test sends only.
- **The webhook signing key field says, at the point of entry, that it is a
  different credential from the API key.** Getting those two the wrong way
  round rejects every incoming event and shows an empty dashboard with no
  error anywhere, which is the worst kind of failure to debug.
- **The screen computes the webhook URL** from the tracking URL and offers it
  to copy, removing a step from the Mailgun setup where a hand-typed path is
  easy to get wrong.
- **Two test actions.** "Check connection" verifies the credentials and that
  the sending domain exists on the account without emailing anyone, so it is
  safe to click repeatedly while getting the settings right. Sending a real
  test message is a separate, deliberate action.
- Secrets stay write-only: never returned by the API, never populated into the
  form, and the fields show "leave blank to keep existing" once one is stored.

**Verified in the running app** against a real database: the form saved, the
values persisted, the trailing slash typed into the tracking URL was stripped
by the schema validator, both secrets were stored encrypted as distinct
ciphertexts and decrypted back correctly, and the fields came back marked as
already set without exposing the values. TypeScript, ESLint and the production
build are all clean, and the backend suite still passes at 131.

## 2026-09-09 — Email campaign analytics: send and record

**Added:** everything needed to send a real campaign and record what happened
to it. Still backend-only; the Analytics tab UI is the next phase.

- **Contacts carry tags** (migration `702f63144e46`), and a campaign names one
  as its segment. Resolved at *send* time, not draft time, so someone who
  unsubscribed yesterday is not mailed by a campaign written last week.
- **Expansion and sending are separate, and both are idempotent.** Expansion
  skips contacts that already have a message row; the send loop skips messages
  that already have a `sent_at`, and commits per message. That is what makes a
  crashed worker safe to re-run — without it, a restart at the wrong moment
  mails the list twice.
- **Holdout and A/B assignment are deterministic**, derived from a hash of the
  campaign and contact ids with *different salts* for the two decisions.
  Random assignment would reshuffle the holdout on every resume and destroy
  the comparison it exists to provide; a shared hash would bias variant B
  toward one side of the holdout boundary.
- **The send worker is a systemd timer**, not an in-app scheduler
  (`backend/app/worker.py`, units in `deploy/ubuntu/`). It matches how this app
  is already deployed and logged. Overlapping runs are prevented by a Postgres
  advisory lock taken on its own connection — taken on the working session it
  would be released by the first per-message commit.
- **Queueing a send never sends inline.** A request that mails several hundred
  people would outlive the front proxy's 30 s timeout and leave nobody knowing
  how far it got.
- **The audience preview reconciles.** `eligible + suppressed +
  excluded_inactive + excluded_no_consent` always equals `total_contacts`, so
  an admin who queues to 300 and sees 240 sent can account for the other 60.
- **The footer is added by the renderer, not the author** — postal address and
  a working unsubscribe are legal requirements, so they cannot depend on
  someone remembering them. RFC 8058 one-click headers on every message.
- **Mailgun webhooks** at `POST /api/webhooks/mailgun`, signature-verified in
  constant time and **failing closed**: with no signing key configured, every
  event is rejected. Deduped on Mailgun's event id, because they retry until
  they get a 200. `failed` splits on severity — permanent suppresses, temporary
  does not.
- **Unsubscribe is live** at `/t/u/{token}`, both the one-click POST that Gmail
  and Yahoo call and the visible GET link. Root-mounted before the SPA
  catch-all, and with no rate limit: the front proxy forwards no client
  address, so a shared bucket would start refusing real unsubscribes.
- **Re-importing a list cannot resurrect anyone.** Unsubscribed and bounced
  contacts are left alone by an import, and a suppressed address cannot be
  reactivated through the contact edit endpoint either.
- **58 new tests** (131 total), plus an end-to-end pass against a real
  Postgres with a stub sender covering expansion, idempotency, holdouts,
  rendering, unsubscribe, webhook signature rejection, deduplication, bounce
  suppression and re-import safety.

**Fixed during verification:** the audience preview's exclusion counts
overlapped. Suppressing an address also flips the contact's status, so a
suppressed contact was filtered by the status gate before the suppression
check and appeared in neither bucket — the preview reported 12 contacts, 10
eligible and 1 excluded, which does not add up. The categories are now
mutually exclusive and exhaustive.

**New dependency:** `markdown` — campaign bodies are Markdown, rendered to
email-safe HTML at send time. Needs `pip install -r requirements.txt` on the
next dev-server update.

**Still open:** the open pixel, click redirect and tier classifier (phase 3),
the Analytics tab UI (phase 4), and a DB-backed pytest fixture — the
end-to-end verification above was run by hand, which remains the biggest
testing gap, as `docs/TESTING.md` already notes.

## 2026-09-09 — Email campaign analytics: foundation

**Added:** the data model and sending layer for the campaign analytics system
that will live under an Analytics tab in the admin backend. This phase is
backend-only and ships no UI; nothing in it changes existing behaviour.

- **Six tables** (migration `7f73b1434cf1`): `contacts`, `campaigns`,
  `campaign_messages`, `email_events`, `suppressions`, `sender_settings`.
- **Consent is per contact, not per list.** `Contact` carries country,
  consent basis and a *separate* tracking consent, because the rules differ by
  jurisdiction: the US allows opt-out, Canada requires consent before the
  first send, and April 2026 guidance from the French and Italian regulators
  treats per-recipient open tracking as needing its own consent. Two
  properties, `is_mailable` and `may_track_opens`, encode the rules so nobody
  has to remember them at send time. An unknown country is treated as the
  stricter rule.
- **Every event carries a reliability tier** (`exact` / `verified` /
  `inferred` / `derived`) as a column, not a caveat. Around half of all
  tracked opens industry-wide are Apple's automatic prefetch, and corporate
  scanners fetch every link within seconds of delivery; a dashboard that
  reports those as people is not measuring engagement.
- **A sender interface** (`services/senders/`) with two implementations.
  `MailgunSender` carries campaigns — Mailgun is already operated for the
  product's password and PIN email, so no new vendor, and its webhooks supply
  the delivery, bounce and complaint events raw SMTP cannot produce at all.
  `SmtpSender` reuses the existing SMTP credentials and is for internal test
  sends only (see its module docstring for why). The demo-reply path in
  `services/email_service.py` is untouched.
- **Campaigns must send from a different domain** from the product's
  transactional mail. `sender_settings` is a separate table from
  `smtp_settings` for the same reason: a campaign complaint spike must never
  land on the reputation that delivers a client's password reset.
- **Mailgun's own open and click tracking is explicitly disabled** on every
  send. It rewrites links onto a domain shared with its other customers, whose
  reputation we would inherit inside our own mail; tracking will be served
  from our own domain instead.
- **Suppression has no removal path.** Addresses are normalised on both write
  and read — the failure that prevents is a suppression stored for
  `bob@example.com` missing an import of `Bob@Example.com`, and mailing
  someone who pressed the spam button a second time.
- **Admin API:** `GET`/`PUT /api/admin/settings/sender` and
  `POST /api/admin/settings/sender/test`. The test endpoint verifies
  credentials *and* that the sending domain exists on the account without
  sending anything, and only mails a real address if one is supplied.
- **60 new tests** (73 total, up from 13), covering the consent rules, address
  normalisation, Mailgun webhook signature verification and the outbound form.

**Fixed before shipping:** the generated migration's `downgrade()` dropped the
tables but not the Postgres ENUM types — `sa.Enum` creates a type as a side
effect of `create_table`, and `drop_table` does not remove it. A downgrade
left eight orphaned types behind and the next upgrade died on
`type "consent_basis" already exists`. Caught by round-tripping the migration
down and back up before it shipped; `downgrade()` now drops the types
explicitly.

**Still open before this can send anything real:** the Mailgun sending domain
for campaigns does not exist yet (it must not be `mail.ashfordbriggs.com`,
which carries the product's password and PIN mail), and there is no UI, no
campaign expansion, no tracking endpoints and no webhook receiver. Those are
the next phases.

## 2026-09-09 — Dev server deployment + Ubuntu runbook + proxy-aware rate limits

**Retired (owner request):** the Railway display deployment. The `Paladin`
and `Postgres` services were deleted from the Railway project, puppyinfo.us
no longer serves anything, and the unused `railway.toml` was removed from the
repo. `docs/DEPLOY-RAILWAY.md` stays as history. The dev server
(devwww.ashfordbriggs.com) is now the only live copy of the site.

**Changed (owner decision, after BUG-007):** the demo-reply **sender address
is now configurable** in the admin Settings screen (`from_email`, migration
`d4a1c9e7b2f8`). It defaults to `info@ashfordbriggs.com` when blank, so
existing deployments behave as before. Reason: mail providers reject a From
address the authenticated account does not own, and the dev server's SMTP
account is not an ashfordbriggs.com mailbox. Regression tests cover the
fallback.

**Fixed (BUG-007, later that day):** the admin SMTP test on the dev server
ended in a 504 for a port-465 mail host. The Settings "Use TLS" switch only
ever meant STARTTLS, so port 465 got a plaintext connection that waited 30 s.
`smtp_tls_options()` now selects implicit TLS for 465 and STARTTLS otherwise,
the send timeout is 15 s so the real error beats the proxy timeout, and the
checkbox says what it does. Six regression tests. Live after deploy: the mail
host answers in ~1 s and rejects the fixed sender `info@ashfordbriggs.com`
because the configured account does not own it. Sending needs either an SMTP
account that owns that address or a decision to make the sender configurable.

**Documentation repo** for the partners: github.com/Vybecode-LTD/ashfordbriggs-docs
now carries a synced copy of `docs/` plus the `deploy/ubuntu` files under
`paladin-website/`. Source of truth stays here; `scripts/sync-docs.sh` (and the
`sync-docs` GitHub Action, once a `DOCS_REPO_TOKEN` secret exists) replaces
that folder wholesale. Added two partner-facing documents to `docs/`:
`OVERVIEW.md` (what the site is, environments, roles, stack, layout) and
`DEPLOY-RAILWAY.md` (the display deployment and its gotchas).

**Dev server follow-ups (2026-09-09, later):** the vhost is now `:80` only
(the expired-cert `:443` block was dropped), it logs every forwarded-address
header, and that log proved the front proxy sends none, so the app's per-IP
rate limits act as global caps there. Raised them in the dev `.env`
(60/min login, 60/hour demo, 200/hour AI) with the revert documented in
`DEPLOY-DEV-SERVER.md`.

**Deployed** the site to the company's shared dev server as
https://devwww.ashfordbriggs.com (details and update procedure in
`docs/DEPLOY-DEV-SERVER.md`). Manual path: Python 3.10 venv, systemd unit
running as a dedicated `paladin` user, own role/database on the existing
Postgres 14, Apache vhost reverse-proxying to 127.0.0.1:8000 behind a front
proxy that terminates TLS. Verified live: health, blog API, sitemap with the
devwww origin, all frontend routes, admin login, `X-Robots-Tag: noindex`.
Lesson recorded there: certbot cannot run on that box for devwww because the
front proxy answers the challenge; no certificate is needed locally.

Prepared the move from the Railway display deployment to a self-managed
Ubuntu server (pending partner approval).

**Added**
- `docs/DEPLOY-UBUNTU.md`: step-by-step runbook (server prep, Docker, code
  transfer, `.env`, launch, first login, backups/restore, updates, carrying
  content over from Railway, troubleshooting, a no-Docker appendix).
- `deploy/ubuntu/docker-compose.yml` (app + Postgres 17 + Caddy),
  `deploy/ubuntu/Caddyfile` (automatic HTTPS), `deploy/ubuntu/.env.example`
  (every variable with its generation command).
- CI job `deploy-image`: validates the compose file, builds the production
  image, boots it against Postgres and checks migrations ran, the seeded
  admin can log in, `/api/blog/posts` and `/` respond. This is the first
  automated end-to-end check of the deploy path.

**Fixed**
- CI `Backend` job had failed on every push since July: the `Run tests` step
  fires because `backend/tests/` exists, but pytest was never installed.
  Added `backend/requirements-dev.txt` (pytest) and install it in CI. The
  7 existing SVG-sanitizer tests pass.
- `Dockerfile`: uvicorn now runs with `--proxy-headers
  --forwarded-allow-ips='*'`. slowapi keys rate limits on
  `request.client.host`; behind Railway's edge (and behind Caddy on the VPS)
  that was the proxy's address, so the login (10/min) and demo-request
  (5/hour) limits were shared by every visitor. Applies to the Railway
  deployment as well.

## 2026-09-08 — First production deploy (Railway)

Redeployed the whole site into a fresh Railway project ("Ashford & Briggs")
and got it live on the generated Railway URL (since replaced — see the
2026-09-09 notes below).

**Changed**
- `railway.toml`: removed `startCommand` and `preDeployCommand`. The
  `startCommand` overrode the Dockerfile CMD, so `alembic upgrade head` never
  ran on Railway and every DB-backed route returned 500 with
  `relation "blog_posts" does not exist`; `preDeployCommand` was ignored by
  Railway entirely (service manifest showed `null`). The Dockerfile CMD is
  now the single start path on any Docker host.
- `Dockerfile`: CMD now runs migrations, then `python -m seed` only when
  `SEED_ADMIN_PASSWORD` is set (idempotent — skips an existing user), then
  uvicorn. Needed because Railway project tokens cannot `railway ssh` to run
  the seed as a one-off.

**Infra (Railway, not in git)**
- Postgres plugin added; `DATABASE_URL` referenced as
  `${{Postgres.DATABASE_URL}}`.
- Fresh production `JWT_SECRET_KEY` and `ENCRYPTION_KEY`; `ANTHROPIC_API_KEY`,
  `ANTHROPIC_MODEL`, `CORS_ORIGINS`, `SITE_URL`, `DEBUG=false` set on the
  `Paladin` service. A stale service-level `startCommand` was cleared via
  the API so the Dockerfile CMD applies.
- All three Alembic migrations applied; first admin created; seed variables
  removed afterwards.
- Verified live: `/`, `/blog`, `/api/blog/posts` (200 `[]`), `/sitemap.xml`
  (200, correct origin), admin login and authenticated admin routes (200).
- 2026-09-09: deleted the stray `frontend` and `backend` services (wrong
  build setup for this monorepo, failed on every push). Note: the GraphQL
  `serviceDelete` mutation is *not* authorized for a project token, but
  `railway service delete --service <name> --yes` (CLI ≥ 5.4x) is.
- 2026-09-09: owner attached **puppyinfo.us** as a temporary display domain
  and set `SITE_URL` / `CORS_ORIGINS` to it (the generated Railway domain was
  regenerated to `paladin-production-c90f`). Verified: sitemap emits
  puppyinfo.us URLs, CORS preflight allows the origin, all routes 200. The
  ashfordbriggs.com references in the frontend are intentionally untouched —
  that is the eventual production domain.

## 2026-07-07 — Blog editor completeness pass + deploy handoff docs

Verified the admin blog editor against a checklist (AI assistant, editing
published posts, image handling, formatting, unpublish/delete) rather than
assuming it was all there. Found and fixed two real gaps.

**Added**
- **Unpublish button** in `PostEditor.tsx` (`frontend/src/pages/admin/PostEditor.tsx`) —
  shown only for already-published posts, confirms before acting, PATCHes
  `status` back to `draft`. The backend already supported this transition;
  there was simply no UI control for it before now.
- **Insert image button** with caption support — a new "Insert image" button
  in the editor prompts for a URL and an optional caption, inserting
  `![alt](url "caption")` at the cursor. A new shared `MarkdownImage`
  component (`frontend/src/components/MarkdownImage.tsx`) renders that
  Markdown "title" as a real `<figure>/<figcaption>` instead of a native
  tooltip — wired into both the editor's Preview tab and the public
  `BlogPost.tsx` page, so captions render identically in both places.
- Relabeled the existing draft-save button to "Save changes" when editing an
  already-published post (it was ambiguously always labeled "Save draft"
  even when it wouldn't actually change status).
- A prominent handoff section at the top of `CLAUDE.md` instructing the next
  Claude session to stop and ask the new maintainer about their actual
  deployment environment (host, domain, DB, Docker availability, secrets)
  before doing any deploy work — this repo is being handed off for
  self-hosting on someone else's server.

**Verified**
- Confirmed the AI assistant (draft/titles/excerpt/SEO), editing an
  already-published post, and delete all already worked correctly.
- Live-tested the new Unpublish button against the real published post:
  backend status flips to `draft`, `published_at` is preserved, the button
  set correctly changes from Save/Unpublish/Update back to Save/Publish.
  Live-tested Insert image: prompts fire, Markdown is inserted at the cursor,
  Preview renders a real `<figure>/<figcaption>`. Restored the test post to
  its original published state and content afterward.
- `npx tsc --noEmit`, `npm run build`, and `npm run lint` all clean.

---

## 2026-07-07 (later) — UX/SEO sweep confirmed + follow-up fixes

The UX/SEO/accessibility pass referenced as "in progress" in the entry below
completed and was committed (`913d0f1`), alongside the security-hardening
commit (`575a9ec`). Four follow-up items from that pass's own review notes:

**Added**
- `GET /sitemap.xml` (`backend/app/routers/sitemap.py`) — generated at request
  time from the DB, so every published blog post is included, not just the
  static marketing routes. Registered at the site root (no `/api` prefix),
  ahead of the SPA catch-all so it wins over the static copy Vite copies from
  `frontend/public/sitemap.xml` in a production build. New `SITE_URL` setting
  (`backend/app/core/config.py`, `.env.example`) drives the absolute URLs —
  change it when deploying under a different domain.
- `max_length` caps on `DemoRequestCreate` (`backend/app/schemas/demo.py`),
  mirrored exactly from the `DemoRequest` DB column limits, so an oversized
  field is a clean 422 instead of a raw `StringDataRightTruncationError` 500
  (confirmed this was a real gap: a 250-char `full_name` previously reached
  the DB and crashed before hitting any length check).

**Fixed**
- `npm audit` in `frontend/`: bumped `vite` 5.4.21 → 6.4.3, resolving the
  moderate/high `esbuild` dev-server advisory. Deliberately did *not* take
  `npm audit fix --force`'s suggested jump straight to `vite@8` — v6 already
  pulls in the patched `esbuild` (`^0.25.0`) with much less breaking-change
  risk. Build, lint, and the dev server proxy all reverified clean afterward.
- Root `CLAUDE.md` was stale — still described the original scaffold as the
  current state and listed the Alembic migration and OG images as pending
  (both were already done). Refreshed to reflect actual current state and
  generalized the deploy section: this project is being handed off to be
  self-hosted on someone else's own server, so the Dockerfile/deploy notes
  are no longer framed as Railway-only.

**Verified**
- `/sitemap.xml` live-checked: includes the one published post with a
  `<lastmod>` tag, static marketing routes still present.
- Oversized-field demo-request live-checked: 422 with a clean Pydantic
  `string_too_long` error, not a 500.
- `npm audit`: 0 vulnerabilities. `npm run build`, `npm run lint`, and a fresh
  `vite` dev server all confirmed working post-bump.

---

## 2026-07-07 — Security hardening pass

Backend security-hardening batch, verified live against the running dev server.
Not yet committed to git (working tree has uncommitted changes to the files
listed below).

**Added**
- Rate limiting via `slowapi`: login endpoint limited to 10/min, demo-request
  submission limited to 5/hour. Wired through `backend/app/core/ratelimit.py`
  (a `Limiter` keyed by remote address) and registered in `backend/app/main.py`
  (`app.state.limiter`, `RateLimitExceeded` handler, `SlowAPIMiddleware`).
- Password length validation (8-128 chars) in `backend/app/schemas/auth.py`.
- Self-service password-change endpoint: `PATCH /api/auth/me/password`.
- Admin user-management endpoint: `PATCH /api/auth/users/{user_id}`.
- `max_length` caps on AI request schemas (`backend/app/schemas/ai.py`) to
  guard against unbounded prompt payloads to the Anthropic proxy.
- `AIServiceError` exception type in `backend/app/services/anthropic_service.py`,
  raised on Anthropic API failure and caught in `backend/app/routers/ai.py` to
  return a clean 502 instead of an unhandled 500.

**Fixed**
- Three unguarded `uuid.UUID()` calls that crashed with a raw unhandled 500 on
  malformed IDs, now returning clean 404/401:
  - `backend/app/middleware/auth.py` (`get_current_user`)
  - `backend/app/routers/auth.py` (`refresh`)
  - `backend/app/routers/blog_admin.py` (`_load_owned`, `admin_delete`)
  - See `docs/BUGS.md` BUG-001/002/003 for root cause and verification detail.
- `backend/.env.example` now defaults `DEBUG=false` instead of `DEBUG=true`
  (was shipping an insecure default for anyone copying the example file).

**Verified**
- Rate limiter confirmed live: 6th demo-request submission within an hour from
  the same client returns 429.
- Malformed UUIDs confirmed live: crafted bad-UUID inputs against all three
  fixed call sites return 404/401, not 500.
- Short passwords confirmed live: sub-8-character passwords rejected with 422.
- See `docs/TESTING.md` for full detail on how these were checked (manual
  curl-based verification against the local dev server — no automated test
  suite exists yet).

**Also this date (in progress, separate parallel effort — not part of this
entry's scope):** a UX/SEO/accessibility polish pass covering per-page SEO meta
tags, `robots.txt`/`sitemap.xml`/JSON-LD, a frontend 404 route, admin
sidebar/grid responsive CSS, click-to-copy in the admin post list, frontend
access-token refresh, Contact/How It Works content-parity fixes, and a GitHub
Actions CI pipeline. Not reflected as complete here — see `docs/ROADMAP.md`
phase 3 for status.

---

## 2026-07-06 (approx.) — Initial scaffold

Full project scaffold, built and verified compiling/rendering.

**Added**
- Backend: FastAPI app factory, async SQLAlchemy 2 (asyncpg) models (user,
  blog, demo_request), Alembic wiring, JWT + bcrypt auth
  (`backend/app/core/security.py`), RBAC middleware (`require_role`), routers
  for health/auth/blog (public + admin)/ai/demo, `anthropic_service.py` as a
  server-side proxy for AI blog generation, `seed.py` to create the first admin.
- Frontend: React 18 + Vite + TypeScript app. Five marketing pages (Home,
  Product, HowItWorks, About, Contact), blog reader (index + post), and a full
  admin surface (Login, Dashboard, PostList, DemoInbox, AI-assisted PostEditor).
  Dark-theme design system in `frontend/src/styles/tokens.css`.
- Docs: original single-page copy frozen verbatim in `docs/original-snapshot/`
  as a revert point; expanded/sharpened marketing copy drafted in
  `docs/content/` alongside a `SITEMAP.md`.
- Deploy scaffolding: `Dockerfile` + `railway.toml` for a single-service Railway
  deploy (FastAPI serves the built frontend as static files).

**Verified**
- Every backend Python file compiles clean (`python -m py_compile`).
- `__pycache__` cleaned before commit. 69 files total in the initial scaffold.

**Not done yet at this point:** dependencies not installed, `.env` not created,
no admin seeded, no live request against either server, no migration generated
(dev mode relies on lifespan auto-create-tables), no images/OG assets wired, not
deployed.
