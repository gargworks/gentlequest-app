# Store Deployment — Single Source of Truth

> **Read this first.** All credential paths and upload commands for App Store + Google Play.
> Any AI agent (Devin, Claude Code, Cursor, Windsurf) can deploy from terminal using this file.

## Setup (run once)

### 1. App Store Connect

1. Go to [App Store Connect → Users and Access → Keys](https://appstoreconnect.apple.com/access/integrations/api)
2. Create a new API key with "App Manager" or "Admin" role
3. Download the `.p8` key file
4. Save it to: `~/.appstoreconnect/private_keys/AuthKey_XXXX.p8` (replace XXXX with your Key ID)
5. Save your Issuer ID (shown on the Keys page) to: `~/.appstoreconnect/issuer_id.txt`

### 2. Google Play Console

1. Go to [Google Play Console → Setup → API Access](https://play.google.com/console/api-access)
2. Create or link a service account
3. Download the JSON key file
4. Save it to: `~/Downloads/your-project-sa.json`
5. Grant the service account permission in Play Console (Admin or Release Manager)

### 3. Fill in your values below

Replace all `YOUR_*` placeholders with your actual values.

## Credentials

### App Store Connect
| Item | Value |
|------|-------|
| API Key Path | `~/.appstoreconnect/private_keys/AuthKey_YOUR_KEY_ID.p8` |
| Issuer ID | `YOUR_ISSUER_ID` (saved at `~/.appstoreconnect/issuer_id.txt`) |
| API Key ID | `YOUR_KEY_ID` |
| Team ID | `YOUR_TEAM_ID` |
| Bundle ID | `com.yourcompany.yourapp` |

### Google Play Console
| Item | Value |
|------|-------|
| Service Account JSON | `~/Downloads/your-project-sa.json` |
| Service Account Email | `your-sa@your-project.iam.gserviceaccount.com` |
| Package Name | `com.yourcompany.yourapp` |
| Project ID | `your-google-cloud-project` |

## Build Commands

```bash
# Set Flutter path (adjust to your install location)
export PATH="$HOME/flutter/bin:$PATH"

# Navigate to your Flutter project
cd /path/to/your/flutter/project

# Android AAB
flutter build appbundle --release
# Output: build/app/outputs/bundle/release/app-release.aab

# iOS IPA (codesigned, App Store ready)
flutter build ipa --release
# Output: build/ios/ipa/yourapp.ipa
```

### iOS signing setup (one-time)

Ensure your iOS project is configured for automatic signing:
1. Open `ios/Runner.xcworkspace` in Xcode
2. Select Runner → Signing & Capabilities
3. Check "Automatically manage signing"
4. Select your Development Team
5. Close Xcode (you won't need it again)

## Upload Commands

### iOS → App Store Connect
```bash
xcrun altool --upload-app -t ios \
  -f build/ios/ipa/yourapp.ipa \
  --apiKey YOUR_KEY_ID \
  --apiIssuer YOUR_ISSUER_ID
```

### Android → Google Play (production track)
```bash
fastlane supply \
  --aab build/app/outputs/bundle/release/app-release.aab \
  --package_name com.yourcompany.yourapp \
  --track production \
  --json_key ~/Downloads/your-project-sa.json \
  --release_status completed \
  --skip_upload_metadata --skip_upload_images --skip_upload_screenshots
```

### Alternative tracks (internal testing, beta, etc.)
```bash
# Change --track to: internal, alpha, beta, or production
fastlane supply \
  --aab build/app/outputs/bundle/release/app-release.aab \
  --package_name com.yourcompany.yourapp \
  --track internal \
  --json_key ~/Downloads/your-project-sa.json \
  --release_status draft \
  --skip_upload_metadata --skip_upload_images --skip_upload_screenshots
```

## Version Bump

Edit `pubspec.yaml`:
```yaml
version: 1.0.0+1
#         ^^^   ^
#         |     build number — MUST increment on every Play Store upload
#         |     (Play rejects duplicate version codes)
#         app version (what users see in the store)

# iOS uses FLUTTER_BUILD_NAME and FLUTTER_BUILD_NUMBER from Info.plist,
# so the pubspec version flows through automatically.
```

## Common Errors

| Error | Fix |
|-------|-----|
| `Version code N has already been used` (Play) | Bump build number in pubspec.yaml, rebuild AAB |
| `bundle version must be higher` (App Store) | Bump build number in pubspec.yaml, rebuild IPA |
| `No signing certificate "iOS Distribution"` | Archive was built with `--no-codesign`; rebuild without that flag |
| `altool: No applicable devices found` | Ensure Xcode is installed and `xcrun` points to it |
| `fastlane: Google Api Error: Invalid request` | Check service account JSON path and permissions in Play Console |
| `xcrun altool: authentication failed` | Check API key path, key ID, and issuer ID are all correct |

## Full Release Flow (copy-paste for AI agents)

```bash
# 1. Bump version in pubspec.yaml
# 2. Build both
export PATH="$HOME/flutter/bin:$PATH"
cd /path/to/your/flutter/project
flutter build appbundle --release
flutter build ipa --release

# 3. Upload both
xcrun altool --upload-app -t ios \
  -f build/ios/ipa/yourapp.ipa \
  --apiKey YOUR_KEY_ID \
  --apiIssuer YOUR_ISSUER_ID

fastlane supply \
  --aab build/app/outputs/bundle/release/app-release.aab \
  --package_name com.yourcompany.yourapp \
  --track production \
  --json_key ~/Downloads/your-project-sa.json \
  --release_status completed \
  --skip_upload_metadata --skip_upload_images --skip_upload_screenshots

# 4. Commit + push
git add pubspec.yaml
git commit -m "chore: bump version to X.Y.Z+BUILD"
git push origin main
```

## AGENTS.md Integration

Add this to your project's `AGENTS.md` (or `CLAUDE.md` or `.cursorrules`)
so any AI agent knows to read this file first:

```markdown
## 0. Store Deployment (Read First)

All store deployment credentials and commands live in one place:
→ docs/STORE_DEPLOYMENT.md

Any agent deploying to stores should read that file first.
Do not search for credentials across the filesystem — they are
already documented there.
```

## Security Notes

- Credentials never leave your machine
- The agent reads files that are already on disk
- No secrets are sent to any third-party API
- Upload commands use Apple's and Google's official CLI tools
- This is more secure than putting secrets in a CI/CD environment
- Add credential paths to `.gitignore` if they're inside your repo

## Requirements

- Flutter SDK installed
- Xcode (for iOS builds, macOS only)
- `fastlane` (`gem install fastlane` or `brew install fastlane`)
- `xcrun` (comes with Xcode)
- App Store Connect API key
- Google Play service account JSON
