#!/bin/bash
set -euo pipefail

# scripts/cloud_run_entrypoint.sh
# Entrypoint for Cloud Run to handle secret injection and start the app.

echo "INFO: Starting Cloud Run Entrypoint..."

# Inject DATABASE_URL from secrets if available (TASK-007)
if [ -z "${DATABASE_URL:-}" ] && [ -n "${DB_PASSWORD:-}" ] && [ -n "${DB_USER:-}" ]; then
  echo "INFO: Constructing DATABASE_URL from secrets..."
  export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=${DB_HOST}"
  echo "INFO: DATABASE_URL constructed (masked password)."
fi

# Diagnostics
echo "INFO: Environment: ${ENVIRONMENT:-unknown}"
echo "INFO: DATABASE_URL set: $(if [ -n "${DATABASE_URL:-}" ]; then echo "YES"; else echo "NO"; fi)"

# Start App
# Inherit args or default to app.py
exec python app.py
