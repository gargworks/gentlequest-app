#!/bin/bash

# Define Protocol Mode
MODE="verify_truth"

echo "☁️  Initiating Cloud Truth Verification..."
echo "🚀 Destination: Google Cloud Run (The Sovereign Container)"
echo "📜 Protocol: .brain/knowledge/ANTI_HALLUCINATION_PROTOCOL.md"
echo "---------------------------------------------------"

# Check if gcloud is authenticated
gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: Not authenticated with gcloud. Run 'gcloud auth login' first."
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
echo "🌍 Project: $PROJECT_ID"

# Determine Proposition
PROPOSITION="${1:-CLOUD_AUDIT_REQUEST}"
echo "🔎 Subject: '$PROPOSITION'"

echo "📦 Submitting Cloud Execution Job..."

gcloud builds submit --config deploy/cloudbuild_audit.yaml \
    --substitutions=_MODE="$MODE",_PROPOSITION="$PROPOSITION"

echo "---------------------------------------------------"
echo "✅ Cloud Audit Submitted. Check the link above for logs."
