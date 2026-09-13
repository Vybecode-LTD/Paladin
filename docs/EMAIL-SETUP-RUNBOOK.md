# Email analytics — setup runbook

The ordered path from today's build to the first real campaign, a production
launch and a locked-down domain. Every step says who does it, what it waits on,
and how to check it worked. Written for Matt and John, and for the developer.

Step codes (A1, C2, …) match the interactive runbook the developer works from,
so a code means the same thing in both. Codes like `NET-01` refer to the setup
questions sent by email.

Rebuilt on **2026-09-12** against live DNS, the dev server and the code. It
replaces the 2026-09-09 version; the corrections are listed at the end.

For what the system does and how it is built, see `EMAIL-ANALYTICS.md`.

## What the network looks like

Two different machines serve `ashfordbriggs.com` names, and telling them apart is
the key to every DNS decision below.

| Name | Resolves to | What is there |
|---|---|---|
| `ashfordbriggs.com` | 89.187.170.160 | nginx 1.24. The public website. Certificate covers `ashfordbriggs.com` and `www.` **only**. |
| anything else `*.ashfordbriggs.com` | 89.187.170.160 | The same nginx, via a **wildcard** record. It answers for any name, but its certificate does not, so HTTPS fails the name check. |
| `devwww.ashfordbriggs.com` | 104.48.125.58 | An **explicit exception** to the wildcard. The AT&T line in Jacksonville → front proxy → Apache on 10.0.0.80 → Paladin on 127.0.0.1:8000. Certificate covers `devwww` only. |

Existing mail and DNS, verified 2026-09-12. Setting up campaigns changes none of
these:

```
MX   ashfordbriggs.com               smtp.google.com   (Google Workspace)
TXT  ashfordbriggs.com               v=spf1 include:_spf.google.com ~all
TXT  _dmarc.ashfordbriggs.com        v=DMARC1; p=none; rua=mailto:dmarc@ashfordbriggs.com; fo=1
TXT  _dmarc.mail.ashfordbriggs.com   v=DMARC1; p=none; rua=mailto:dmarc@ashfordbriggs.com; fo=1
NS   ashfordbriggs.com               dns1.registrar-servers.com, dns2.registrar-servers.com (Namecheap)
```

There is already a Mailgun sending domain, **`mail.ashfordbriggs.com`**, used by
the product to send clients their passwords and PIN codes. It signs with a
1024-bit DKIM key. Nothing here should disturb it, and step H1 exists
specifically to not disturb it.

## Already done

- The analytics system is built (five phases, 279 backend tests) and running on
  the dev server, with the send worker installed.
- `dmarc@ashfordbriggs.com` is live (John, 2026-09-12), and both DMARC records
  send their reports to it.
- The DNS host is confirmed as Namecheap.

## The one rule: real campaigns go out from production

Every email carries links to the tracking hostname — the open pixel, every link,
the unsubscribe — written into the message when it is sent and impossible to
change afterwards. US anti-spam law (CAN-SPAM) requires the unsubscribe to keep
working for at least 30 days, and people click old emails for months. Mail sent
from dev would point all of that at dev's database, which production will not
have.

So dev only rehearses, with internal addresses, using
`https://devwww.ashfordbriggs.com` as its tracking URL: it already has working
HTTPS and needs no new DNS or certificate. `links.ashfordbriggs.com` is set up
once, for production.

If a real campaign truly cannot wait, point `links.` at dev and use it (never
`devwww`) in that campaign, then move dev's whole database to production when it
launches, so every link still resolves.

## Nine mistakes nothing will warn you about

| Mistake | What happens | See |
|---|---|---|
| A real campaign sent from dev | Tracking and unsubscribe links in delivered mail break when production takes over. | The rule |
| The tracking URL set to `updates.` | Once Mailgun's records publish, the wildcard stops answering for that name and every link on it stops resolving. | C2, D1 |
| The Reply domain setting filled in | Replies go to an address nothing reads, so people's answers disappear. | C4 |
| A wrong webhook signing key | The dashboard shows sends and nothing after: no deliveries, bounces or complaints. | C3 |
| `dmarc@` refusing outside mail | The reports never arrive, and nothing says so. | A1 |
| No send worker running | Campaigns schedule normally and never go out. | E2 |
| Contacts loaded before past opt-outs | The first send reaches people who already asked not to be emailed. | F1 |
| A proxy that hides visitor addresses | Rate limits become one global cap, and scanner detection loses its best clue. | E3 |
| The old DKIM key removed too early | Clients quietly stop receiving their password and PIN emails. | H1 |

The wildcard behaviour is demonstrable on this zone: `_dmarc.ashfordbriggs.com`
holds a TXT record and returns nothing for an A lookup, while an invented name
still resolves to 89.187.170.160. A wildcard only answers for names that have no
records of any type (RFC 4592).

---

## A. Right now

**Starts when:** now. None of this needs an answer from anyone.

### A1. Check that `dmarc@` accepts mail from outside the company
**Who:** the developer (group owner)

The reports come from Google, Microsoft, Yahoo and others. A group that only
accepts internal mail discards every one of them silently, and a test email sent
from inside the company proves nothing about that.

1. Open groups.google.com and select the dmarc group.
2. **Group settings → Who can post** must allow anyone to post ("Anyone on the
   web").
3. If that option is not offered, outside mail to groups is off for the whole
   organization; a Workspace admin allows it in the Admin console.
4. Note the spam handling on the same screen. After a few days, check the
   group's pending messages for held reports: automated mail with `.zip` or
   `.gz` attachments is exactly what group spam filters tend to hold.

**How to know it worked:** within one to three days, reports arrive from Google
(`noreply-dmarc-support@google.com`) and Microsoft. A few may still reach the old
address in that window, because providers cache DMARC records.

### A2. Answer the setup questions
**Who:** John and Matt

Phase B depends on them. They were sent by email, each with a code such as
`LST-02`, so answers can come back inline.

### A3. Load the first DMARC reports into the Trust panel
**Who:** the developer · **Waits on:** A1

Shows who sends mail as ashfordbriggs.com today. Anything unrecognised is either
a forgotten tool or someone forging the domain, and it matters which before
tightening anything.

1. Save the `.zip` or `.gz` attachments from the reports.
2. Admin → Analytics → **Domain trust** → upload them. The dev server is fine for
   this: it is analysis, not campaign data.
3. Repeat weekly until collection is automated (G1).

### A4. Review and merge PR #1
**Who:** the developer

The analytics system still lives on the feature branch, and production installs
from `main`. The tests must pass first:

```bash
cd backend && python -m pytest
```

### A5. Change the dev server account's password
**Who:** Matt

Once setup work on the box is finished. Deploys use an SSH key, so changing it
breaks nothing.

### A6. Confirm 2-step verification is enforced for everyone
**Who:** John

A stolen Workspace login is the most common way a well-configured domain starts
sending spam. Admin console → Security → Authentication → 2-Step Verification.
When enforcing it, set a start date so people can enroll first and nobody gets
locked out.

---

## B. Decisions

**Starts when:** the setup questions are answered.

### B1. Choose how `links.ashfordbriggs.com` reaches production
**Who:** Matt · **Questions:** NET-01 … NET-05

The last open architectural question. This name never gets a mail record, so any
of these routes is safe from the wildcard trap.

| If production… | Do this |
|---|---|
| has its own fixed public IP and handles its own HTTPS | One A record, `links` → production's IP, and a certificate on production. The simplest route. |
| sits behind the office front proxy, like dev | An A record to the office line (only if that IP is fixed, NET-05), `links.` added to the front proxy's certificate, and forwarding to production. |
| must sit behind the nginx web host (89.187.170.160) | A server block and certificate there, proxying to production. The wildcard already covers the name, so no DNS change, but that host has to reach production (tested in E3). |

### B2. Mailgun access, region and limits
**Who:** Matt · **Questions:** MG-01 … MG-04

Region sets the API host (US or EU), and a key from one returns a confusing
authorisation error against the other; the existing `mail.ashfordbriggs.com`
domain's page shows it. MG-04 confirms exactly what that domain carries before
anything goes near it.

### B3. Who publishes DNS records at Namecheap
**Who:** Matt · **Questions:** DNS-02, DNS-03

Server access does not come with DNS access, and the Mailgun records in C2 are on
the critical path. A wrong record here can stop the whole company's mail, not just
campaigns, so name one person to own DNS changes, with the developer as second,
and write every change down before it is made.

### B4. The sending identity, and where replies go
**Who:** John · **Questions:** ID-01 … ID-04, GW-05

- **From name and address.** Chosen once and never varied, because consistency is
  itself a reputation signal. A founder's name reads better than a company name on
  a warm list.
- **Where replies land, and who answers them within a day.** Replies come back to
  the From address. A From address on `updates.` needs replies forwarded (C4); one
  on a Google Workspace mailbox receives them directly.
- **A postal address for the footer.** The office, a registered agent or a PO box
  all qualify; pre-flight will not send without one.
- **Approval** of `updates.` for sending and `links.` for tracking, and the From
  address the product's own emails use (GW-05), so campaign mail never collides
  with it.

### B5. The contact list
**Who:** John · **Questions:** LST-01 … LST-05

- Email, name, company and country per person. The country decides whether the
  open pixel is embedded.
- A consent basis for each contact: a contract, a signup, a demo request or
  explicit permission. One note per group is fine if it is true for everyone in
  it. Unknown consent is never mailed.
- The record of past unsubscribes, complaints and bounces, which is loaded before
  anything else (F1).

### B6. Sign-off, cadence and data retention
**Who:** John · **Questions:** POL-01 … POL-03

- Who approves content before it goes out.
- How often you will send: weekly at most to start, since a new sending domain has
  to build its reputation.
- How long to keep engagement data. Two years is the recommendation; suppressions
  are kept permanently regardless.

### B7. The production server
**Who:** Matt · **Questions:** SRV-01 … SRV-03

When it is ready, what it runs, whether Docker is available (which picks the
install path in E2), and how the developer gets access.

### B8. A real mailbox inside the DMARC group
**Who:** John

A Google Group has no inbox that software can sign into. Automatic report
collection needs one member of `dmarc@` that is a real mailbox, most likely a
dedicated Workspace account (one license). Until then, reports are uploaded by
hand.

---

## C. The Mailgun sending domain

**Starts when:** B2, B3 and B4 are answered. Nothing here touches the website or
the client password emails.

### C1. Add `updates.ashfordbriggs.com` to Mailgun
**Who:** Matt

Campaigns get their own domain, so a complaint spike on a campaign never lands on
the reputation that delivers a client's password reset.

1. Mailgun → Sending → Domains → Add new domain: `updates.ashfordbriggs.com`, in
   the region from B2.
2. If Mailgun offers a DKIM key length, choose 2048-bit.
3. Copy every DNS record it shows before leaving the page.
4. Ignore its open and click tracking settings. Paladin switches Mailgun's
   tracking off on every message, because Mailgun's version rewrites links onto a
   domain it shares with its other customers.

**How to know it worked:** the domain is listed as unverified. It stays that way
until C2 is published.

### C2. Publish the records at Namecheap, in one sitting
**Who:** Matt · **Waits on:** C1

This subdomain carries mail only. Putting any record on a name switches off the
wildcard's answer for it, which is intended here: nothing web-facing uses
`updates.`.

Namecheap → Domain List → Manage → Advanced DNS. Namecheap adds the domain itself,
so type the host exactly as shown:

| Type | Host | Value |
|---|---|---|
| TXT | `updates` | `v=spf1 include:mailgun.org ~all` |
| TXT | `<selector>._domainkey.updates` | the DKIM value from Mailgun, copied in full |
| TXT | `_dmarc.updates` | `v=DMARC1; p=reject; rua=mailto:dmarc@ashfordbriggs.com` |
| MX | `updates` | the two receiving records Mailgun shows (mxa and mxb), so replies can reach C4's forwarding. Skip only if B4 put the From address on a Google Workspace mailbox. |

- **No A record for `updates`.** Sending does not need one.
- The DKIM value is long. A truncated copy is the usual reason a domain never
  verifies.
- Skip Mailgun's `email.updates` tracking record: Paladin serves its own.
- `p=reject` is safe on this name from day one. Only Mailgun will ever send from
  it, so there are no older senders to break.

**How to know it worked:**

```bash
nslookup -type=TXT updates.ashfordbriggs.com
```

```bash
nslookup -type=TXT _dmarc.updates.ashfordbriggs.com
```

The first shows the SPF record, the second the DMARC record. Then press **Verify
DNS settings** in Mailgun.

### C3. Enter the Mailgun credentials — on a call, never by email
**Who:** Matt and the developer · **Waits on:** C1 · Done once per environment:
dev in D1, production in E5.

Credentials are encrypted with each environment's own key, so they cannot be
copied from one database to another.

1. Admin → Settings → **Campaign sending**: provider Mailgun, the region, sending
   domain `updates.ashfordbriggs.com`.
2. Paste the API key. Use the account's main key for now: the connection check
   also reads the domain's details, which a sending-only key cannot do (G3 changes
   that).
3. Paste the **HTTP webhook signing key** from Mailgun's Settings → API Keys page.
   It is a different credential, and putting the API key in this field is the most
   common mistake in the whole setup.
4. Leave **Reply domain** blank (C4).
5. Under **Check the connection**, run the check. It verifies the key and confirms
   the domain exists on the account without emailing anyone, so it is safe to run
   repeatedly.

**How to know it worked:** the check passes. A "no domain" error means the region
or the domain name is wrong.

### C4. Forward replies to a person
**Who:** Matt · **Waits on:** C2 (the MX records)

Nothing in Paladin records replies yet (BUG-008). If the Reply domain setting is
filled in, every reply goes to a machine address that nothing reads. Until reply
capture is built (G5), replies go straight to someone who answers them.

1. Mailgun → Receiving → Routes → Create route. Match recipient
   `.*@updates.ashfordbriggs.com`, and forward to the inbox or group from B4 that
   someone reads daily.
2. Keep **Reply domain** blank, so replies go to the From address and through this
   route. Servers deployed before 2026-09-12 show help text on that field claiming
   replies are matched; they are not.

If B4 put the From address on a Google Workspace mailbox, skip this step and the MX
records in C2: replies already land in that mailbox.

**How to know it worked:** in D4, a reply arrives at the forwarding inbox.

---

## D. Rehearsal on dev

**Starts when:** phase C is done. Internal addresses only, per the rule.

### D1. Point dev's campaign settings at itself
**Who:** the developer · **Waits on:** C3 (on dev)

Admin → Settings → Campaign sending:

- From name and address from B4, or a team address until that is decided.
- Postal address from B4. Pre-flight will not send without it.
- Tracking URL: `https://devwww.ashfordbriggs.com`. It works today with no DNS or
  certificate changes.
- Reply domain: blank.

Servers deployed before 2026-09-12 show `https://updates.ashfordbriggs.com` as the
tracking URL example. Do not use it: it is the one value that breaks every link
once C2 is published.

### D2. Point Mailgun's webhooks at dev, for now
**Who:** Matt · **Waits on:** D1 (the webhook URL is built from the tracking URL)

1. Copy the address shown under **Webhook URL** on the Campaign sending screen
   (`https://devwww.ashfordbriggs.com/api/webhooks/mailgun`).
2. Mailgun → Sending → Webhooks → select `updates.ashfordbriggs.com`.
3. Add that URL for Delivered, Permanent Failure, Temporary Failure, Complained and
   Unsubscribed.
4. Use Mailgun's own Test button.

**How to know it worked:** the test returns 200. A 403 means the signing key in
Settings is wrong or missing, which is exactly what it should do.

### D3. Build an internal test list, with seed inboxes
**Who:** the developer

- The founders plus three to six addresses the team controls: at least one Gmail,
  one Microsoft (Outlook.com or Microsoft 365), a Yahoo if possible, and a team
  inbox.
- Load them through the contacts import endpoint (`POST /api/admin/contacts/import`)
  with consent basis `express`, tagged `internal`. There is no import screen yet.
- **Seed inboxes** show where a campaign landed — inbox, spam or Promotions —
  before a client mentions it. Create company-owned Gmail accounts with a company
  address as recovery, so they outlive any individual; turn on 2-step verification
  and generate an app password for each; then add them with
  `POST /api/admin/trust/seed-inboxes` (`label`, `email`, `provider` "gmail",
  `password`). There is no screen for this either.
- The checker also has an Outlook setting, but Microsoft now requires modern
  sign-in for IMAP, which the checker does not do. Expect it to fail, and check
  Microsoft inboxes by eye.
- **Seeds belong in every audience.** The checker looks for every recent campaign
  in every seed inbox and reports "Never arrived" for a campaign a seed was never
  sent. Import each seed address as a contact and include it in every send.

### D4. Send the rehearsal and check every signal
**Who:** the developer · **Waits on:** C4, D1, D2 and D3

1. Analytics → Campaigns → New campaign. Write it in Markdown, with one link to a
   page on the site itself. The postal address and unsubscribe link are added
   automatically.
2. Use **Send a test** to read it on a phone and a laptop. That checks how it looks,
   not the tracking: test sends use a preview link token, so opens, clicks and
   unsubscribes from them are not recorded.
3. Check the audience panel reconciles, clear pre-flight, then **Send the
   campaign** to the `internal` tag. The worker picks it up within a minute.

Then check, in order:

1. Where it landed in each inbox: inbox, spam or Promotions.
2. In Gmail, **Show original**: SPF, DKIM and DMARC all PASS, with DKIM signed by
   `updates.ashfordbriggs.com`.
3. On the campaign page, deliveries appear within minutes marked **Exact**. That
   proves the webhook and the signing key.
4. Open it on a phone. The open appears as **Inferred**, probably flagged as a
   machine, because Apple and Gmail fetch images automatically. That is the system
   being honest, not a bug.
5. Click the link. The page's script runs, because it is a page on the site, so the
   click shows as **Verified**. Security scanners fetch pages without running
   scripts, which is how they are told apart.
6. Unsubscribe one address with the footer link. It moves to the suppression list,
   and a second send skips it.
7. Reply from one address. It arrives at the inbox C4 forwards to. The campaign's
   reply count stays at zero until G5.

**How to know the worker sent it:**

```bash
journalctl -u paladin-worker --since "30 min ago"
```

---

## E. Production

**Starts when:** B1 and B7 are answered and the server exists.

### E1. Provision the production server and grant the developer access
**Who:** Matt · **Questions:** SRV-01 … SRV-03

### E2. Install Paladin on production, with the send worker
**Who:** the developer · **Waits on:** E1 and A4

1. Follow the dev server's layout (`DEPLOY-DEV-SERVER.md`), or `DEPLOY-UBUNTU.md`
   if production runs Docker.
2. Generate a fresh `JWT_SECRET_KEY` and `ENCRYPTION_KEY`. Never reuse dev's.
3. Do not copy dev's rate-limit overrides from its environment file. They work
   around a proxy that hides visitor addresses; with E3 done, the defaults are
   right.
4. Install from `main`, including `pip install -r requirements.txt`. Migrations
   apply on start.
5. Install the worker: copy `paladin-worker.service` and `paladin-worker.timer`
   into `/etc/systemd/system/`, run one pass through the real unit, then enable the
   timer. With Docker, add the worker service from `DEPLOY-UBUNTU.md` section 5.5
   instead, because the compose file does not include one.

```bash
sudo systemctl daemon-reload
sudo systemctl start paladin-worker.service
sudo systemctl enable --now paladin-worker.timer
```

**How to know it worked:**

```bash
systemctl list-timers paladin-worker.timer
journalctl -u paladin-worker --since "10 min ago"
```

The timer is scheduled, and the journal shows a pass that exited cleanly with
nothing to do. This failure is silent, so check rather than assume.

### E3. Route `links.ashfordbriggs.com` to production, with HTTPS and visitor addresses
**Who:** Matt and the developer · **Waits on:** B1 and E2

1. Build the route chosen in B1, with a certificate that covers
   `links.ashfordbriggs.com`.
2. Whatever forwards to Paladin must pass `Host`, `X-Forwarded-For` and
   `X-Forwarded-Proto`. Without the visitor's address, per-visitor rate limits act
   as one global cap, and the open and click classifier cannot use the address to
   spot a data-centre scanner. That is the situation on dev today.
3. Paladin trusts `X-Forwarded-For` only from the proxy addresses its service is
   told to trust (on dev, `127.0.0.1` and `10.0.0.1`), so production's service must
   name its own proxy.
4. Before relying on a proxy, test its connection to Paladin from the proxy host
   itself. It must return Paladin's JSON:

```bash
curl -H "Host: links.ashfordbriggs.com" http://BACKEND-ADDRESS/api/health
```

If a different site answers, Apache matched another virtual host. On dev,
Paladin's is bound to one LAN address (`10.0.0.80:80`), so a request arriving on
any other address, a Tailscale one for example, never reaches it. Add that address
to the `<VirtualHost>` line and allow the port through the firewall. That route has
not been tested yet.

For the nginx route in B1:

```nginx
server {
    listen 443 ssl;
    server_name links.ashfordbriggs.com;
    ssl_certificate     /etc/letsencrypt/live/links.ashfordbriggs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/links.ashfordbriggs.com/privkey.pem;
    location / {
        proxy_pass http://BACKEND-ADDRESS:80;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

Or, where HAProxy does the routing:

```
frontend https_in
    acl host_links hdr(host) -i links.ashfordbriggs.com
    use_backend paladin if host_links

backend paladin
    option forwardfor
    http-request set-header X-Forwarded-Proto https
    server paladin BACKEND-ADDRESS:80 check
```

**How to know it worked:**

```bash
curl https://links.ashfordbriggs.com/api/health
```

```bash
sudo grep -o 'xff=[^ ]*' /var/log/apache2/paladin-access.log | tail -3
```

From outside the network the first returns
`{"status":"ok","service":"ashford-briggs-api"}`, and a browser shows no
certificate warning. The second shows real visitor addresses rather than
`xff="-"`.

### E4. Make production's web server answer for `links.`
**Who:** the developer · **Waits on:** E2 · With Docker, Caddy's site block covers
this instead.

1. Add `ServerAlias links.ashfordbriggs.com` to Paladin's virtual host. On dev,
   `sites-enabled` holds a real file rather than a symlink, so check which it is on
   production before editing.
2. Run `apache2ctl configtest`, and reload only if it passes — a graceful reload,
   not a restart.
3. Check every other site on that box still loads.

### E5. Cut Mailgun over to production
**Who:** Matt and the developer · **Waits on:** E3 and E4

1. Enter the Mailgun credentials in production's Settings (C3 again), with Reply
   domain blank.
2. Set production's tracking URL to `https://links.ashfordbriggs.com`, plus the
   From details and postal address.
3. In Mailgun's webhooks, replace the dev URL with the one production's screen now
   shows, `https://links.ashfordbriggs.com/api/webhooks/mailgun`, and run Mailgun's
   Test again.
4. Run the D4 rehearsal again against production, with the internal list.

### E6. Take dev out of the sending path
**Who:** the developer · **Waits on:** E5

- Remove the Mailgun keys from dev's Settings, so nothing sent from dev can reach a
  real person.
- Remove the provisional `updates.ashfordbriggs.com` alias from the dev virtual
  host.
- If dev's front proxy is ever changed to forward visitor addresses, remove dev's
  rate-limit overrides too, so the defaults apply.

---

## F. The first real campaign

**Starts when:** phase E is finished and B4–B6 are answered.

### F1. Load past opt-outs first, then the contacts
**Who:** the developer

The first send must never reach someone who already asked to stop. Complaints are
the hardest reputation damage to undo.

1. Load the past unsubscribes, complaints and bounces from LST-04. **There is no
   screen or endpoint for this yet**, so it is a small development task first: a
   one-off import through the suppression service.
2. Import the contacts with a consent basis and country for each (B5). Anything
   with unknown consent stays unmailable. Re-importing is safe: an import cannot
   reactivate anyone who unsubscribed or bounced.
3. Add the seed inboxes to the audience (D3).
4. On the campaign, check the audience panel reconciles: the contacts in the
   segment, minus each exclusion, equal the number to be sent.

### F2. Write it, clear pre-flight, get sign-off
**Who:** the developer and John

- Send a test and read it on a phone and a laptop.
- Pre-flight shows no blockers. Read the warnings anyway.
- The approver from B6 signs off.

### F3. Send small first
**Who:** the developer

The new sending domain has no reputation yet, and volume has to be earned. Send to
a small slice of the most engaged contacts, such as recent demo requests and people
who have replied before: tens to a few hundred, not the whole list.

### F4. Read the results after 48 hours
**Who:** the developer

- Hard bounces: under about 2%.
- Spam complaints: under 0.1%. Gmail's hard limit is 0.3%.
- Domain trust: blocklists clean, and where the seed inboxes received it.
- Replies, the number that matters. Count them in the inbox C4 forwards to until G5
  is built.

If bounces or complaints run high, stop, clean the list, and do not raise the
volume until the rates come back down.

### F5. Grow the sends step by step
**Who:** the developer

Weekly at most, never more than double the previous send, and only while bounces
and complaints stay low. Providers read a sudden spike as a compromised account.

---

## G. Keep it healthy, and finish the gaps

**Starts when:** the first real send. Ongoing.

### G1. Automate DMARC report collection
**Who:** John and the developer · **Waits on:** B8

Once `dmarc@` has a real mailbox as a member, build the collector to read that
mailbox, reusing the seed inbox mechanism. Until then, upload reports weekly (A3).

### G2. Look at Domain trust every week
**Who:** the developer

The worker checks blocklists automatically twice a day and logs a loud error if the
domain is listed. Watch the trend in bounces, complaints and placement, and look
into any new sending source that appears in the DMARC reports.

### G3. Switch to a sending-only Mailgun key
**Who:** the developer and Matt

The same Mailgun account signs the client password emails, and a leaked account key
can do far more than send campaigns.

1. Change the connection check so it works with a sending-only key. It currently
   reads the domain's details, which such a key cannot. A small code change.
2. Matt issues a sending key for `updates.ashfordbriggs.com`.
3. Replace the account key in production's Settings.

### G4. Count real conversions from the product
**Who:** John and the developer · **Questions:** PRD-01 … PRD-03

No off-the-shelf email tool can see inside Paladin. With this, a report can say
"this campaign produced twelve logins" instead of stopping at the click.

1. A campaign link carries a token as `ab_t`. The landing page already strips it
   from the address bar; the product keeps it in the session so it survives to
   sign-up.
2. When that person books a demo or logs in for the first time, the product posts
   to `/api/attribution` with `{"token": "...", "name": "demo_booked"}`.
3. No credential is needed. The token is 128 bits of randomness minted per message,
   so holding one means having received that message.
4. Start with two events: `demo_booked` and `first_login`.

**How to know it worked:** the Conversions figure on a campaign scorecard shows
something other than zero.

### G5. Build reply capture
**Who:** the developer · **Waits on:** C4

The scorecard already has a replies figure, and a reply is the strongest signal the
system can get, but nothing records one (BUG-008).

1. Add an endpoint that accepts replies forwarded by a Mailgun route, verifies them,
   and records a reply against the message whose token is in the address.
2. Add that endpoint to C4's route, keeping the forward to a person as well.
3. Only then fill in **Reply domain**, so replies are addressed
   `replies+<token>@updates.ashfordbriggs.com` and can be matched.

---

## H. Lock the domain

**Starts when:** at least two weeks of DMARC reports are in. None of it blocks
sending, and rushing it does not make the domain safer; it makes the company's own
mail disappear.

### H1. Move `mail.ashfordbriggs.com` to a 2048-bit DKIM key, with both keys live during the switch
**Who:** Matt

**Customers feel a mistake here the same day.** This key signs the client password
and PIN emails. Mailgun lets both keys exist at once, so there is a window where the
old one still works while the new one is proven. Never collapse that window.

1. In Mailgun, open `mail.ashfordbriggs.com` and add a 2048-bit DKIM key. It gets a
   new selector, and the existing one stays.
2. Publish the new record at Namecheap; its host looks like
   `<newselector>._domainkey.mail`. Do not touch `k1._domainkey.mail` yet.
3. Wait for Mailgun to show the new key verified. Usually minutes; allow up to 48
   hours.
4. Trigger a real password or PIN email from the product to an address you control.
   Not a Mailgun test: the real path is what has to keep working.
5. Open it and choose **Show original**. The DKIM lines must name the new selector
   and pass:

   ```
   DKIM: 'PASS' with domain mail.ashfordbriggs.com
   dkim=pass header.i=@mail.ashfordbriggs.com header.s=<newselector>
   ```

   If it still names the old selector, Mailgun has not switched to the new key yet.
   Wait, send another, and check again.
6. Only once the new selector shows, delete the `k1._domainkey.mail` record.
7. Trigger one more real password email and confirm it still passes.

**If the new selector never shows:** stop, and change nothing else. The old key is
still published, so client mail is unaffected and there is no urgency. Ask Mailgun
support to switch the domain's active signing key; the problem is on their side, not
in the DNS.

**Why it can wait:** nothing breaks if this is never done. Every provider accepts a
1024-bit key; checkers flag it as weak and it is below current guidance. Do it before
the root domain reaches enforcement.

### H2. Account for every sender in the reports
**Who:** the developer · **Waits on:** two weeks of reports (A3 or G1)

Google Workspace, both Mailgun domains and the product's own password emails
(GW-05) should all pass. Anything else, such as a CRM, an invoicing tool or a
calendar service, is fixed until it passes or stops sending as the domain. The Trust
panel lists the worst source first and shows what each one is signed by, which is
how a forwarder, a forgotten legitimate sender and an outright forgery are told
apart.

### H3. Tighten the root domain in stages
**Who:** Matt · **Waits on:** H1, H2, and a clear verdict on the Domain trust panel

| Stage | Record | Hold until |
|---|---|---|
| 1 | `p=none` (today) | Every legitimate source passes |
| 2 | `p=quarantine; pct=25` | One week with no genuine mail quarantined. Ask the team whether anything went missing. |
| 3 | `p=quarantine` | One week clean |
| 4 | `p=reject` | Done. Nobody can send as the company except the systems it authorised, including anyone faking a password reset to clients. |

- Edit the existing `_dmarc` record at each stage. Never add a second one: two DMARC
  records at one name are invalid and treated as none.
- Keep `rua=mailto:dmarc@ashfordbriggs.com` in every version.

### H4. Then take `mail.ashfordbriggs.com` through the same stages
**Who:** Matt · **Waits on:** H1 and H3

`mail.ashfordbriggs.com` has its own DMARC record, so it does not inherit the root
domain's policy. Finishing H3 leaves it at `p=none` until its own record goes through
the same four stages.

### H5. Later, optionally: the company logo in inboxes (BIMI)
**Who:** Matt and John

Once the domain is fully enforced, BIMI can show the company logo beside its emails
in inboxes that support it. It needs a mark certificate, which makes it the only
expensive item in the whole project. Revisit it then.

---

## What the system does not do, deliberately or not yet

| | |
|---|---|
| **Exact open rates** | Nobody can produce these any more: about half of all tracked opens are machines. Opens are split between probable machines and possible people, and there is no bare open rate. |
| **Reply capture** | Not built yet (BUG-008). Replies reach a person through C4, and the scorecard's reply count stays at zero until G5. |
| **Automatic DMARC collection** | Needs a real mailbox inside the group (B8, then G1). Uploading reports works today. |
| **Screens for seed inboxes, contact import and past opt-outs** | The first two are API calls (D3); the third is a development task (F1). |
| **Scanner detection by visitor address** | Waits on the proxy forwarding addresses (E3). Until then the classifier works from the browser string, the referrer and timing; it degrades rather than breaks. |
| **Google Postmaster Tools** | Its API needs domain-wide delegation, and Google shows no data below roughly a few hundred Gmail messages a day. DMARC reports and seed inboxes answer the same questions at this volume. |
| **A database-backed test suite** | The 279 tests are unit tests. End-to-end behaviour was checked by hand against a real database. |

---

## Corrections

### 2026-09-12

- **Reply capture is not built.** The earlier version counted "a reply matched" as
  part of proving the loop, and the settings screen's help text said replies would be
  matched. Nothing records a reply. Replies are now forwarded to a person (C4), the
  Reply domain setting stays blank, and capture is step G5. The help text was
  corrected in the code the same day (BUG-009).
- **Real campaigns wait for production.** Dev rehearses on `devwww`, which already
  has HTTPS.
- **Mailgun's tracking needs no setting.** The earlier advice to switch it off in
  Mailgun was unnecessary: the app turns it off on every message.
- **Use the account's Mailgun API key.** A sending-only key would fail the
  connection check, which reads the domain's details.
- **Rehearse with a real send.** Test sends use a preview token, so a rehearsal built
  on them could never have confirmed the tracking.
- **Past opt-outs cannot be loaded yet**, so that is now a task before the first real
  campaign.
- **Proxying by another address.** The earlier proxy examples forwarded to the dev
  box's Tailscale address, but Paladin's vhost is bound to `10.0.0.80:80`, so a
  request arriving on another address is not served by it. E3 now tests that hop
  first.
- **Seed inboxes:** Gmail works, Microsoft's IMAP sign-in rules block the Outlook
  setting, and each seed must be in every audience.

### 2026-09-09

An earlier version described `89.187.170.160` as "the front proxy on your gateway at
10.0.0.1" and said to point `updates` at it while also adding the hostname to the
Apache vhost on the Paladin box. **Those are two different machines**, so that
instruction was internally inconsistent and would have sent tracking traffic to the
wrong server. `89.187.170.160` is the nginx host serving the public website and every
wildcard name; the Paladin box is reached through `104.48.125.58`.
