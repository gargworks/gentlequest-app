---
description: Deploy GentleQuest to Google Cloud Run via Cloud Build
---


# Deploy GentleQuest to GCP

## Prerequisites
- `gcloud` CLI installed and authenticated
- Project configured: `gcloud config set project gen-lang-client-0894185576`
- APIs enabled: `run.googleapis.com`, `cloudbuild.googleapis.com`

## 🚀 Scenario A: Full Deployment (Flutter + Backend)
**Use when:** You have modified Dart code (Flutter), Assets, or Web Config.

1. **Rebuild Flutter Web:**
   Must run locally to regenerate `static/` folder.
   ```bash
   cd ~/ai-mvp-backend/ai_buddy_web
   flutter clean
   flutter build web --release --base-href "/"
   ```

2. **Update Static Assets:**
   Copy the new build to the backend's static folder.
   ```bash
   cd ~/ai-mvp-backend
   rm -rf static/*
   cp -R ai_buddy_web/build/web/* static/
   ```

3. **Deploy:**
   ```bash
   gcloud builds submit --config=cloudbuild.backend.yaml
   ```

## ⚡️ Scenario B: Backend Only (Fast Path)
**Use when:** You *ONLY* modified Python code (`app.py`), Config, or Scripts.
*WARNING: This will deploy the OLD/EXISTING `static/` folder. Do not use if you changed Frontend.*

1. **Deploy Directly:**
   ```bash
   cd ~/ai-mvp-backend
   gcloud builds submit --config=cloudbuild.backend.yaml
   ```

## Verification
1. **Live Check:** [https://app.gentlequest.app](https://app.gentlequest.app)
2. **Cloud Run Console:** [Service Details](https://console.cloud.google.com/run?project=gen-lang-client-0894185576)
