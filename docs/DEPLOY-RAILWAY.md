# Railway display deployment (puppyinfo.us)

The temporary **display / demo** deployment, live since 2026-09-08. It exists
so the site can be shown before the real domain is ready; it is not the
production plan (that is `DEPLOY-UBUNTU.md`).

## Where it runs

| Item | Value |
|---|---|
| Platform | Railway, project **"Ashford & Briggs"**, environment `production` |
| Services | `Paladin` (the app, built from the repo's root `Dockerfile`, GitHub-connected to `main`, auto-deploys on every push) and `Postgres` (Railway plugin) |
| Public URL | https://puppyinfo.us (custom domain attached in Railway; the generated Railway URL also works) |
| Health check | `/api/health` |
| Admin | `/admin/login` |

## Configuration (Railway → `Paladin` → Variables)

| Variable | Value / note |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` — a Railway reference, not a pasted URL |
| `JWT_SECRET_KEY`, `ENCRYPTION_KEY` | generated fresh for this deployment |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | the owner's key; `claude-sonnet-4-6` |
| `SITE_URL` | `https://puppyinfo.us` (feeds `/sitemap.xml`) |
| `CORS_ORIGINS` | `https://puppyinfo.us,https://www.puppyinfo.us,<the generated Railway URL>` |
| `DEBUG` | `false` |
| `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `APP_NAME` | defaults |

Changing a variable redeploys the service automatically.

## How it starts

The Dockerfile's `CMD` runs `alembic upgrade head`, then `python -m seed`
**only if** `SEED_ADMIN_PASSWORD` is set (the seed skips a user that already
exists), then uvicorn on Railway's `$PORT`. The first admin was created this
way and the seed variables were removed afterwards.

## Moving it to another domain

Two variables change: `SITE_URL` and `CORS_ORIGINS`. Add the domain to the
`Paladin` service in Railway first. The frontend's compiled-in
`ashfordbriggs.com` references need editing only if the final domain is
something else.

## Things that cost time once, so nobody repeats them

1. **Never set a start command** on the `Paladin` service, neither in
   `railway.toml` nor in the dashboard. It overrides the Dockerfile `CMD`,
   migrations silently stop running, and every database route returns 500
   with `relation "blog_posts" does not exist` while `/api/health` stays
   green. Railway also ignored `preDeployCommand` from `railway.toml`.
2. Removing a start command from `railway.toml` does not clear one already
   stored on the service; it had to be cleared through Railway's API
   (`serviceInstanceUpdate` with an empty `startCommand`).
3. `railway redeploy` reuses the previous deployment's settings snapshot. A
   settings change only takes effect on a **new** deployment: a push,
   `railway up`, or the `serviceInstanceDeploy` API call.
4. Railway **project tokens** cannot `railway ssh`, `railway run`, or delete
   services through the GraphQL API. `railway service delete --service <name> --yes`
   from the CLI does work with one.
5. The app runs uvicorn with `--proxy-headers --forwarded-allow-ips='*'` so
   per-IP rate limits see the real visitor behind Railway's edge rather than
   the edge itself.
