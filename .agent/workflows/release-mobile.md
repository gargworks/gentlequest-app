---
description: Trigger the One-Button Mobile Release (Android & iOS) via GitHub Actions
---

# One-Button Mobile Release Protocol

> **⚠️ Not currently live:** GitHub Actions push/PR/cron triggers were paused 2026-08-06 (abuse review) — the automated path this workflow's script triggers does not currently run. The live path is [docs/release/MANUAL_RELEASE_PLAYBOOK.md](../../docs/release/MANUAL_RELEASE_PLAYBOOK.md). This workflow is kept for when Actions returns.

This workflow triggers the automated build and release pipeline for GentleQuest mobile apps.
It interacts with GitHub Actions to bypass local environment restrictions (signing keys, etc.).

**Prerequisites:**
- `gh` CLI installed and authenticated (`gh auth status`)
- Repository: `ai-mvp-backend`

## Usage

Run the repository-level wrapper script:

```bash
./scripts/release_mobile.sh [internal|production|dry-run] "Optional Notes"
```

### Options:
- **internal** (Default): Uploads to **Internal App Sharing** (Android) and **TestFlight** (iOS).
- **production**: Uploads to **Production Track** (Android) and **TestFlight** (iOS App Store Connect).
- **dry-run**: Triggers the workflow with `upload: false` to verify simple build success.

### Example:

```bash
# Standard internal release
./scripts/release_mobile.sh internal "Weekly Beta Release"

# Dry run verification
./scripts/release_mobile.sh dry-run
```

## Troubleshooting
- **Billing Limits:** If the workflow fails immediately, check GitHub Action minutes usage.
- **Keys:** This workflow relies on GitHub Secrets. Local key files are NOT required.
