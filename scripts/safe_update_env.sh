#!/bin/bash
# Safe Environment Variable Update Script
# Part of Phase 67: Infrastructure Hardening
# 
# Usage: ./safe_update_env.sh SERVICE_NAME VAR_NAME VAR_VALUE
#
# This script safely updates a single env var while preserving all others.
# It creates a backup and supports rollback.

set -euo pipefail

SERVICE_NAME="${1:-}"
VAR_NAME="${2:-}"
VAR_VALUE="${3:-}"
REGION="${REGION:-us-central1}"
PROJECT="${PROJECT:-gen-lang-client-0894185576}"
BACKUP_DIR="${HOME}/.nucleus/env_backups"

if [[ -z "$SERVICE_NAME" || -z "$VAR_NAME" || -z "$VAR_VALUE" ]]; then
    echo "Usage: $0 SERVICE_NAME VAR_NAME VAR_VALUE"
    echo "Example: $0 gentlequest-backend ENVIRONMENT production"
    exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "📋 Fetching current env vars for $SERVICE_NAME..."
CURRENT_VARS=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT" \
    --format="json" | jq -r '.spec.template.spec.containers[0].env // []')

BACKUP_FILE="$BACKUP_DIR/${SERVICE_NAME}_$(date +%Y%m%d_%H%M%S).json"
echo "$CURRENT_VARS" > "$BACKUP_FILE"
echo "✅ Backup saved to $BACKUP_FILE"

# Build new env var list
NEW_VARS=$(echo "$CURRENT_VARS" | jq --arg name "$VAR_NAME" --arg value "$VAR_VALUE" '
    [.[] | select(.name != $name)] + [{"name": $name, "value": $value}]
')

# Convert to gcloud format
ENV_STRING=$(echo "$NEW_VARS" | jq -r '[.[] | select(.value != null) | "\(.name)=\(.value)"] | join(",")')

if [[ -z "$ENV_STRING" ]]; then
    echo "❌ No env vars to set"
    exit 1
fi

echo "🔄 Updating $VAR_NAME on $SERVICE_NAME..."
gcloud run services update "$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT" \
    --set-env-vars="$ENV_STRING" \
    --quiet

echo "✅ Successfully updated $VAR_NAME"
echo ""
echo "To rollback, run:"
echo "  cat $BACKUP_FILE | jq -r '[.[] | select(.value != null) | \"\\(.name)=\\(.value)\"] | join(\",\")' | xargs gcloud run services update $SERVICE_NAME --region=$REGION --set-env-vars"
