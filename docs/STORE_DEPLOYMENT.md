# Store Deployment — Single Source of Truth

> **Read this first.** All credential paths and upload commands for App Store + Google Play.
> Any agent (Devin, Claude Code, Cursor, etc.) can deploy from terminal using this file.

## Credentials (all on disk, no manual steps needed)

### App Store Connect
| Item | Path |
|------|------|
| API Key | `~/.appstoreconnect/private_keys/AuthKey_L6BQY5DFKM.p8` |
| Issuer ID | `~/.appstoreconnect/issuer_id.txt` (`aa60935b-8c0a-4055-b26f-f44d84c265f7`) |
| API Key ID | `L6BQY5DFKM` |
| Team ID | `828Q2S3G4Q` |
| Bundle ID | `com.gentlequest.app` |

### Google Play Console
| Item | Path |
|------|------|
| Service Account JSON | `~/Downloads/gentlequest-prod-d698b1aa74fb.json` |
| Service Account Email | `play-store-upload@gentlequest-prod.iam.gserviceaccount.com` |
| Package Name | `app.gentlequest.www` |
| Project ID | `gentlequest-prod` |

### Other
| Item | Path / Value |
|------|------|
| Firebase Admin SA | `~/gentlequest/secret/gentlequest-prod-sa.json` |
| gcloud active account | `mailforlkgarg@gmail.com` |
| gcloud project | `gentlequest-prod` (alias: `gen-lang-client-0814369801`) |

## Build Commands

```bash
# Flutter path
export PATH="/Users/lokeshgarg/ssd_dev/flutter/bin:$PATH"
cd /Users/lokeshgarg/gentlequest/ai_buddy_web

# Android AAB
flutter build appbundle --release
# Output: build/app/outputs/bundle/release/app-release.aab

# iOS IPA (codesigned, App Store ready)
flutter build ipa --release
# Output: build/ios/ipa/ai_buddy_web.ipa
```

## Upload Commands

### iOS → App Store Connect
```bash
xcrun altool --upload-app -t ios \
  -f /Users/lokeshgarg/gentlequest/ai_buddy_web/build/ios/ipa/ai_buddy_web.ipa \
  --apiKey L6BQY5DFKM \
  --apiIssuer aa60935b-8c0a-4055-b26f-f44d84c265f7
```

### Android → Google Play (production track)
```bash
fastlane supply \
  --aab /Users/lokeshgarg/gentlequest/ai_buddy_web/build/app/outputs/bundle/release/app-release.aab \
  --package_name app.gentlequest.www \
  --track production \
  --json_key /Users/lokeshgarg/Downloads/gentlequest-prod-d698b1aa74fb.json \
  --release_status completed \
  --skip_upload_metadata --skip_upload_images --skip_upload_screenshots
```

## Version Bump

Edit `ai_buddy_web/pubspec.yaml`:
```yaml
version: 1.4.2+26062511
#              ^^^^^^^^
#              build number — MUST increment on every Play Store upload
#              (Play rejects duplicate version codes)
```

iOS uses `$(FLUTTER_BUILD_NAME)` and `$(FLUTTER_BUILD_NUMBER)` from Info.plist,
so the pubspec version flows through automatically.

## Common Errors

| Error | Fix |
|-------|-----|
| `Version code N has already been used` (Play) | Bump build number in pubspec.yaml, rebuild AAB |
| `bundle version must be higher` (App Store) | Bump build number in pubspec.yaml, rebuild IPA |
| `No signing certificate "iOS Distribution"` | Archive was built with `--no-codesign`; rebuild without that flag |
| `altool: No applicable devices found` | Ensure Xcode is installed and `xcrun` points to it |

## Blog Deployment

Blog is a Render static site — auto-deploys on git push to `main`:
```bash
cd /Users/lokeshgarg/gentlequest
git add gentlequest-blog/
git commit -m "blog: <description>"
git push origin main
# Render auto-builds from render.yaml → gentlequest-blog service
```

## Full Release Flow (copy-paste)

```bash
# 1. Bump version in pubspec.yaml
# 2. Build both
export PATH="/Users/lokeshgarg/ssd_dev/flutter/bin:$PATH"
cd /Users/lokeshgarg/gentlequest/ai_buddy_web
flutter build appbundle --release
flutter build ipa --release

# 3. Upload both
xcrun altool --upload-app -t ios \
  -f build/ios/ipa/ai_buddy_web.ipa \
  --apiKey L6BQY5DFKM \
  --apiIssuer aa60935b-8c0a-4055-b26f-f44d84c265f7

fastlane supply \
  --aab build/app/outputs/bundle/release/app-release.aab \
  --package_name app.gentlequest.www \
  --track production \
  --json_key /Users/lokeshgarg/Downloads/gentlequest-prod-d698b1aa74fb.json \
  --release_status completed \
  --skip_upload_metadata --skip_upload_images --skip_upload_screenshots

# 4. Commit + push
cd /Users/lokeshgarg/gentlequest
git add ai_buddy_web/pubspec.yaml
git commit -m "chore: bump version to X.Y.Z+BUILD"
git push origin main
```
