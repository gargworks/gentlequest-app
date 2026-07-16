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

## iOS Submit for Review (after upload)

After `xcrun altool` upload succeeds, the build is NOT submitted for review yet.
You must create a version, link the build, set release notes, and submit.

**Use the script (handles all 3 steps of the submit flow):**
```bash
python3 scripts/asc_submit_for_review.py \
  --app-id 6756537464 \
  --version-id <APP_STORE_VERSION_UUID> \
  --platform IOS
```

**Manual steps if the script fails** (see `docs/release/MANUAL_RELEASE_PLAYBOOK.md` §2.8):

1. **Create version** (if not already created):
```python
POST /v1/appStoreVersions
{"data":{"type":"appStoreVersions","attributes":{"platform":"IOS","versionString":"1.5.1"},
"relationships":{"app":{"data":{"type":"apps","id":"6756537464"}}}}}
```

2. **Link build to version** — find the build ID first:
```python
GET /v1/apps/6756537464/builds?limit=200  # find by version number matching your build
PATCH /v1/appStoreVersions/{VERSION_ID}
{"data":{"type":"appStoreVersions","id":"VERSION_ID",
"relationships":{"build":{"data":{"type":"builds","id":"BUILD_ID"}}}}}
```

3. **Set whatsNew (release notes)** — REQUIRED or submit fails with 409:
```python
GET /v1/appStoreVersions/{VERSION_ID}/appStoreVersionLocalizations  # get loc_id
PATCH /v1/appStoreVersionLocalizations/{LOC_ID}
{"data":{"type":"appStoreVersionLocalizations","id":"LOC_ID",
"attributes":{"whatsNew":"Your release notes here"}}}
```

4. **Submit for review** (3-step flow via reviewSubmissions API):
```bash
python3 scripts/asc_submit_for_review.py --app-id 6756537464 --version-id {VERSION_ID} --platform IOS
```

**IMPORTANT:** The API key does NOT have `CREATE` permission for the old
`appStoreVersionSubmissions` endpoint. Use the newer `reviewSubmissions` +
`reviewSubmissionItems` flow (which the script does). Do NOT try
`POST /v1/appStoreVersionSubmissions` — it returns 403.

**Verify submission:**
```python
GET /v1/appStoreVersions/{VERSION_ID}
# appStoreState should be WAITING_FOR_REVIEW
```

## Checking Download / Install Numbers

### Funnel endpoint (live GA4 data)
```bash
curl -s "https://gentlequest.onrender.com/api/metrics/funnel" | python3 -m json.tool
```
Returns: installs by platform (90-day + all-time), app opens, first chat count,
active users. Simulator/emulator traffic filtered out.

### GA4 analytics report (local script)
```bash
cd /Users/lokeshgarg/gentlequest
python3 scripts/analytics_dashboard.py
# Outputs: metrics/analytics_latest.json + metrics/analytics_report.md
```
Requires `GOOGLE_APPLICATION_CREDENTIALS` env var pointing to a GA4 service
account JSON. The funnel endpoint above is preferred for quick checks.

### Daily funnel snapshot log
```bash
tail -20 /Users/lokeshgarg/gentlequest/docs/strategy/stage0/backups/gate_artifacts/funnel_snapshot.latest.log
```
Launchd job hits the funnel endpoint daily at 02:30 UTC and logs install counts.

### App Store Connect status check
```bash
# Generate JWT token
TOKEN=$(python3 -c "
import jwt, time
with open('$HOME/.appstoreconnect/private_keys/AuthKey_L6BQY5DFKM.p8', 'rb') as f:
    key = f.read()
payload = {'iss':'aa60935b-8c0a-4055-b26f-f44d84c265f7','iat':int(time.time()),
'exp':int(time.time())+1200,'aud':'appstoreconnect-v1'}
header = {'kid':'L6BQY5DFKM','typ':'JWT','alg':'ES256'}
print(jwt.encode(payload, key, 'ES256', headers=header))
")

# Check version states
curl -s "https://api.appstoreconnect.apple.com/v1/apps/6756537464/appStoreVersions?limit=50" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for v in d['data']:
    a = v['attributes']
    if a.get('appStoreState') != 'READY_FOR_SALE':
        print(f'>>> v{a[\"versionString\"]} | {a[\"appStoreState\"]}')
ready = [v for v in d['data'] if v['attributes'].get('appStoreState') == 'READY_FOR_SALE']
if ready: print(f'Latest live: {ready[0][\"attributes\"][\"versionString\"]}')
"
```

### Google Play status check
```bash
TOKEN=$(python3 -c "
from google.oauth2 import service_account
import google.auth.transport.requests
creds = service_account.Credentials.from_service_account_file(
    '$HOME/Downloads/gentlequest-prod-d698b1aa74fb.json',
    scopes=['https://www.googleapis.com/auth/androidpublisher'])
req = google.auth.transport.requests.Request()
creds.refresh(req)
print(creds.token)
")

EDIT=$(curl -s -X POST "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/app.gentlequest.www/edits" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

curl -s "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/app.gentlequest.www/edits/$EDIT/tracks" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for t in d['tracks']:
    for r in t.get('releases', []):
        print(f'{t[\"track\"]}: v{r.get(\"name\",\"?\")} | {r.get(\"status\",\"?\")}')
"
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

# 4. iOS: Create version + link build + set release notes + submit for review
#    (see "iOS Submit for Review" section above — use asc_submit_for_review.py)
#    Android: fastlane supply with --release_status completed goes live immediately

# 5. Commit + push
cd /Users/lokeshgarg/gentlequest
git add ai_buddy_web/pubspec.yaml
git commit -m "chore: bump version to X.Y.Z+BUILD"
git push origin main
```
