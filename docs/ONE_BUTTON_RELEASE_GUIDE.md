# 🚀 One-Button Release: Complete Guide

> **Version:** 1.0 | **Last Updated:** January 2, 2026

This document covers the full release workflow from triggering the one-button automation to publishing on app stores.

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 1: Trigger One-Button Release](#phase-1-trigger-one-button-release)
3. [Phase 2: Store Promotion](#phase-2-store-promotion)
   - [For AI Agent (Browser Automation)](#for-ai-agent-browser-automation)
   - [For Humans (Manual Steps)](#for-humans-manual-steps)
4. [Troubleshooting](#troubleshooting)
5. [Secrets & Configuration](#secrets--configuration)

---

## Overview

The release pipeline has two phases:

| Phase | What Happens | Who Does It |
|-------|-------------|-------------|
| **Phase 1** | Build, sign, upload to testing tracks | ✅ Fully Automated (GitHub Actions) |
| **Phase 2** | Promote from testing to production | 🤖 Agent OR 👤 Human |

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  One-Button     │ ──> │  Internal Test   │ ──> │   Production    │
│  Release        │     │  (Auto-uploaded) │     │   (Promotion)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
     Phase 1                 Phase 1                  Phase 2
   (Automated)            (Automated)         (Agent or Human)
```

---

## Phase 1: Trigger One-Button Release

### Option A: Command Line (Recommended)

```bash
# Full release to both platforms with upload
gh workflow run release_one_button.yml \
  --ref main \
  -f build_number="<BUILD_NUMBER>" \
  -f release_notes="v1.x.x - <RELEASE_NOTES>" \
  -f 'android_params={"track":"internal","upload":"true"}' \
  -f 'ios_params={"upload":"true"}' \
  -f 'release_params={"create_gh_release":"true"}'
```

### Option B: GitHub UI

1. Go to: `Actions` → `One-Button Release (Beta)`
2. Click `Run workflow`
3. Fill in parameters:
   - **build_number**: Increment from last (check Play Console)
   - **release_notes**: What's new in this version
   - **android_params**: `{"track":"internal","upload":"true"}`
   - **ios_params**: `{"upload":"true"}`

### What Gets Created

| Artifact | Location |
|----------|----------|
| Android AAB | Google Play Internal Track |
| iOS IPA | TestFlight |
| GitHub Release | Releases page with tag |
| Build artifacts | Actions artifacts (90 day retention) |

---

## Phase 2: Store Promotion

### For AI Agent (Browser Automation)

Use this prompt with the browser agent to promote to production:

#### Google Play Promotion

```
Promote the GentleQuest app from Internal Testing to Production.

Steps:
1. Navigate to: https://play.google.com/console/u/0/developers/5873334186320541231/app/4972169396011657469/tracks/internal-testing
2. Find the latest release (check build number matches what was just uploaded)
3. Click "Promote release" dropdown
4. Select "Production" as target track
5. Set rollout percentage to 100%
6. Click through the wizard, adding release notes if prompted
7. Click "Start rollout to Production"
8. If there are policy warnings, click "Proceed anyway" (unless critical)
9. Go to Publishing overview and click "Send for review"
10. Confirm the submission

Return the final status (In Review, Published, or any errors).
```

#### App Store (TestFlight → App Review)

```
Submit the GentleQuest iOS app from TestFlight to App Store review.

Steps:
1. Navigate to: https://appstoreconnect.apple.com/apps
2. Select GentleQuest app
3. Go to the latest build in TestFlight
4. Click "Submit for Review" or navigate to App Store → version
5. Fill in any required information (What's New, etc.)
6. Select the build from TestFlight
7. Submit for Apple review

Return the final status.
```

---

### For Humans (Manual Steps)

#### 🤖 Android: Google Play Console

**URL:** https://play.google.com/console

1. **Navigate to App**
   - Select "GentleQuest" from app list
   - Go to `Release` → `Testing` → `Internal testing`

2. **Verify Build**
   - Check the latest release shows correct version/build number
   - Verify release notes are correct

3. **Promote to Production**
   - Click dropdown arrow next to "Promote release"
   - Select "Production"
   
4. **Configure Rollout**
   - Review the promotion wizard
   - Set rollout percentage (recommend 100% for small apps, 10% staged for large)
   - Add/verify release notes under "What's new"

5. **Handle Warnings**
   - If policy warnings appear (like privacy policy):
     - Fix if critical
     - Click "Proceed anyway" if non-blocking

6. **Submit for Review**
   - Go to `Publishing overview`
   - Click "Send changes for review"
   - Confirm in dialog

7. **Monitor**
   - Status will show "In review"
   - Typically approved within 1-3 days
   - Once approved, changes go live automatically

---

#### 🍎 iOS: App Store Connect

**URL:** https://appstoreconnect.apple.com

1. **Navigate to App**
   - Select "GentleQuest" from app list
   - Go to `TestFlight` tab

2. **Verify Build**
   - Check latest build is present (green dot = ready)
   - Note the build number for reference

3. **Prepare for Submission**
   - Go to `App Store` tab
   - Click the version (e.g., "1.2.0 Prepare for Submission")
   - Or click `+` to create new version

4. **Fill Required Info**
   - **What's New:** Enter release notes
   - **Build:** Select the TestFlight build
   - **Screenshots:** Verify all sizes present
   - **Description:** Update if needed

5. **Submit for Review**
   - Click "Add for Review" (top right)
   - Review all sections show green checkmarks
   - Click "Submit to App Review"

6. **Answer Questions**
   - Export compliance (typically "No" for standard apps)
   - Advertising identifier (if applicable)
   - Content rights

7. **Monitor**
   - Status changes to "Waiting for Review"
   - Typically reviewed within 24-48 hours
   - May get questions from reviewer

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Version code conflict** | Use a higher build_number than existing |
| **Privacy policy 404** | Deploy the `/privacy` route to production |
| **Signing failed** | Check GitHub secrets are set correctly |
| **Upload failed** | Verify `PLAY_SERVICE_ACCOUNT_JSON` secret |
| **iOS signing failed** | Check Apple certificates haven't expired |

### Build Number Best Practices

- Always increment from the highest existing build on any track
- Use a high starting number (e.g., 100+) to avoid conflicts
- Check Play Console for current highest: `Release` → `App bundle explorer`

### Policy Warnings

**Privacy Policy URL:** Must be accessible. Currently configured as:
- `https://www.gentlequest.app/privacy`
- Fallback: `https://gentlequest.onrender.com/privacy`

---

## Secrets & Configuration

### Required GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `ANDROID_KEYSTORE_BASE64` | Base64-encoded upload keystore |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_ALIAS` | Key alias in keystore |
| `ANDROID_KEY_PASSWORD` | Key password |
| `PLAY_SERVICE_ACCOUNT_JSON` | Google Play API service account JSON |
| `APP_STORE_CONNECT_API_KEY_ID` | Apple API key ID (optional) |
| `APP_STORE_CONNECT_ISSUER_ID` | Apple issuer ID (optional) |
| `APP_STORE_CONNECT_API_PRIVATE_KEY` | Apple API private key (optional) |

### Workflow Files

| File | Purpose |
|------|---------|
| `.github/workflows/release_one_button.yml` | Main orchestrator |
| `.github/workflows/android_release.yml` | Android build + Play upload |
| `.github/workflows/ios_release.yml` | iOS build + TestFlight upload |

---

## Quick Reference Card

```
╔════════════════════════════════════════════════════════════╗
║                  ONE-BUTTON RELEASE                        ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  1. TRIGGER RELEASE                                        ║
║     gh workflow run release_one_button.yml \               ║
║       -f build_number="102" \                              ║
║       -f 'android_params={"track":"internal","upload":"true"}' ║
║       -f 'ios_params={"upload":"true"}'                    ║
║                                                            ║
║  2. WAIT ~10 MINUTES                                       ║
║     Check: gh run list --workflow="release_one_button.yml" ║
║                                                            ║
║  3. PROMOTE TO PRODUCTION                                  ║
║     Android: Play Console → Internal → Promote → Production║
║     iOS: App Store Connect → TestFlight → Submit for Review║
║                                                            ║
║  4. MONITOR REVIEW                                         ║
║     Android: 1-3 days                                      ║
║     iOS: 24-48 hours                                       ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

*Documentation generated: January 2, 2026*
*Maintained by: GentleQuest Engineering*
