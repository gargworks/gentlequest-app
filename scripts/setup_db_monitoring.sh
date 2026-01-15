#!/bin/bash
# scripts/setup_db_monitoring.sh
# Usage: ./scripts/setup_db_monitoring.sh [EMAIL_ADDRESS]
# Description: Creates a Cloud Monitoring alert policy for DB authentication failures.

set -euo pipefail

EMAIL="${1:-gargenterprises2019@gmail.com}"
PROJECT_ID=$(gcloud config get-value project)

echo "Setting up DB Monitoring for ${PROJECT_ID} (Notify: ${EMAIL})..."

# 1. Create Notification Channel
echo "Creating notification channel..."
CHANNEL_ID=$(gcloud beta monitoring channels create \
    --display-name="Primary Email Alert" \
    --type=email \
    --channel-content="email_address=${EMAIL}" \
    --format="value(name)" || true)

if [ -z "$CHANNEL_ID" ]; then
    echo "Warning: Channel creation failed or returned empty. Using existing channels if any."
    # Fallback to listing first email channel
    CHANNEL_ID=$(gcloud beta monitoring channels list --filter='type=email' --format='value(name)' --limit=1)
fi

if [ -z "$CHANNEL_ID" ]; then
    echo "Error: No notification channel available. Aborting."
    exit 1
fi

echo "Using Channel ID: ${CHANNEL_ID}"

# 2. Create Alert Policy (Log-based alert)
# Trigger if ANY log entry matches the filter in a 1-minute window
echo "Creating alert policy..."

# Define condition in JSON file to avoid complex CLI escaping
cat <<EOF > policy_condition.json
{
  "displayName": "DB Auth Failure",
  "conditionMatchedLog": {
    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"gentlequest-backend\" AND textPayload:\"FATAL: password authentication failed\""
  }
}
EOF

gcloud alpha monitoring policies create \
    --display-name="Critical: DB Auth Failure" \
    --policy-from-file=policy_condition.json \
    --notification-channels="${CHANNEL_ID}" \
    --combiner=OR

rm policy_condition.json

echo "✅ Alert policy created."
