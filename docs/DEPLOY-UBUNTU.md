# Deploying Paladin on an Ubuntu server

Step-by-step runbook for standing this site up on a fresh Ubuntu server you
control (a VPS at Hetzner, DigitalOcean, Linode, AWS Lightsail, or a machine
in your own rack). Every command is meant to be copied as-is. Where a value is
yours to choose, it is written as `example.com` or shown in angle brackets.

The recommended path is **Docker Compose**: one command builds the frontend and
backend into an image, runs Postgres beside it, and puts Caddy in front for
automatic HTTPS. Nothing is installed on the host except Docker. A manual
(no-Docker) path is in the appendix for environments where Docker is not
allowed.

---

## 0. What you are deploying

```
 internet ──443/80──▶ caddy ──8000──▶ app (FastAPI + built React site) ──5432──▶ db (Postgres 17)
                     (TLS)            one container, one process              persistent volume
```

- **`app`** is built from the repo's root `Dockerfile`. On every start it runs
  the database migrations, optionally creates the first admin, then serves
  the API under `/api/*` and the React site for every other path.
- **`db`** is Postgres 17 on a named Docker volume. It is not reachable from
  the internet.
- **`caddy`** terminates HTTPS with a Let's Encrypt certificate it obtains and
  renews on its own, and proxies to `app`. It is the only container with
  published ports.

All configuration lives in one file: `deploy/ubuntu/.env`.

---

## 1. Prerequisites

| Item | Requirement |
|---|---|
| OS | Ubuntu 22.04 LTS or 24.04 LTS, 64-bit, fresh install |
| Size | 2 vCPU, **4 GB RAM** recommended. 2 GB works if you add swap (step 2.4); the frontend build needs the headroom once, at build time. 20 GB disk. |
| Access | A user with `sudo`, reachable over SSH |
| Domain | A domain or subdomain whose **A record already points at the server's public IP** before you start. Caddy cannot get a certificate otherwise. |
| Ports | 22, 80 and 443 reachable from the internet (open them in the provider's firewall/security group too, not only `ufw`) |
| Secrets | An **Anthropic API key** from the owner's console (used server-side for the AI blog assistant) |
| Code | Read access to the GitHub repo `Vybecode-LTD/Paladin`, or a copy of the source tree (step 3 covers both) |

---

## 2. Prepare the server

### 2.1 Updates and basics

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl git ufw
```

### 2.2 Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 443/udp
sudo ufw --force enable
sudo ufw status
```

### 2.3 Install Docker (official repository)

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Log out and back in (or run `newgrp docker`) so the group change applies, then
confirm:

```bash
docker compose version
```

You should see `Docker Compose version v2.x`. Docker starts on boot by
default, and every container below is set to restart automatically, so a
server reboot brings the site back without intervention.

### 2.4 Swap (only if the server has less than 4 GB RAM)

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 3. Get the code onto the server

Pick **one**.

**A. Clone from GitHub** (the repo is private, so use a token or deploy key):

```bash
sudo mkdir -p /opt/paladin && sudo chown "$USER":"$USER" /opt/paladin
git clone https://<GITHUB_TOKEN>@github.com/Vybecode-LTD/Paladin.git /opt/paladin
```

Create the token at GitHub → Settings → Developer settings → Fine-grained
tokens, scoped to this one repository with *Contents: Read*. This path makes
later updates a `git pull` (section 8).

**B. Copy an archive** (no GitHub access needed on the server). On the machine
that has the repo:

```bash
git archive --format=tar.gz -o paladin.tar.gz main
scp paladin.tar.gz <user>@<server-ip>:/tmp/
```

Then on the server:

```bash
sudo mkdir -p /opt/paladin && sudo chown "$USER":"$USER" /opt/paladin
tar -xzf /tmp/paladin.tar.gz -C /opt/paladin
```

Either way, finish with:

```bash
cd /opt/paladin/deploy/ubuntu
ls
# Caddyfile  docker-compose.yml  .env.example
```

---

## 4. Configure

```bash
cp .env.example .env
```

Generate the secrets. Run each command and paste its output into `.env`:

```bash
openssl rand -hex 24        # -> POSTGRES_PASSWORD
openssl rand -base64 48     # -> JWT_SECRET_KEY
python3 -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"   # -> ENCRYPTION_KEY
openssl rand -base64 18     # -> SEED_ADMIN_PASSWORD (temporary; you change it after first login)
```

Then edit the file:

```bash
nano .env
```

Fill in every value. The ones that are not generated:

| Variable | Set it to |
|---|---|
| `SITE_DOMAIN` | the bare hostname, e.g. `ashfordbriggs.com` |
| `SITE_URL` | the same host with `https://`, no trailing slash |
| `CORS_ORIGINS` | the same as `SITE_URL` (add `,https://www.<domain>` only if you enable www in the Caddyfile) |
| `ANTHROPIC_API_KEY` | the owner's key |
| `SEED_ADMIN_EMAIL` | the email the first admin will log in with |

Leave the "fixed" block at the bottom as it is. Never reuse the values from
the Railway display deployment or from a developer's `.env`.

### 4.1 If the final domain is not `ashfordbriggs.com`

The frontend has that domain compiled into the bundle for SEO purposes. It is
baked in at **build** time, so change it *before* the first `docker compose up`:

| File | What it holds |
|---|---|
| `frontend/src/components/Seo.tsx` (line 3) | canonical URL and JSON-LD for every page |
| `frontend/index.html` | Open Graph `og:url` |
| `frontend/public/robots.txt` | the `Sitemap:` line |
| `frontend/src/pages/Home.tsx`, `frontend/src/pages/About.tsx` | organization URLs in structured data |
| `frontend/src/pages/admin/PostList.tsx` | the click-to-copy public link for a post |
| `frontend/src/pages/Privacy.tsx`, `frontend/src/pages/Terms.tsx` | the site name in legal text |

`frontend/public/sitemap.xml` is a stale static copy; the backend generates
the real sitemap from `SITE_URL`. Delete the static file rather than editing it.

A one-liner for the mechanical replacements (review the diff afterwards; the
email addresses on the Contact page also contain the old domain and are a
business decision, not a hosting one):

```bash
cd /opt/paladin && grep -rl "ashfordbriggs.com" frontend/src frontend/index.html frontend/public/robots.txt | xargs sed -i 's#https://ashfordbriggs\.com#https://example.com#g'
```

---

## 5. Launch

```bash
cd /opt/paladin/deploy/ubuntu
docker compose up -d --build
```

The first build takes 3 to 6 minutes (npm install, Vite build, pip install).
Watch the app come up:

```bash
docker compose logs -f app
```

You are looking for these lines, in this order, then it is running:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 109933857eb1, init
INFO  [alembic.runtime.migration] Running upgrade 109933857eb1 -> b2f4c7a19d3e, ...
INFO  [alembic.runtime.migration] Running upgrade b2f4c7a19d3e -> c7e2f8a41b6d, ...
Created admin: <SEED_ADMIN_EMAIL>
IMPORTANT: change this password after first login.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Press `Ctrl-C` to stop following (the containers keep running). Then verify:

```bash
docker compose ps                       # all three: running / healthy
curl -sS https://<SITE_DOMAIN>/api/health
# {"status":"ok","service":"ashford-briggs-api"}
curl -sS https://<SITE_DOMAIN>/api/blog/posts
# []
curl -sS https://<SITE_DOMAIN>/sitemap.xml | head -5
```

Caddy obtains the certificate during the first request or two; if the
`curl` reports a TLS error in the first minute, wait and retry. Open
`https://<SITE_DOMAIN>/` in a browser: the marketing site should render.

---

## 6. First login and lock-down

1. Open `https://<SITE_DOMAIN>/admin/login` and sign in with
   `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`.
2. Change the password immediately (admin menu → change password).
3. Remove the seed credentials from the server and recreate the app container:

   ```bash
   cd /opt/paladin/deploy/ubuntu
   sed -i '/^SEED_ADMIN_/d' .env
   docker compose up -d
   ```

4. In the admin **Settings** screen, enter the company's SMTP host, port,
   username, password, sender address and sender name. The sender address
   must be one the SMTP account is allowed to send as (providers reject
   anything else with `553 Sender address rejected`); leave it blank to use
   `info@ashfordbriggs.com`. Demo-request replies are sent through that
   server; until it is configured, the reply action reports "SMTP is not
   configured yet". The password is stored encrypted with `ENCRYPTION_KEY`.
5. Create the other users (admin → Users). Roles: `author` can write and
   publish their own posts and use the AI assistant; `editor` can also manage
   all posts and the demo-request inbox; `admin` can additionally manage users.

---

## 7. What is where on the server

| Thing | Location |
|---|---|
| Code | `/opt/paladin` |
| Configuration and secrets | `/opt/paladin/deploy/ubuntu/.env` (mode 600 recommended: `chmod 600 .env`) |
| Database files | Docker volume `paladin_pgdata` |
| TLS certificates | Docker volume `paladin_caddy_data` |
| App logs | `docker compose logs app` (stdout; Docker keeps them) |
| Caddy logs | `docker compose logs caddy` |

---

## 8. Day-to-day operations

All commands run from `/opt/paladin/deploy/ubuntu`.

**Deploy a code update** (path A only; for path B, re-copy the archive first):

```bash
cd /opt/paladin && git pull && cd deploy/ubuntu
docker compose up -d --build
docker image prune -f
```

Migrations run automatically on start. Downtime is the few seconds the app
container takes to restart.

**Restart / stop / start**

```bash
docker compose restart app
docker compose down          # stops everything; data volumes are kept
docker compose up -d
```

**Logs**

```bash
docker compose logs -f app          # follow
docker compose logs --since 1h app  # last hour
```

**Database shell**

```bash
docker compose exec db psql -U paladin -d paladin
```

**Nightly backups** (kept 30 days). Run once to install the cron job:

```bash
mkdir -p /opt/paladin-backups
( crontab -l 2>/dev/null; echo '15 3 * * * cd /opt/paladin/deploy/ubuntu && docker compose exec -T db pg_dump -U paladin paladin | gzip > /opt/paladin-backups/paladin-$(date +\%F).sql.gz && find /opt/paladin-backups -name "*.sql.gz" -mtime +30 -delete' ) | crontab -
```

Copy `/opt/paladin-backups` somewhere off the server on a schedule (rsync,
object storage, your provider's snapshots). Test a backup once:

```bash
cd /opt/paladin/deploy/ubuntu && docker compose exec -T db pg_dump -U paladin paladin | gzip > /tmp/test.sql.gz && ls -lh /tmp/test.sql.gz
```

**Restore a backup** (into an empty database):

```bash
cd /opt/paladin/deploy/ubuntu
docker compose stop app
docker compose exec -T db psql -U paladin -d postgres -c "DROP DATABASE paladin;" -c "CREATE DATABASE paladin OWNER paladin;"
gunzip -c /opt/paladin-backups/paladin-<DATE>.sql.gz | docker compose exec -T db psql -U paladin -d paladin
docker compose start app
```

**Rotate a secret**: edit `.env`, then `docker compose up -d`. Rotating
`JWT_SECRET_KEY` signs everyone out. Rotating `ENCRYPTION_KEY` requires
re-entering the SMTP password in Settings.

---

## 9. Optional: carry content over from the Railway display site

If blog posts or users created on the temporary display deployment should
survive the move, restore Railway's database into the new server **before the
first `docker compose up` in section 5**:

1. In the Railway dashboard, open the `Postgres` service → *Settings* →
   *Networking* → enable **TCP Proxy**. Then copy `DATABASE_PUBLIC_URL` from
   its *Variables* tab.
2. On the new server, start only the database and load the dump straight in:

   ```bash
   cd /opt/paladin/deploy/ubuntu
   docker compose up -d db
   docker run --rm postgres:17-alpine pg_dump "<DATABASE_PUBLIC_URL>" --no-owner --no-privileges \
     | docker compose exec -T db psql -U paladin -d paladin
   ```

3. Remove `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` from `.env` (the users
   come with the dump), then continue with section 5.
4. Disable the TCP proxy on Railway again afterwards.

The dump includes the migration bookmark (`alembic_version`), so the app
applies only migrations newer than the dump on its first start. The one thing
that does not carry over is the SMTP password saved in Settings: it is
encrypted with Railway's `ENCRYPTION_KEY`, which you deliberately did not
reuse. Re-enter it in Settings once.

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `docker compose up` fails with `set POSTGRES_PASSWORD in deploy/ubuntu/.env` | `.env` missing or a required value blank | `cp .env.example .env` and fill it in |
| Build dies during `npm run build` or `vite build` with no clear error | Out of memory on a 2 GB box | Add swap (2.4), run `docker compose up -d --build` again |
| `app` restarts in a loop; logs show `Connection refused` on port 5432 | Database not ready or wrong password | `docker compose logs db`; make sure `POSTGRES_PASSWORD` was not changed after the volume was created (if it was, `docker compose down -v` wipes the DB, then start over) |
| Site loads but `/api/blog/posts` returns 500 and logs say `relation "blog_posts" does not exist` | Migrations did not run: something is overriding the container's start command | Do not set a `command:` for `app` in compose; the Dockerfile CMD must run `alembic upgrade head` first |
| Browser shows CORS errors on the admin pages | `CORS_ORIGINS` does not match the origin in the address bar exactly (scheme, host, no trailing slash) | Fix `.env`, `docker compose up -d` |
| Caddy logs `obtaining certificate ... failed` | DNS not pointing here yet, or port 80/443 blocked at the provider | Fix DNS/firewall; Caddy retries automatically |
| Sitemap contains the wrong hostname | `SITE_URL` wrong | Fix `.env`, `docker compose up -d` |
| Login works for one person, then everyone gets `429 Too Many Requests` | The app is not seeing real client IPs, so all visitors share one rate-limit bucket | The Dockerfile already passes `--proxy-headers --forwarded-allow-ips='*'`; if you replaced Caddy with another proxy, make sure it sends `X-Forwarded-For` |
| Everything is up but the site shows the old marketing copy / old domain | The frontend is compiled into the image at build time | Any change under `frontend/` needs `docker compose up -d --build` |

Health check from the host at any time:

```bash
docker compose ps
docker compose exec app python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/api/health').read().decode())"
```

---

## Appendix A: without Docker (manual install)

Use this only where Docker is not permitted. Tested versions: Ubuntu 24.04
(Python 3.12) and 22.04 (Python 3.10); Node 20; Postgres from Ubuntu's own
packages.

```bash
# 1. System packages
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip build-essential libpq-dev postgresql nginx certbot python3-certbot-nginx git
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 2. Database
sudo -u postgres psql -c "CREATE USER paladin WITH PASSWORD '<POSTGRES_PASSWORD>';" \
                       -c "CREATE DATABASE paladin OWNER paladin;"

# 3. Code (see section 3), owned by a dedicated user
sudo useradd -r -m -d /opt/paladin -s /usr/sbin/nologin paladin 2>/dev/null || true
sudo chown -R paladin:paladin /opt/paladin

# 4. Frontend build -> backend/static (the API serves it from there)
cd /opt/paladin/frontend && sudo -u paladin npm ci && sudo -u paladin npm run build
sudo -u paladin rm -rf ../backend/static && sudo -u paladin cp -r dist ../backend/static

# 5. Backend
cd /opt/paladin/backend
sudo -u paladin python3 -m venv .venv
sudo -u paladin .venv/bin/python -m pip install -r requirements.txt
sudo -u paladin cp .env.example .env && sudo chmod 600 .env
sudo -u paladin nano .env   # same variables as section 4, plus:
                            # DATABASE_URL=postgresql://paladin:<POSTGRES_PASSWORD>@localhost:5432/paladin

# 6. Migrations + first admin (one time)
sudo -u paladin .venv/bin/alembic upgrade head
sudo -u paladin env SEED_ADMIN_EMAIL=<email> SEED_ADMIN_PASSWORD=<temp-password> .venv/bin/python -m seed
```

Systemd unit, `/etc/systemd/system/paladin.service`:

```ini
[Unit]
Description=Paladin (Ashford & Briggs) API + site
After=network.target postgresql.service
Requires=postgresql.service

[Service]
User=paladin
WorkingDirectory=/opt/paladin/backend
EnvironmentFile=/opt/paladin/backend/.env
ExecStartPre=/opt/paladin/backend/.venv/bin/alembic upgrade head
ExecStart=/opt/paladin/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now paladin
curl -sS http://127.0.0.1:8000/api/health
```

Nginx site, `/etc/nginx/sites-available/paladin`:

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/paladin /etc/nginx/sites-enabled/paladin
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d example.com     # obtains the certificate and rewrites the site for HTTPS
```

Updating later: `git pull`, rebuild the frontend (step 4), reinstall
requirements if they changed (step 5), then `sudo systemctl restart paladin`
(migrations run in `ExecStartPre`).

---

## Appendix B: how this differs from the Railway display deployment

| | Railway (display) | Ubuntu (this runbook) |
|---|---|---|
| Build | Railway builds the same `Dockerfile` on each push to `main` | `docker compose up -d --build` on the server |
| Database | Railway Postgres plugin, `DATABASE_URL` via variable reference | Postgres 17 container on a Docker volume; `DATABASE_URL` derived from `POSTGRES_PASSWORD` |
| TLS / domain | Railway edge, custom domain added in the dashboard | Caddy, automatic Let's Encrypt |
| Secrets | Service variables in the dashboard | `deploy/ubuntu/.env` |
| Start command | Must stay empty in Railway so the Dockerfile CMD runs | Same Dockerfile CMD; compose sets no `command:` |
| First admin | Seed variables set once, then removed | Same, via `.env` |
