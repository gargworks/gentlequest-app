#!/bin/bash
# Deploy Nucleus Builder as a Cloud Run Job

PROJECT_ID="gen-lang-client-0894185576"
REGION="us-central1"
IMAGE="us-central1-docker.pkg.dev/gen-lang-client-0894185576/nucleus-artifacts/nucleus-builder"
JOB_NAME="nucleus-builder"

echo "🚀 Deploying [$JOB_NAME] using image [$IMAGE]..."

# Create or Update the Job
# We omit service-account to use the default Compute Engine SA (which usually has Editor/Owner in dev projects, or at least Vertex Access)
# If stricter security is needed, we will create a dedicated SA later.

gcloud run jobs create $JOB_NAME \
  --image $IMAGE \
  --region $REGION \
  --project $PROJECT_ID \
  --set-env-vars FORCE_VERTEX=1,PYTHONUNBUFFERED=1,NUCLEUS_STORAGE_TYPE=firestore \
  --max-retries 0 \
  --task-timeout 60m \
  2>/dev/null || \
gcloud run jobs update $JOB_NAME \
  --image $IMAGE \
  --region $REGION \
  --project $PROJECT_ID \
  --set-env-vars FORCE_VERTEX=1,PYTHONUNBUFFERED=1,NUCLEUS_STORAGE_TYPE=firestore \
  --task-timeout 60m

echo "✅ Deployment logic executed."
echo "To run the swarm manually:"
echo "gcloud run jobs execute $JOB_NAME --region $REGION --project $PROJECT_ID"
