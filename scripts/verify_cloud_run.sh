#!/bin/bash
# scripts/verify_cloud_run.sh
# Post-deployment verification for Nucleus on Cloud Run

set -e

SERVICE_NAME="nucleus-sovereign"
REGION="us-central1"

echo "🔍 Verifying Nucleus on Cloud Run..."

# Get Service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)' 2>/dev/null || echo "")

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Service '$SERVICE_NAME' not found in region '$REGION'."
    echo "   Hint: Run 'gcloud builds submit --config deploy/cloudbuild.yaml .' first."
    exit 1
fi

echo "📍 Service URL: $SERVICE_URL"
echo ""

# 1. Health Check
echo "--- [1/3] Health Check ---"
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/api/health" || echo '{"error": "curl failed"}')
echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
echo ""

# 2. HUD Status (Agent Liveness)
echo "--- [2/3] HUD Status ---"
STATUS_RESPONSE=$(curl -s "$SERVICE_URL/api/status" || echo '{"error": "curl failed"}')
echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
echo ""

# 3. Simple Latency Test
echo "--- [3/3] Latency Test ---"
START_TIME=$(python3 -c 'import time; print(int(time.time() * 1000))')
curl -s -o /dev/null "$SERVICE_URL/api/health"
END_TIME=$(python3 -c 'import time; print(int(time.time() * 1000))')
LATENCY=$((END_TIME - START_TIME))
echo "Latency: ${LATENCY}ms"
echo ""

echo "✅ Verification Complete."
