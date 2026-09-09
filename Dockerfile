# Stage 1: build the frontend (Vite static assets)
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: backend, serving the built frontend on the same origin
FROM python:3.13-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend-build /frontend/dist ./static

EXPOSE 8000

# Boot sequence (shell-form CMD so &&, ${PORT} and the || guard all work):
#   1. apply migrations
#   2. create the first admin ONLY if SEED_ADMIN_PASSWORD is set
#      (seed.py is idempotent: it skips a user that already exists)
#   3. start uvicorn on $PORT (Railway injects it; plain Docker defaults to 8000)
#
# --proxy-headers / --forwarded-allow-ips='*': this container is only ever
# reached through a reverse proxy (Railway's edge, or Caddy/Nginx on a VPS).
# Without these, request.client.host is the proxy's IP, so slowapi's per-IP
# rate limits (login 10/min, demo 5/hour) would be shared by every visitor.
# '*' is safe precisely because nothing but the proxy can reach us; never
# publish port 8000 directly to the internet.
CMD alembic upgrade head \
 && { [ -z "$SEED_ADMIN_PASSWORD" ] || python -m seed; } \
 && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} \
      --proxy-headers --forwarded-allow-ips='*'
