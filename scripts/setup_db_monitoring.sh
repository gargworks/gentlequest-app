#!/bin/bash
# scripts/setup_db_monitoring.sh
# Usage: ./scripts/setup_db_monitoring.sh [EMAIL_ADDRESS]
# Description: Creates a Cloud Monitoring alert policy for DB authentication failures.

set -euo pipefail

EMAIL="${1:-gargenterprises2019@gmail.com}"
PROJECT_ID=$(gcloud config get-value project)

echo "Setting up DB Monitoring for ${PROJECT_ID} (Notify: ${EMAIL})..."

# 1. Get Notification Channel (Simplified)
# Try to find existing email channel first to avoid creation complexity
# Fix quoting for gcloud filter to avoid "ambiguous use of email" error
CHANNEL_ID=$(gcloud beta monitoring channels list --filter="type=\"email\" AND labels.email_address=\"${EMAIL}\"" --format="value(name)" --limit=1)

if [ -z "$CHANNEL_ID" ]; then
    echo "Creating new notification channel for ${EMAIL}..."
    
    # Create JSON config for robustness
    cat <<EOF > channel_config.json
{
  "type": "email",
  "displayName": "Primary Email Alert",
  "labels": {
    "email_address": "${EMAIL}"
  }
}
EOF
    
    # Create channel using the file
    # Note: Using 'alpha' or 'beta' might vary, but 'monitoring channels create' is standard.
    # We parse the output to get the name.
    CHANNEL_ID=$(gcloud beta monitoring channels create --channel-content-from-file="channel_config.json" --format="value(name)")
    
    rm channel_config.json
fi

if [ -z "$CHANNEL_ID" ]; then
    # Fallback: Just grab the first email channel if specific creation failed
    echo "Warning: Specific channel creation failed. Using first available email channel."
    CHANNEL_ID=$(gcloud beta monitoring channels list --filter='type=email' --format='value(name)' --limit=1)
fi

if [ -z "$CHANNEL_ID" ]; then
    echo "Error: No notification channel available and creation failed. Please create an email notification channel manually in Cloud Console."
    exit 1
fi

echo "Using Channel ID: ${CHANNEL_ID}"

# 2. Create Alert Policy (Log-based alert)
# Trigger if ANY log entry matches the filter in a 1-minute window
echo "Creating alert policy..."

# Define full policy in JSON
echo "Creating policy config..."
cat <<EOF > policy.json
{
  "displayName": "Critical: DB Auth Failure",
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "DB Auth Failure Log",
      "conditionMatchedLog": {
        "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"gentlequest-backend\" AND textPayload:\"FATAL: password authentication failed\""
      }
    }
  ],
  "notificationChannels": [
    "${CHANNEL_ID}"
  ],
  "alertStrategy": {
    "notificationRateLimit": {
      "period": "300s"
    }
  }
}
EOF

# Create policy from file
gcloud alpha monitoring policies create \
    --policy-from-file=policy.json

rm policy.json

echo "✅ Alert policy created."
