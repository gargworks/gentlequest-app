---
description: Deploy GentleQuest to Google Cloud Run via Cloud Build
---

# Deploy GentleQuest to GCP

## Prerequisites
- `gcloud` CLI installed and authenticated
- Project configured: `gcloud config set project gen-lang-client-0894185576`
- APIs enabled: `run.googleapis.com`, `cloudbuild.googleapis.com`

## Steps

1. Navigate to project directory:
```bash
cd ~/ai-mvp-backend
```

// turbo
2. Submit build to Cloud Build:
```bash
gcloud builds submit --config=cloudbuild.yaml
```

3. Wait for build to complete (~5-10 minutes).

// turbo
4. Verify deployment:
```bash
gcloud run services list
```

5. Test the service:
```bash
curl https://gentlequest-backend-7an2ps6yna-uc.a.run.app/api/health
```

## Troubleshooting

### Permission Denied
```bash
gcloud projects add-iam-policy-binding gen-lang-client-0894185576 \
  --member="user:gargenterprises2019@gmail.com" \
  --role="roles/cloudbuild.builds.editor"
```

### API Not Enabled
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

## Links
- [Cloud Build Console](https://console.cloud.google.com/cloud-build/builds?project=gen-lang-client-0894185576)
- [Cloud Run Console](https://console.cloud.google.com/run?project=gen-lang-client-0894185576)
- [cloudbuild.yaml](/Users/lokeshgarg/ai-mvp-backend/cloudbuild.yaml)
