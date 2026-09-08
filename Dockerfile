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

# Run migrations, bootstrap the first admin only when SEED_ADMIN_PASSWORD is
# set (seed.py is idempotent: it skips if that user already exists), then
# start. Shell-form CMD so `&&`, `${PORT}` and the `||` guard all work.
CMD alembic upgrade head  && { [ -z "$SEED_ADMIN_PASSWORD" ] || python -m seed; }  && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
