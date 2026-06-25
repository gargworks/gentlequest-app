# Flutter Store Deployment Kit — Setup Guide

## What you get

This kit lets any AI agent (Devin, Claude Code, Cursor, Windsurf) deploy
your Flutter app to both App Store and Google Play from terminal —
no Xcode, no Play Console web UI, no CI/CD pipeline.

## Setup (15 minutes, one-time)

### Step 1: App Store Connect API Key

1. Go to https://appstoreconnect.apple.com/access/integrations/api
2. Click "Generate API Key" (or use existing)
3. Name it "Terminal Deploy"
4. Role: "App Manager" (or "Admin")
5. Download the `.p8` file
6. Note the **Key ID** and **Issuer ID** (both shown on the page)

Save the key:
```bash
mkdir -p ~/.appstoreconnect/private_keys
cp ~/Downloads/AuthKey_XXXX.p8 ~/.appstoreconnect/private_keys/
echo "your-issuer-id-here" > ~/.appstoreconnect/issuer_id.txt
```

### Step 2: Google Play Service Account

1. Go to https://play.google.com/console/api-access
2. Under "Service Accounts" → "Create new service account"
3. Follow the link to Google Cloud Console
4. Create a service account with "Android Publisher" role
5. Download the JSON key file
6. Back in Play Console, grant the service account "Release Manager" permission

Save the key:
```bash
cp ~/Downloads/your-project-sa.json ~/Downloads/your-project-sa.json
```

### Step 3: Copy the template

1. Copy `STORE_DEPLOYMENT.md` to your Flutter project:
```bash
mkdir -p /path/to/your/flutter/project/docs
cp STORE_DEPLOYMENT.md /path/to/your/flutter/project/docs/
```

2. Edit `STORE_DEPLOYMENT.md` and replace all `YOUR_*` placeholders
   with your actual values (key ID, issuer ID, package name, paths, etc.)

### Step 4: Add the AGENTS.md pointer

Add this to your project's `AGENTS.md`, `CLAUDE.md`, or `.cursorrules`:

```markdown
## 0. Store Deployment (Read First)

All store deployment credentials and commands live in one place:
→ docs/STORE_DEPLOYMENT.md

Any agent deploying to stores should read that file first.
```

### Step 5: Test it

Tell your AI agent:
> "Read docs/STORE_DEPLOYMENT.md and deploy the current version to both stores."

The agent will:
1. Read the deployment file
2. Find the credential paths
3. Build the AAB and IPA
4. Upload to both stores
5. Commit and push the version bump

### Step 6: Install fastlane (if not already)

```bash
# Option 1: Homebrew (macOS)
brew install fastlane

# Option 2: Ruby gem
gem install fastlane

# Verify
fastlane --version
```

## Troubleshooting

### "No signing certificate iOS Distribution"

Your iOS project needs automatic signing configured:
1. Open `ios/Runner.xcworkspace` in Xcode (one last time)
2. Runner → Signing & Capabilities
3. Check "Automatically manage signing"
4. Select your team
5. Close Xcode

### "Version code N has already been used"

Google Play rejects duplicate version codes. Bump the build number
in `pubspec.yaml`:
```yaml
version: 1.0.0+1  →  version: 1.0.0+2
```

### "xcrun altool: authentication failed"

Check that:
- The `.p8` key file is at `~/.appstoreconnect/private_keys/AuthKey_XXXX.p8`
- The Key ID matches the filename
- The Issuer ID is correct (check `~/.appstoreconnect/issuer_id.txt`)

### "fastlane: Google Api Error: request failed"

Check that:
- The service account JSON path is correct
- The service account has "Release Manager" permission in Play Console
- The package name matches your app's `applicationId` in `android/app/build.gradle`

## What's included

| File | Purpose |
|------|---------|
| `STORE_DEPLOYMENT.md` | The single source of truth — credential paths, build commands, upload commands |
| `SETUP.md` | This file — step-by-step setup guide |
| `AGENTS.md.template` | Template for the agent pointer file |

## Support

- Blog post with full walkthrough: [link after publication]
- Questions: email the author
- Updates: check the Gumroad page for new versions

---

*Made by Eidetic Works — building AI agents that ship real things.*
