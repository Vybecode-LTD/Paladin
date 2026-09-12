# Email campaign analytics

The admin backend's **Analytics** tab: sending campaigns to a consented contact
list, and measuring what happened to them honestly.

This document explains what the system does and how it is built. For the setup
work that only an owner can do — Mailgun, DNS, the sending domain — see
`EMAIL-SETUP-RUNBOOK.md`.

## The problem it solves, and the one that shapes everything

Email marketing tools report an "open rate" as though it were a fact. It is not.
Roughly **half of all tracked opens industry-wide are machines**, not people:
Apple Mail Privacy Protection fetches every image in every message before the
recipient sees it, Gmail proxies and caches images, and corporate security
gateways click every link in a message to check it for malware. A tool that
reports those as engagement is not measuring interest; it is measuring
infrastructure.

Rather than pick a number and hope, this system **labels every figure with how
much it can be trusted**. That is the central design decision, and it is visible
in the database, the API and the UI.

| Tier | Means | Examples |
|---|---|---|
| `exact` | A mail system told us, as a fact about delivery | delivered, hard/soft bounced, complained (spam button), unsubscribed |
| `verified` | A person did something a machine cannot plausibly fake | replied, confirmed on a landing page, converted |
| `inferred` | Real, but machines produce this signal too | opened, clicked |
| `derived` | Computed from the above | rates, A/B verdicts, best-time recommendations |

Nothing in the UI shows a bare "open rate". Opens and clicks are split between
what is probably a machine and what might be a person, and the split is always
shown. **A reply is worth more than a hundred opens**, and the system is built
to say so. Replies are not captured yet, though: the scoring and the
scorecard are in place, but nothing records a reply, so that figure stays at zero
until reply capture is built (see "Not built yet" below).

## Machine detection

`app/services/classifier.py` decides which side of that split an event falls on.
It is deliberately conservative — when it cannot tell, it does not claim a human.

- **Known machine user agents:** `GoogleImageProxy`, `ms-office`, `BingPreview`,
  security-scanner strings, and Apple MPP — which is detected by shape rather
  than name, because MPP presents a WebKit user agent with the `Safari`,
  `Version` and `Chrome` tokens stripped out.
- **Scanner referers:** links arriving via `urldefense.proofpoint.com`,
  `safelinks.protection.outlook.com`, `linkprotect.cudasvc.com` and
  `protect-us.mimecast.com` are gateway rewrites, not human clicks.
- **The prefetch window:** an open within **10 seconds** of the message being
  sent is a prefetch. Nobody reads that fast.
- **Sweep detection:** **3 or more distinct links** from one message inside
  **30 seconds** is a gateway walking the message, not a person reading it.

## What it does

**Contacts and consent.** Every contact carries a `consent_basis` (express,
implied, contract, signup, demo request, or unknown) and a status. A contact
with `unknown` consent is never mailable — the system refuses rather than
assuming. `may_track_opens` gates open tracking separately from mailability.

**Suppression.** Unsubscribes, complaints and hard bounces go to a suppression
list that is consulted before every send. **There is deliberately no code path
that removes an address from it.** Re-adding someone who asked to be left alone
should require a human decision and a database write, not a button.

**Campaigns.** Draft, schedule, send. Optional A/B variants and a holdout group,
assigned by salted hash so the same contact always lands in the same bucket.

**Sending.** A `Sender` protocol with two implementations — Mailgun (the real
path, which reports delivery events) and SMTP (a fallback that structurally
cannot report them). Sending is claimed with `FOR UPDATE SKIP LOCKED` so two
workers can never send the same message twice. Mailgun's own open and click
tracking is switched off on every message, because its version rewrites links onto
a domain it shares with its other customers.

**Tracking.** An open pixel, click redirects, a landing-page beacon, and a
one-click unsubscribe honouring `List-Unsubscribe` / `List-Unsubscribe-Post`.
These routes are mounted at the **root**, not under `/api`, so they work on any
hostname pointed at the app.

**Statistics.** A two-proportion z-test (implemented with `math.erf` — no scipy
dependency) decides whether an A/B difference is real. Below the sample-size
threshold it **refuses to give a verdict** rather than reporting noise as a
winner.

**Domain trust.** DMARC report ingestion, blocklist checks over plain DNS, seed
inbox placement over IMAP, and a pre-flight check that blocks a broken campaign
before it goes out. See "Trust" below.

## Architecture

```
frontend/src/pages/admin/analytics/   Overview, Campaigns, CampaignEditor,
                                      CampaignDetail, Contacts, Trust
backend/app/routers/
  sender_settings.py    provider credentials (encrypted at rest)
  contacts_admin.py     import, list, consent
  campaigns_admin.py    draft/schedule/send, audience breakdown
  analytics_admin.py    scorecards, overview, send-time recommendation
  trust_admin.py        DMARC, blocklists, seed inboxes, pre-flight
  webhooks.py           Mailgun delivery events (HMAC-verified)
  tracking.py           ROOT-mounted: /t/o, /t/c, /t/b, /t/u
  attribution.py        landing-page beacon + product conversion events
backend/app/services/
  senders/              base protocol, mailgun_sender, smtp_sender
  campaign_service      audience, variants, expansion, sending
  classifier            machine vs human
  event_service         classification + idempotent recording
  render_service        personalisation, link extraction, unsubscribe URLs
  stats_service         significance testing, scorecards
  dmarc_service, blocklist_service, seed_service, preflight_service, trust_service
backend/app/worker.py   systemd-timer driven: sends due campaigns, runs trust checks
```

**Router order matters.** `tracking.router` must be registered *before* the SPA
catch-all in `app/main.py`, or the React app swallows the tracking URLs.

**Idempotency.** Every event carries a `dedupe_key` under a unique constraint,
recorded inside a savepoint. Mailgun retries webhooks; a retried delivery must
not become two delivery events.

**The worker** takes a Postgres advisory lock (`84712026`) on its own connection
so overlapping timer firings cannot double-send. It also runs the daily trust
checks, rate-limited by when each check last actually ran rather than by a
second timer unit.

## Trust

- **DMARC reports** are parsed from the gzip, zip or bare XML that providers
  send. Alignment is read from `policy_evaluated`, **not** from raw auth
  results — a forged message can show DKIM "pass" for the forger's own domain,
  and reading the raw result would report an attacker as a healthy sender.
- **The panel's verdict is whether it is safe to tighten the domain policy.** It
  refuses while any source is still failing, because enforcing before the
  failing sources are identified is how a company silently stops receiving its
  own mail.
- **Blocklist checks** run over plain DNS with no account or key. A Spamhaus
  refusal — which is what a public resolver gets — is reported as *an error*,
  not as a listing, so a resolver problem never shows up as a reputation problem.
- **Seed inboxes** check real placement, including Gmail's Promotions tab (not a
  folder — it needs Gmail's own search extension to detect). "Could not check"
  is a distinct result from "never arrived", and only the latter is stored. Two limits: the checker
  signs in over IMAP with an app password, which Gmail allows and Microsoft no
  longer does, so Outlook and Microsoft 365 seeds will fail; and it looks for every
  recent campaign in every seed inbox, so each seed has to be in every campaign's
  audience or it reports "never arrived".
- **Pre-flight** enforces four blockers at send time: no sender configured, no
  From address, no tracking URL, no postal address. Everything else is a warning
  or a note — a checker that blocks on style is one people learn to work around.

## Secrets

`ENCRYPTION_KEY` (Fernet) protects the sender credentials at rest. Mailgun needs
**two different credentials** and they are easy to confuse: the **API key** for
sending, and the **HTTP webhook signing key** for verifying inbound events. The
webhook verifier fails closed — with no signing key configured it rejects
everything rather than trusting unverified input. Use the account's API key:
the settings screen's connection check reads the domain's details, which a
sending-only key cannot, so switching to one needs that check changed first.

## Deliberately not built, and not built yet

- **Google Postmaster Tools API** — needs a service account and domain-wide
  delegation, and shows no data below roughly a few hundred Gmail messages a
  day. It would be an OAuth integration displaying an empty panel at this
  volume. DMARC reports and seed inboxes answer the same questions and work now.
- **SpamAssassin** — running its daemon on a shared box serving three other
  sites is not a reasonable trade for a checkable short list of rules.
- **Removing addresses from the suppression list** — see above; intentional.

Not built yet:

- **Reply capture.** A reply is meant to be a `verified` signal, but nothing
  records one. With the *Reply domain* setting filled in, replies are addressed to
  `replies+<token>@<domain>` and go nowhere, so it must stay blank until an inbound
  handler exists; when it is blank, replies go to the From address. See BUG-008 and
  runbook step G5.
- **Loading past opt-outs.** There is no endpoint or screen for importing an existing
  suppression list, so it has to be done as a one-off before the first real send
  (runbook F1).
- **Screens for seed inboxes and contact import.** Both are API calls for now:
  `POST /api/admin/trust/seed-inboxes` and `POST /api/admin/contacts/import`.

## Tests

279 backend tests, the bulk of them on the parts where being wrong is expensive:
77 on the machine classifier alone, plus the Mailgun event mapping, consent
gates, link rewriting, significance testing, the DMARC parser and pre-flight.
See `TESTING.md`.
