#!/bin/bash
# scripts/update_env_safe.sh
# Usage: ./scripts/update_env_safe.sh <service_name> <KEY=VALUE> [KEY2=VALUE2 ...]
# Description: Safely updates environment variables using --update-env-vars (merge) instead of --set-env-vars (replace).

set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <service_name> <KEY=VALUE> [KEY2=VALUE2 ...]"
    exit 1
fi

SERVICE_NAME="$1"
shift
ENV_VARS=$(IFS=,; echo "$*")

echo "Safely updating env vars for ${SERVICE_NAME}..."
gcloud run services update "${SERVICE_NAME}" \
    --region us-central1 \
    --update-env-vars "${ENV_VARS}"

echo "✅ Environment variables updated."
