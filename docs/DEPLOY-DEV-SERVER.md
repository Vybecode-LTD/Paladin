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
| App listener | `127.0.0.1:8000` only |
| Database | existing Postgres 14 on the box; role `paladin`, database `paladin` |
| Apache vhost | `/etc/apache2/sites-enabled/www.ashfordbriggs.com.conf` (reverse proxy to 8000; `ServerName ashfordbriggs.com`, `ServerAlias devwww.ashfordbriggs.com`). The previous static-site version is kept at `sites-available/www.ashfordbriggs.com.conf.bak-2026-09-09-static`. |
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
- The `:443` block of the vhost still references the old, expired
  `ashfordbriggs.com` certificate; it is only reachable from the LAN/tailnet
  and is left as it was.
- uvicorn trusts `X-Forwarded-*` from `127.0.0.1` (Apache) and `10.0.0.1`
  (the front proxy), so per-IP rate limits see the real visitor as long as
  the front proxy sends `X-Forwarded-For`.
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
