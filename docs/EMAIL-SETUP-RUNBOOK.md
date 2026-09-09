# Email analytics — setup runbook for the owners

Everything that has to be done by a person with an account login, rather than by
someone with access to the code. Written for Matt and John.

Verified against live DNS and the running servers on **2026-09-09**. Where this
document contradicts an earlier copy of the runbook, this one is correct — see
"Correction to the earlier runbook" at the end.

For what the system does and how it is built, see `EMAIL-ANALYTICS.md`.

## What the network actually looks like

Two different machines serve `ashfordbriggs.com` names, and telling them apart is
the key to every DNS decision below.

| Name | Resolves to | What is there |
|---|---|---|
| `ashfordbriggs.com` | 89.187.170.160 | nginx 1.24. The public website. Certificate covers `ashfordbriggs.com` and `www.` **only**. |
| anything else `*.ashfordbriggs.com` | 89.187.170.160 | The same nginx, via a **wildcard** record. It answers for any name, but its certificate does not, so HTTPS fails the name check. |
| `devwww.ashfordbriggs.com` | 104.48.125.58 | An **explicit exception** to the wildcard. The AT&T line in Jacksonville → front proxy → Apache on 10.0.0.80 → Paladin on 127.0.0.1:8000. Certificate covers `devwww` only. |

Existing mail, unchanged by any of this:

```
MX   ashfordbriggs.com          smtp.google.com          (Google Workspace)
TXT  ashfordbriggs.com          v=spf1 include:_spf.google.com ~all
TXT  _dmarc.ashfordbriggs.com   v=DMARC1; p=none; rua=mailto:jevans@ashfordbriggs.com
```

There is already a Mailgun sending domain, **`mail.ashfordbriggs.com`**, used by
the product to send clients their passwords and PIN codes. It signs with a
1024-bit DKIM key. Nothing in this runbook should disturb it, and one task below
is specifically about not disturbing it.

---

## The three things that will bite

### 1. Giving the campaign subdomain mail records can take it offline

**Only applies if you serve web traffic from the same name you send mail from.**
A DNS wildcard answers only for names that have **no records of any type**. The
moment `updates.ashfordbriggs.com` gets a single TXT record, the wildcard stops
answering for it entirely — including the A record you never touched. Every
tracking and unsubscribe link in already-sent mail dies with it.

This is not a theory. It is demonstrable on your own domain right now:

```
_dmarc.ashfordbriggs.com      has a TXT record  ->  A lookup returns NOTHING
nonsense-abc123.ashford...    has no records    ->  A lookup returns 89.187.170.160
```

**How to avoid it — the clean way.** Do not serve web traffic from the sending
domain at all. Split the two jobs across two names:

| Name | Job | DNS it needs |
|---|---|---|
| `updates.ashfordbriggs.com` | Mailgun sending domain | SPF TXT + DKIM TXT (+ MX only if receiving). **No A record.** Sending mail does not require one. |
| `links.ashfordbriggs.com` | tracking pixel, click redirects, unsubscribe page | Nothing new — the wildcard already covers it, and it never gets a mail record, so it stays covered. |

With the split, the trap cannot fire: the name that gets mail records does not
need to resolve to a web server, and the name that serves web never gets a mail
record. It also means **no new DNS records for the tracking host** — which is how
Matt prefers to run things.

**If you would rather use one name anyway,** then `updates.ashfordbriggs.com`
needs an explicit A record published **in the same editing session** as the TXT
records, pointing at whichever machine will serve the tracking traffic (see
task C below — it is not automatically 89.187.170.160).

**How to know it worked**

```bash
nslookup -type=TXT updates.ashfordbriggs.com
```
```bash
nslookup links.ashfordbriggs.com
```
The first must show the SPF record. The second must return an address.

**If it has already gone wrong,** it is recoverable within one TTL (about half an
hour on Namecheap's automatic setting). Add the missing A record. No mail is
lost — links simply fail while it is down.

### 2. Rotating the old DKIM key touches your clients' password emails

The 1024-bit key on `mail.ashfordbriggs.com` signs the passwords and PIN codes
the product sends clients. Remove it before its replacement is proven and those
messages start failing authentication — and once the domain is enforced, clients
stop receiving their passwords. **This is the one task here where a mistake is
felt by customers the same day.**

**How to do it safely.** Mailgun lets both keys exist at once. Never collapse
that window.

1. In Mailgun, open `mail.ashfordbriggs.com`, find DKIM settings, add a
   **2048-bit** key. Mailgun issues it under a new selector and leaves the
   existing one alone.
2. Publish the new record at Namecheap — Host looks like
   `<newselector>._domainkey.mail`. **Do not touch `k1._domainkey.mail` yet.**
3. Wait until Mailgun shows the new key verified. Usually minutes; allow 48 hours.
4. Trigger a **real** password or PIN email from the product to an address you
   control — not a Mailgun test, because the real path is what has to keep working.
5. Open it, choose **Show original**, and confirm the DKIM line names the new
   selector and says `dkim=pass`.
6. Only then remove the old record.

This is worth doing before the root domain reaches enforcement. It blocks nothing
else in this runbook.

### 3. HTTPS for the tracking hostname is not on the Paladin server

Certbot on the Paladin box cannot issue a certificate for these names, because
the machine in front of it answers the ACME challenge. Other sites on that box do
have local certificates — because they point straight at it rather than through
the proxy, which is exactly why this looks like it should work and does not.

The certificate currently in front of Paladin covers `devwww.ashfordbriggs.com`
and nothing else. No wildcard, no second name. So whichever hostname ends up
serving tracking needs a certificate that covers it.

**How to fix it** depends on which machine serves the tracking host — this is the
decision in task C. ACME already works on both machines, so either way this is an
addition to a proven setup, not a new one.

*If tracking is served from the nginx box (89.187.170.160), the recommended
option:* add a server block for `links.ashfordbriggs.com`, issue a certificate
for it, and proxy to Paladin.

```nginx
server {
    listen 443 ssl;
    server_name links.ashfordbriggs.com;
    ssl_certificate     /etc/letsencrypt/live/links.ashfordbriggs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/links.ashfordbriggs.com/privkey.pem;
    location / {
        proxy_pass http://100.123.86.59:80;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

*If a proxy such as HAProxy does the routing instead:*

```
frontend https_in
    acl host_links hdr(host) -i links.ashfordbriggs.com
    use_backend paladin if host_links

backend paladin
    option forwardfor
    http-request set-header X-Forwarded-Proto https
    server paladin 100.123.86.59:80 check
```

*If tracking is served from the office box instead,* add the name to the existing
certificate on the front proxy and forward it to `10.0.0.80:80` — the same
backend `devwww` already uses:

```bash
certbot --expand -d devwww.ashfordbriggs.com -d links.ashfordbriggs.com
```

`100.123.86.59` is the Paladin box's Tailscale address, which avoids depending on
that ADSL line's public IP — but it only works if the proxy host is on the same
tailnet. **Worth confirming.**

Whichever route you take, **tell me when it is done** and I add one line to the
Apache vhost so it answers for the new name. Until that line exists the request
reaches Apache and falls through to a different site.

**Those `X-Forwarded-For` lines are not optional decoration.** The proxy in front
of Paladin currently sends no forwarding headers at all, so the app sees every
visitor as a single IP and its per-visitor rate limits behave as one global cap.
Adding them fixes a real, existing defect.

**How to know it worked**

```bash
curl https://links.ashfordbriggs.com/api/health
```
Expect `{"status":"ok","service":"ashford-briggs-api"}`. A certificate warning
means the certificate step is incomplete; landing on a different site or a
redirect means the forwarding rule or the vhost line is.

---

## The critical path to a first send

In order. Everything else can wait.

1. **A** — Create the Mailgun sending domain and collect its DNS records.
2. **B** — Publish those records at Namecheap (see trap 1 for the shape).
3. **C** — Decide which machine serves the tracking hostname, and get a
   certificate and a forwarding rule for it (trap 3).
4. **D** — Create the DMARC report mailbox and point `rua` at it.
5. **E** — Give me the sending identity: From name, From address, reply-to, and
   the postal address that must appear in the footer.
6. **F** — I deploy, install the worker, and add the vhost line.
7. **G** — Enter the Mailgun credentials in Settings, import contacts, send.

Steps 1–5 are yours. Step 6 is mine. Step 7 is together.

---

## A. In the Mailgun account

**A1. Confirm which region the account is in.** US and EU accounts use different
API hosts (`api.mailgun.net` vs `api.eu.mailgun.net`), and using the wrong one
fails with a confusing authentication error. The region is shown on the domain
page.

**A2. Add `updates.ashfordbriggs.com` as a sending domain.** A subdomain, not the
root — this keeps campaign reputation separate from the Google Workspace mail on
the root domain, so a bad campaign cannot damage your ability to receive business
email. Mailgun will show a list of DNS records; **copy all of them before leaving
the page**, because task B needs them all at once.

**A3. Get the API key.** Sending credential.

**A4. Get the HTTP webhook signing key.** **This is a different credential from
the API key**, on a different settings page, and confusing the two is the single
most common setup error here. Without the correct signing key the system rejects
every delivery event Mailgun sends — deliberately, because accepting unverified
webhooks would let anyone forge delivery data.

**A5. Point Mailgun's webhooks at the app** once task C is done:
`https://<tracking-host>/api/webhooks/mailgun`. Subscribe to delivered,
permanent failure, temporary failure, complained and unsubscribed.

**A6. Leave Mailgun's own open and click tracking OFF.** Paladin does its own,
and running both produces double-counted, contradictory numbers.

## B. DNS at Namecheap

Domain List → Manage → Advanced DNS. Namecheap strips the base domain, so the
Host column below is what you type, not the full name.

With the recommended split, `updates` needs **no A record**:

| Type | Host | Value |
|---|---|---|
| TXT | `updates` | `v=spf1 include:mailgun.org ~all` |
| TXT | `<selector>._domainkey.updates` | from Mailgun |
| TXT | `_dmarc.updates` | `v=DMARC1; p=reject; rua=mailto:dmarc@ashfordbriggs.com` |

`p=reject` is safe **on this new subdomain from day one**, because nothing has
ever legitimately sent from it. That is the opposite of the advice for the root
domain, which must be staged — see "Locking the domain" below.

Add MX records only if you want Mailgun to receive replies at that subdomain.
Replies to a campaign go to the reply-to address in task E, so this is optional.

Save, then return to Mailgun and press **Verify**.

## C. The routing decision

Pick where the tracking hostname is served — the nginx box or the office box —
and complete the certificate and forwarding work in trap 3. **This is the only
open architectural decision in the whole setup**, and everything in step 6 waits
on it.

Also worth confirming while you are in there: which host terminates TLS for the
domain generally, and whether it is on the tailnet.

## D. Google Workspace admin

**D1. Create the DMARC report address.** A group or shared mailbox at
`dmarc@ashfordbriggs.com`. Reports currently go to `jevans@ashfordbriggs.com`
personally, which means they stop being read the moment John is busy. These
arrive daily from every major provider and are the raw material the Trust panel
reads.

**D2. Confirm the From address** the product uses for password and PIN emails, so
campaign mail does not collide with it.

**D3. Confirm two-step verification is enforced** for all users. A compromised
mailbox on a sending domain undoes every reputation gain in this document.

## E. Information only you have

- **From name and From address** for campaigns.
- **Reply-to address**, and who watches it. Replies are the highest-value signal
  the system measures, and they only count if someone reads them.
- **A physical postal address** for the footer. This is a legal requirement under
  CAN-SPAM, and pre-flight **blocks** a send without it.
- **The contact list**, with a consent basis per contact. Contacts imported with
  unknown consent are never mailed — the system refuses rather than assuming, so
  a list without provenance is a list that will not send.

## F. On the server (mine)

Deploy the code, install the send worker (`paladin-worker.service` +
`paladin-worker.timer`), add the tracking hostname to the Apache vhost, and run
the migrations. See `DEPLOY-DEV-SERVER.md`.

## G. Inside the app

1. **Settings → Sender** — choose Mailgun, enter the region, API key and webhook
   signing key. Both are encrypted before they are stored.
2. **Analytics → Contacts** — import the list, set the consent basis.
3. **Analytics → Campaigns** — write the campaign. Pre-flight runs before it can
   go out and will refuse on the four blockers: no sender, no From address, no
   tracking URL, no postal address.
4. **Send to a small segment first.** Check the Trust panel afterwards.

---

## Locking the domain (the slow track)

The root domain is at `p=none` today — DMARC is watching and reporting, but
enforcing nothing. Moving to enforcement is what stops anyone forging
`ashfordbriggs.com`, and it must be staged, because going straight to `p=reject`
before every legitimate sender is passing is how a company silently stops
receiving its own mail.

| Stage | Record | Wait for |
|---|---|---|
| 1. Watch | `p=none` (today) | Two weeks of reports with every legitimate source identified and passing |
| 2. Quarantine a quarter | `p=quarantine; pct=25` | One week, no legitimate mail quarantined |
| 3. Quarantine all | `p=quarantine` | One week clean |
| 4. Reject | `p=reject` | Done |

**The Trust panel gates this.** It carries an explicit verdict on whether it is
safe to tighten, and it refuses while any source is still failing. Do not advance
a stage the panel has not cleared.

---

## What breaks if you skip something

| Skipped | What happens |
|---|---|
| Webhook signing key (A4) | No delivery, bounce or complaint data at all. Opens and clicks still work, so it looks like it is working — the tier labels in the UI are how you would notice. |
| Certificate for the tracking host (trap 3) | Every recipient clicking a link gets a browser security warning with your company name on it. |
| Postal address (E) | Pre-flight blocks the send. Deliberate. |
| Consent basis on import (E) | Contacts import but are never mailable. |
| DMARC mailbox (D1) | The Trust panel has nothing to read, and the enforcement path above cannot start. |
| Old DKIM key rotated carelessly (trap 2) | Clients stop receiving passwords. |

---

## Correction to the earlier runbook

An earlier version of this runbook described `89.187.170.160` as "the front proxy
on your gateway at 10.0.0.1" and told you to point `updates` at it while also
adding the hostname to the Apache vhost on the Paladin box. **Those are two
different machines**, so that instruction was internally inconsistent and would
have sent tracking traffic to the wrong server.

The corrected picture is in "What the network actually looks like" above:
`89.187.170.160` is the nginx host serving the public website and every wildcard
name; the Paladin box is reached through `104.48.125.58`. The choice between them
is now task C, made explicitly rather than assumed.
