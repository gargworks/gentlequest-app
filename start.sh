#!/bin/bash

set -euo pipefail
export PYTHONUNBUFFERED=1

echo "DEBUG: Starting up..."
echo "DEBUG: DATABASE_URL is '${DATABASE_URL:-}'"
echo "DEBUG: DB_USER is '${DB_USER:-}'"
echo "DEBUG: DB_HOST is '${DB_HOST:-}'"
if [ -n "${DB_PASSWORD:-}" ]; then
  echo "DEBUG: DB_PASSWORD is set (length: ${#DB_PASSWORD})"
else
  echo "DEBUG: DB_PASSWORD is UNSET or EMPTY"
fi

# Inject DATABASE_URL from secrets if available (TASK-007)
# This allows us to remove the hardcoded password from cloudbuild.yaml
if [ -z "${DATABASE_URL:-}" ] && [ -n "${DB_PASSWORD:-}" ] && [ -n "${DB_USER:-}" ]; then
  echo "Constructing DATABASE_URL from secrets..."
  # Construct standard PostgreSQL connection string
  # host usually contains the socket path for Cloud SQL (e.g. /cloudsql/PROJECT:REGION:INSTANCE)
  export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=${DB_HOST}"
  echo "DEBUG: DATABASE_URL constructed (masked password)."
fi

# Determine environment (default to docker/local)
ENVIRONMENT_NAME="${ENVIRONMENT:-docker}"

# Decide nginx listen port
# In docker/local, always keep nginx on 80 to avoid conflicts with Gunicorn (5055).
# Honor PORT when running on Render, Cloud Run, or production-like environments.
PORT_TO_USE="80"
if [ -n "${PORT:-}" ] && { [ -n "${RENDER:-}" ] || [ -n "${RENDER_SERVICE_ID:-}" ] || [ -n "${K_SERVICE:-}" ] || [ "${ENVIRONMENT_NAME}" = "render" ] || [ "${ENVIRONMENT_NAME}" = "production" ] || [ "${ENVIRONMENT_NAME}" = "gcp" ]; }; then
  PORT_TO_USE="${PORT}"
fi

echo "ENVIRONMENT=${ENVIRONMENT_NAME} | PORT env: ${PORT:-<not set>} | nginx listen port: ${PORT_TO_USE}"

# If chosen port differs from default 80, update nginx listen port
if [ "${PORT_TO_USE}" != "80" ]; then
  echo "Configuring nginx to listen on port ${PORT_TO_USE}..."
  sed -i "s/listen 80;/listen ${PORT_TO_USE};/g" /etc/nginx/nginx.conf
fi

# nginx will be started AFTER gunicorn is ready (at the end of the script)

# Start Flask application with Gunicorn (backend listens on 5055; nginx proxies /api to it)
echo "Starting Flask application..."
# Wait for dependencies (Postgres, Redis) to be ready
# Skip PostgreSQL wait if DATABASE_URL is set (production mode with external DB)
if [ -n "${DATABASE_URL:-}" ]; then
  echo "Using external DATABASE_URL - skipping local PostgreSQL wait"
else
  DB_HOST="db"
  DB_USER="${POSTGRES_USER:-ai_buddy}"
  DB_NAME="${POSTGRES_DB:-ai_buddy}"
  
  echo "Waiting for PostgreSQL at ${DB_HOST} (db=${DB_NAME} user=${DB_USER})..."
  for i in $(seq 1 60); do
    if pg_isready -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" -t 1 >/dev/null 2>&1; then
      echo "PostgreSQL is ready."
      break
    fi
    echo "PostgreSQL not ready yet (attempt $i/60)..."
    sleep 1
  done
fi

# Check for Redis
# Skip wait if REDIS_URL is set (production/Render mode) - app handles connection retry
# Also skip if running on Cloud Run (K_SERVICE) without Redis configured
if [ -n "${REDIS_URL:-}" ]; then
  echo "Using external REDIS_URL - skipping local Redis wait"
elif [ -n "${K_SERVICE:-}" ]; then
  echo "Running on Cloud Run without REDIS_URL - skipping Redis wait (caching disabled)"
else
  REDIS_HOST="redis"

  echo "Waiting for Redis at ${REDIS_HOST}..."
  for i in $(seq 1 60); do
    if redis-cli -h "${REDIS_HOST}" ping 2>/dev/null | grep -q PONG; then
      echo "Redis is ready."
      break
    fi
    echo "Redis not ready yet (attempt $i/60)..."
    sleep 1
  done
fi

# Diagnostics (quick checks only - don't import app.py as it's slow)
echo "=== DIAGNOSTICS ==="
which python || echo "python not found"
python --version || echo "python version failed"
echo "=== END DIAGNOSTICS ==="

# Build Gunicorn command
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
GUNICORN_LOG_LEVEL="${GUNICORN_LOG_LEVEL:-debug}"
GUNICORN_ARGS=(
  -b 0.0.0.0:5055
  --workers "${GUNICORN_WORKERS}"
  --timeout "${GUNICORN_TIMEOUT}"
  --keep-alive 5
  --access-logfile -
  --error-logfile -
  --log-level "${GUNICORN_LOG_LEVEL}"
)

echo "Launching gunicorn in background with args: ${GUNICORN_ARGS[*]}"
python -m gunicorn "${GUNICORN_ARGS[@]}" app:app &
GUNICORN_PID=$!

# Wait for Gunicorn to start listening on port 5055
echo "Waiting for Gunicorn to be ready on port 5055..."
MAX_WAIT=120
for i in $(seq 1 $MAX_WAIT); do
  if nc -z 127.0.0.1 5055 2>/dev/null; then
    echo "✅ Gunicorn is ready on port 5055 (waited ${i}s)"
    break
  fi
  if ! kill -0 $GUNICORN_PID 2>/dev/null; then
    echo "❌ Gunicorn process died unexpectedly!"
    exit 1
  fi
  sleep 1
done

if ! nc -z 127.0.0.1 5055 2>/dev/null; then
  echo "❌ Gunicorn failed to start within ${MAX_WAIT}s"
  exit 1
fi

# NOW start nginx (after Gunicorn is ready)
echo "Starting nginx..."
nginx

echo "✅ All services started. Waiting for Gunicorn process..."
wait $GUNICORN_PID