#!/bin/bash

set -euo pipefail

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

# Start nginx in the background
echo "Starting nginx..."
nginx

# Wait a moment for nginx to start
sleep 2

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

# Diagnostics
echo "=== DIAGNOSTICS START ==="
which python || echo "python not found"
python --version || echo "python version failed"
echo "Checking gunicorn module..."
python -m gunicorn --version 2>&1 || echo "gunicorn module check failed"
echo "Checking app.py imports..."
python -c "import app; print('app.py import OK')" 2>&1 || echo "app.py import FAILED"
echo "=== DIAGNOSTICS END ==="

# Use module invocation to avoid issues with gunicorn entrypoint script paths
# Add verbose logging to capture errors on startup
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
echo "Launching gunicorn with args: ${GUNICORN_ARGS[*]}"
exec python -m gunicorn "${GUNICORN_ARGS[@]}" app:app