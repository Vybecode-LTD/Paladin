# Dev server deployment (ab-webserver → devwww.ashfordbriggs.com)

State of the **dev/demo** deployment set up on 2026-09-09, and how to operate
it. This is the shared company server, not a dedicated box: it also hosts
PBX systems and other sites. **Touch only the Paladin footprint listed here.**

## Footprint on the server

| What | Where |
|---|---|
| Code (built frontend in `backend/static`) | `/opt/paladin` — owner `mbarker` (does updates), group `paladin` (read-only for the service) |
| Config and secrets | `/opt/paladin/backend/.env` (mode 640, `mbarker:paladin`) |
| Python venv | `/opt/paladin/backend/.venv` (Python 3.10, system) |
| Service | `paladin.service` (systemd; runs as the `paladin` system user; `ExecStartPre` applies migrations) |
| Background worker | `paladin-worker.service` + `paladin-worker.timer` (systemd; source in `deploy/ubuntu/`). Sends due campaigns and runs the daily domain-trust checks. Takes a Postgres advisory lock (`84712026`) on its own connection, so an overlapping timer firing exits rather than double-sending. Logs: `journalctl -u paladin-worker` |
| App listener | `127.0.0.1:8000` only |
| Database | existing Postgres 14 on the box; role `paladin`, database `paladin` |
| Apache vhost | `/etc/apache2/sites-enabled/www.ashfordbriggs.com.conf` (`:80` only; reverse proxy to 8000; `ServerName ashfordbriggs.com`, aliases `devwww.ashfordbriggs.com` and `updates.ashfordbriggs.com` — the second is **provisional**, see "How traffic reaches it" below). **`sites-enabled/` holds a real file here, not the usual `a2ensite` symlink** — `sites-available/www.ashfordbriggs.com.conf` is a stale copy of the old static site (it still has a `:443` block) and is *not* what Apache serves. Edit the `sites-enabled/` file. The previous static-site version is kept at `sites-available/www.ashfordbriggs.com.conf.bak-2026-09-09-static`. |
| SSH access used for the deploy | the `claude-paladin-deploy` line in `~mbarker/.ssh/authorized_keys`; remove it with `sed -i '/claude-paladin-deploy/d' ~/.ssh/authorized_keys` when no longer wanted |
| Apache logs for this site only | `/var/log/apache2/paladin-access.log`, `paladin-error.log` |
| App logs | `journalctl -u paladin` |

Two OS-level changes were made and nothing else: `python3-venv` was installed
and Apache's `headers` module was enabled (needed for the forwarded-proto and
noindex headers).

## How traffic reaches it

```
internet ──443──▶ front proxy (LAN gateway 10.0.0.1, holds the Let's Encrypt
                  cert for devwww.ashfordbriggs.com, redirects http→https)
         ──80───▶ Apache vhost on this server ──▶ 127.0.0.1:8000 (uvicorn)
```

Consequences:
- **No certificate lives on this server for devwww.** `certbot` here fails
  (the HTTP-01 challenge is answered by the front proxy). Do not try.
- The vhost has **only a `:80` block**. The `:443` block from the original
  static-site vhost was dropped on 2026-09-09: nothing legitimate reaches it
  (the front proxy talks to `:80`), and the only certificate it could use is
  the expired `ashfordbriggs.com` one.
- **`updates.ashfordbriggs.com` is aliased on the vhost, but the tracking
  hostname is not settled and this alias is provisional.** The alias was added
  2026-09-09; the campaign tracking routes are root-mounted, so they answer on
  any hostname that reaches the app, and changing which name is used is a
  one-line vhost edit.

  **The current recommendation is to move tracking to a different name than the
  sending domain** — see `EMAIL-SETUP-RUNBOOK.md`, trap 1. Serving web traffic
  from `updates.` means it needs an A record, and per RFC 4592 the zone wildcard
  stops answering for any name that gains a record of any type — so the first
  Mailgun TXT record published on `updates.` would silently remove its address.
  Keeping the sending domain mail-only (no A record) and serving tracking from
  e.g. `links.ashfordbriggs.com` removes that trap entirely. **When that name is
  chosen, change this alias to match.**

  Either way, two things outside this box have to happen before any tracking
  hostname works:
  1. **DNS.** It must resolve to whichever machine will serve it. Note that the
     wildcard points at `89.187.170.160` (the nginx host serving the public
     website) while Paladin is reached through `104.48.125.58` — those are two
     different machines, so "the wildcard already covers it" is only true if the
     nginx host is the one doing the proxying.
  2. **TLS.** The front proxy's certificate covers `devwww.ashfordbriggs.com`
     only (no wildcard, no SAN), and the nginx host's covers `ashfordbriggs.com`
     and `www.` only. Whichever hostname serves tracking needs adding to
     whichever certificate is in front of it.
- **Rate limiting is degraded, by the front proxy, not by this box.** The
  vhost's access log records every candidate forwarded-address header
  (`xff=`, `xrip=`, `fwd=`, `cf=`), and the front proxy sends none of them,
  so the app sees every visitor as `10.0.0.1` and its per-IP limits become
  global caps. uvicorn is already configured to trust `X-Forwarded-For` from
  `127.0.0.1` (Apache) and `10.0.0.1`, so the moment the front proxy is set
  to forward the client address, real per-visitor limiting starts working
  with no change here. Until then `.env` raises the caps
  (`AUTH_RATE_LIMIT=60/minute`, `DEMO_RATE_LIMIT=60/hour`,
  `AI_RATE_LIMIT=200/hour`) so a shared bucket cannot lock the demo out;
  delete those three lines and restart the service once the proxy forwards
  addresses. Check with:
  `sudo grep -o 'xff=[^ ]*' /var/log/apache2/paladin-access.log | tail -3`
  (anything other than `xff="-"` means it is fixed).
- The vhost sends `X-Robots-Tag: noindex, nofollow`: this is a demo, it must
  not get indexed. The frontend's canonical/OG tags still say
  `ashfordbriggs.com` on purpose (that is the eventual production domain).

## Updating the site

From a machine with the repo (the server has no GitHub access; nothing is
cloned there):

```bash
cd /path/to/Paladin
git archive --format=tar.gz -o paladin.tar.gz main
scp paladin.tar.gz mbarker@<server>:/tmp/
```

On the server (as `mbarker`):

```bash
cd /opt/paladin
tar -xzf /tmp/paladin.tar.gz -C /opt/paladin && rm -f /tmp/paladin.tar.gz
cd frontend && npm ci --no-audit --no-fund && npm run build && rm -rf ../backend/static && cp -r dist ../backend/static
cd ../backend && .venv/bin/python -m pip install -q -r requirements.txt
sudo chown -R mbarker:paladin /opt/paladin && sudo chmod -R g+rX /opt/paladin && sudo chmod 640 /opt/paladin/backend/.env
sudo systemctl restart paladin
curl -sS http://127.0.0.1:8000/api/health
```

Migrations run automatically on restart. `.env` is not in the archive and is
never overwritten by an update.

## Operating

```bash
sudo systemctl status paladin
sudo journalctl -u paladin -n 100 --no-pager
sudo systemctl restart paladin
sudo tail -n 50 /var/log/apache2/paladin-error.log
```

Rotate a secret: edit `/opt/paladin/backend/.env`, then restart the service.
Rotating `JWT_SECRET_KEY` signs everyone out; rotating `ENCRYPTION_KEY` means
re-entering the SMTP password in the admin Settings screen.

## Removing it (if the demo is retired)

```bash
sudo systemctl disable --now paladin && sudo rm /etc/systemd/system/paladin.service && sudo systemctl daemon-reload
sudo cp /etc/apache2/sites-available/www.ashfordbriggs.com.conf.bak-2026-09-09-static /etc/apache2/sites-enabled/www.ashfordbriggs.com.conf && sudo systemctl reload apache2
sudo -u postgres psql -c "DROP DATABASE paladin;" -c "DROP ROLE paladin;"
sudo rm -rf /opt/paladin && sudo userdel paladin
```
