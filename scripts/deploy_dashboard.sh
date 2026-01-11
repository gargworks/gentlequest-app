#!/bin/bash
set -e

# Set Project ID
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="marketing-dashboard"

echo "🚀 Deploying [$SERVICE_NAME] to Cloud Run..."

# 1. Build
echo "Building Container..."
gcloud builds submit --config cloudbuild_dashboard.yaml .

# 2. Deploy
echo "Deploying Service..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080

echo "✅ Deployment Complete!"
