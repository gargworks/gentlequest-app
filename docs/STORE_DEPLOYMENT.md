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
| App ID | `6756537464` |

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

### Flutter SDK
| Item | Path |
|------|------|
| Flutter binary | `/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin/flutter` |
| Symlink | `~/ssd_dev/flutter/bin/flutter` (symlinks to SSD) |

> **WARNING:** Flutter is on an external SSD. If `flutter` command fails with
> "No such file or directory", the SSD is not mounted. Ask the user to mount it.
> Do NOT try to install Flutter via Homebrew — the project depends on the exact
> version on the SSD.

### iOS Signing Assets
| Item | Location |
|------|----------|
| Distribution cert | Keychain: `Apple Distribution: Lokesh Kumar Garg (828Q2S3G4Q)` |
| Cert SHA-1 | `7672A7A08EC2B97B93C35A8A843D1A2DEE93E591` |
| App Store provisioning profile | `~/Library/MobileDevice/Provisioning Profiles/251fc563-82c5-45cf-94f9-b7d0701ee56d.mobileprovision` |
| Profile name | `GentleQuest-AppStore-Prod` |
| Entitlements file | `ai_buddy_web/ios/Runner/Runner.entitlements` |

---

## End-to-End Release Playbook (verified 2026-08-04)

This section documents the EXACT steps that worked on 2026-08-04 to deploy
v1.5.2 to both stores from a terminal-only environment (no Xcode GUI).
Follow these steps in order. Each step has a copy-paste command.

### Step 0: Prerequisites Check

```bash
# 1. Check Flutter SDK is accessible (SSD must be mounted)
ls "/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin/flutter" 2>/dev/null \
  && echo "Flutter OK" || echo "SSD NOT MOUNTED — ask user to mount it"

# 2. Check signing assets
security find-identity -v -p codesigning 2>/dev/null | grep "Apple Distribution" \
  && echo "Distribution cert OK" || echo "MISSING distribution cert"

ls ~/Library/MobileDevice/Provisioning\ Profiles/251fc563-82c5-45cf-94f9-b7d0701ee56d.mobileprovision \
  2>/dev/null && echo "Provisioning profile OK" || echo "MISSING provisioning profile"

# 3. Check Play Store service account JSON
ls ~/Downloads/gentlequest-prod-d698b1aa74fb.json 2>/dev/null \
  && echo "Play SA OK" || echo "MISSING Play Store service account JSON"

# 4. Check App Store Connect API key
ls ~/.appstoreconnect/private_keys/AuthKey_L6BQY5DFKM.p8 2>/dev/null \
  && echo "ASC API key OK" || echo "MISSING ASC API key"
# Also check alternate location
ls ~/Downloads/AuthKey_L6BQY5DFKM.p8 2>/dev/null \
  && echo "ASC API key found in Downloads" || true
```

### Step 1: Bump Version

Edit `ai_buddy_web/pubspec.yaml`:
```yaml
version: 1.5.2+26080402
#              ^^^^^^^^
#              build number — MUST increment on EVERY upload
#              Format: YYMMDDNN (YY=year, MM=month, DD=day, NN=sequence)
```

**Rules:**
- Play Store rejects duplicate version codes → always increment
- App Store rejects uploads to a "closed" train → if you get
  "Invalid Pre-Release Train. The train version 'X.Y.Z' is closed",
  bump the marketing version (e.g., 1.5.1 → 1.5.2)
- iOS uses `$(FLUTTER_BUILD_NAME)` and `$(FLUTTER_BUILD_NUMBER)` from
  Info.plist, which flow through from pubspec automatically

### Step 2: Build Android AAB

```bash
export PATH="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin:$PATH"
cd /Users/lokeshgarg/gentlequest/ai_buddy_web

flutter build appbundle --release
# Output: build/app/outputs/bundle/release/app-release.aab (~87MB)
# Time: ~2-7 min depending on cache state
```

**If build fails:** Check that the SSD is mounted and Flutter is in PATH.

### Step 3: Upload Android AAB to Google Play

```bash
fastlane supply \
  --aab /Users/lokeshgarg/gentlequest/ai_buddy_web/build/app/outputs/bundle/release/app-release.aab \
  --package_name app.gentlequest.www \
  --track production \
  --json_key /Users/lokeshgarg/Downloads/gentlequest-prod-d698b1aa74fb.json \
  --release_status completed \
  --skip_upload_metadata --skip_upload_images --skip_upload_screenshots
```

**Success looks like:** `Successfully finished the upload to Google Play`
**Android goes live immediately** with `--release_status completed` (no review needed).

**Common errors:**
| Error | Fix |
|-------|-----|
| `Version code N has already been used` | Bump build number in pubspec.yaml, rebuild AAB |
| `fastlane update available` notice | Ignore — it's just a changelog printout, not an error |

### Step 4: Build iOS (no-codesign + manual signing)

> **CRITICAL:** `flutter build ipa --release` FAILS in a terminal-only environment
> because Xcode automatic signing requires an Apple ID account configured in
> Xcode GUI. The workaround is to build with `--no-codesign` and then manually
> codesign the app + all frameworks.

```bash
export PATH="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin:$PATH"
cd /Users/lokeshgarg/gentlequest/ai_buddy_web

# Build without codesigning
flutter build ios --release --no-codesign
# Output: build/ios/iphoneos/Runner.app (~66MB)
# Time: ~1-3 min
```

### Step 5: Manual iOS Codesigning (the hard part)

> **Why this is needed:** Flutter's `flutter build ipa` relies on Xcode automatic
> signing, which needs an interactive Apple ID session. In a terminal-only
> environment (SSH, CI, or no Xcode GUI), this fails. The workaround is to
> build the .app without signing, then manually sign everything with the
> distribution certificate and embed the provisioning profile.

#### 5a: Embed provisioning profile

```bash
APP_PATH="/Users/lokeshgarg/gentlequest/ai_buddy_web/build/ios/iphoneos/Runner.app"
PROFILE=~/Library/MobileDevice/Provisioning\ Profiles/251fc563-82c5-45cf-94f9-b7d0701ee56d.mobileprovision

cp "$PROFILE" "$APP_PATH/embedded.mobileprovision"
```

#### 5b: Create entitlements file with application-identifier

> **CRITICAL:** The default `Runner.entitlements` in the repo does NOT include
> `application-identifier` or `team-identifier`. Without these, Apple rejects
> the upload with error 90075: "The application-identifier entitlement is missing."

```bash
cat > /tmp/gq_runner.entitlements << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>application-identifier</key>
    <string>828Q2S3G4Q.com.gentlequest.app</string>
    <key>com.apple.developer.associated-domains</key>
    <array>
        <string>applinks:gentlequest.app</string>
        <string>applinks:www.gentlequest.app</string>
        <string>applinks:app.gentlequest.app</string>
        <string>webcredentials:gentlequest.app</string>
    </array>
    <key>com.apple.developer.team-identifier</key>
    <string>828Q2S3G4Q</string>
    <key>get-task-allow</key>
    <false/>
</dict>
</plist>
PLIST
```

#### 5c: Sign all frameworks

> **CRITICAL:** Every `.framework` inside `Runner.app/Frameworks/` must be
> individually signed. If any framework is unsigned, Apple rejects with
> error 90034: "Missing or invalid signature."

```bash
CERT="7672A7A08EC2B97B93C35A8A843D1A2DEE93E591"
APP_PATH="/Users/lokeshgarg/gentlequest/ai_buddy_web/build/ios/iphoneos/Runner.app"

find "$APP_PATH/Frameworks" -name "*.framework" -type d | while read fw; do
    /usr/bin/codesign --force --sign "$CERT" --timestamp=none "$fw"
done
```

#### 5d: Sign the main app bundle

```bash
CERT="7672A7A08EC2B97B93C35A8A843D1A2DEE93E591"
APP_PATH="/Users/lokeshgarg/gentlequest/ai_buddy_web/build/ios/iphoneos/Runner.app"

/usr/bin/codesign --force --sign "$CERT" \
    --entitlements /tmp/gq_runner.entitlements \
    --timestamp=none "$APP_PATH"
```

#### 5e: Verify signing

```bash
APP_PATH="/Users/lokeshgarg/gentlequest/ai_buddy_web/build/ios/iphoneos/Runner.app"

# Verify signature is valid
codesign -vvv "$APP_PATH"
# Should output: "valid on disk" + "satisfies its Designated Requirement"

# Verify entitlements include application-identifier
codesign -d --entitlements - "$APP_PATH" 2>&1 | grep "application-identifier"
# Should output: [Key] application-identifier
```

### Step 6: Package IPA

> **CRITICAL:** The IPA must be a ZIP file with a `Payload/` directory at the
> root containing `Runner.app`. Using `ditto` directly on the Payload directory
> does NOT create the correct structure. Use Python's zipfile module instead.

```bash
IPA_DIR="/Users/lokeshgarg/gentlequest/ai_buddy_web/build/ios/ipa"
APP_PATH="/Users/lokeshgarg/gentlequest/ai_buddy_web/build/ios/iphoneos/Runner.app"

rm -rf "$IPA_DIR/Payload"
mkdir -p "$IPA_DIR/Payload"
cp -r "$APP_PATH" "$IPA_DIR/Payload/"
rm -f "$IPA_DIR/ai_buddy_web.ipa"

/usr/bin/python3 -c "
import zipfile, os
ipa_path = '$IPA_DIR/ai_buddy_web.ipa'
payload_dir = '$IPA_DIR/Payload'
with zipfile.ZipFile(ipa_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(payload_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, os.path.dirname(payload_dir))
            zf.write(file_path, arcname)
print(f'IPA created: {os.path.getsize(ipa_path)} bytes')
"

# Verify IPA structure
unzip -l "$IPA_DIR/ai_buddy_web.ipa" | grep "Payload/Runner.app/Info.plist"
# Should show: Payload/Runner.app/Info.plist
```

### Step 7: Upload IPA to App Store Connect

```bash
xcrun altool --upload-app -t ios \
  -f /Users/lokeshgarg/gentlequest/ai_buddy_web/build/ios/ipa/ai_buddy_web.ipa \
  --apiKey L6BQY5DFKM \
  --apiIssuer aa60935b-8c0a-4055-b26f-f44d84c265f7
```

**Success looks like:**
```
UPLOAD SUCCEEDED with no errors
Delivery UUID: xxxx-xxxx-xxxx
Transferred NNNNNNNN bytes in X.XXX seconds
```

**Common errors:**
| Error | Code | Fix |
|-------|------|-----|
| `Missing Provisioning Profile` | 90174 | Step 5a: embed provisioning profile |
| `Missing or invalid signature ... App.framework` | 90034 | Step 5c: sign ALL frameworks |
| `application-identifier entitlement is missing` | 90075 | Step 5b: create entitlements with application-identifier |
| `Invalid Pre-Release Train ... version X.Y.Z is closed` | 90186 | Bump marketing version (e.g., 1.5.1 → 1.5.2) |
| `IPA does not include a Payload directory` | 90072 | Step 6: use Python zipfile, not ditto |

### Step 8: Verify Uploads

#### Android status check (via Google Play Developer API)

```bash
/opt/homebrew/bin/python3 << 'PYEOF'
import json, urllib.request, urllib.parse, base64, time

with open("/Users/lokeshgarg/Downloads/gentlequest-prod-d698b1aa74fb.json") as f:
    key_data = json.load(f)

header = {"alg": "RS256", "typ": "JWT", "kid": key_data["private_key_id"]}
payload = {
    "iss": key_data["client_email"],
    "scope": "https://www.googleapis.com/auth/androidpublisher",
    "aud": "https://oauth2.googleapis.com/token",
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600,
}
header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
signing_input = f"{header_b64}.{payload_b64}".encode()

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
private_key = serialization.load_pem_private_key(key_data["private_key"].encode(), password=None)
signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
jwt_token = f"{header_b64}.{payload_b64}.{sig_b64}"

token_data = urllib.parse.urlencode({
    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
    "assertion": jwt_token,
}).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token",
    data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
with urllib.request.urlopen(req, timeout=15) as resp:
    access_token = json.loads(resp.read().decode())["access_token"]

req = urllib.request.Request(
    "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/app.gentlequest.www/edits",
    method="POST", headers={"Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"}, data=b"{}")
with urllib.request.urlopen(req, timeout=15) as resp:
    edit_id = json.loads(resp.read().decode())["id"]

req = urllib.request.Request(
    f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/app.gentlequest.www/edits/{edit_id}/tracks/production",
    headers={"Authorization": f"Bearer {access_token}"})
with urllib.request.urlopen(req, timeout=15) as resp:
    track_data = json.loads(resp.read().decode())
    for r in track_data.get("releases", []):
        print(f"Status: {r.get('status')}")
        print(f"Version codes: {r.get('versionCodes')}")
PYEOF
```

**Expected output:** `Status: completed` with your version code.

#### iOS status check (via altool)

```bash
xcrun altool --list-apps \
  --apiKey L6BQY5DFKM \
  --apiIssuer aa60935b-8c0a-4055-b26f-f44d84c265f7 \
  2>&1 | grep -E "Version|State" | head -20
```

**Note:** The build takes 15-60 minutes to process after upload before it
appears in `--list-apps`. If you see `ENTITY_ERROR.ATTRIBUTE.INVALID.DUPLICATE`
when running `--validate-app`, that means the build IS in Apple's system and
is processing — just wait.

You can also verify the build is accepted by validating:
```bash
xcrun altool --validate-app -t ios \
  -f /Users/lokeshgarg/gentlequest/ai_buddy_web/build/ios/ipa/ai_buddy_web.ipa \
  --apiKey L6BQY5DFKM \
  --apiIssuer aa60935b-8c0a-4055-b26f-f44d84c265f7
# "DUPLICATE" error = build is already uploaded and processing (good)
```

### Step 9: iOS Submit for Review (after processing completes)

> After `xcrun altool` upload succeeds, the build is NOT submitted for review yet.
> Wait for processing to complete (15-60 min), then submit via the script.

```bash
# Check if build is done processing
xcrun altool --list-apps \
  --apiKey L6BQY5DFKM \
  --apiIssuer aa60935b-8c0a-4055-b26f-f44d84c265f7 \
  2>&1 | grep "1.5.2"
# If no output, build is still processing. Wait and retry.

# Once the version appears, submit for review:
python3 scripts/asc_submit_for_review.py \
  --app-id 6756537464 \
  --version-id <APP_STORE_VERSION_UUID> \
  --platform IOS
```

**Manual steps if the script fails** (see `docs/release/MANUAL_RELEASE_PLAYBOOK.md` §2.8):

1. **Create version** (if not already created):
```python
POST /v1/appStoreVersions
{"data":{"type":"appStoreVersions","attributes":{"platform":"IOS","versionString":"1.5.2"},
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

### Step 10: Commit + Push Version Bump

```bash
git -C /Users/lokeshgarg/gentlequest add ai_buddy_web/pubspec.yaml
git -C /Users/lokeshgarg/gentlequest commit -m "release: vX.Y.Z+BUILD — <description>

Co-Authored-By: Devin <158243242+devin-ai-integration[bot]@users.noreply.github.com>"
git -C /Users/lokeshgarg/gentlequest push
```

---

## Full Automated Release Script (copy-paste)

> This is the complete end-to-end script that was verified on 2026-08-04.
> Copy this into a shell script and run it. It handles everything except
> the iOS submit-for-review step (which requires the build to finish processing).

```bash
#!/bin/bash
set -e

# === CONFIG ===
FLUTTER="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin/flutter"
GQ_DIR="/Users/lokeshgarg/gentlequest/ai_buddy_web"
CERT="7672A7A08EC2B97B93C35A8A843D1A2DEE93E591"
PROFILE_UUID="251fc563-82c5-45cf-94f9-b7d0701ee56d"
ASC_KEY="L6BQY5DFKM"
ASC_ISSUER="aa60935b-8c0a-4055-b26f-f44d84c265f7"
PLAY_JSON="/Users/lokeshgarg/Downloads/gentlequest-prod-d698b1aa74fb.json"
PACKAGE="app.gentlequest.www"

# === STEP 1: Bump version (edit pubspec.yaml manually before running) ===
echo "Current version:"
grep "^version:" "$GQ_DIR/pubspec.yaml"

# === STEP 2: Build Android AAB ===
echo "Building Android AAB..."
export PATH="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin:$PATH"
cd "$GQ_DIR"
flutter build appbundle --release
echo "AAB built: $(ls -la build/app/outputs/bundle/release/app-release.aab | awk '{print $5}') bytes"

# === STEP 3: Upload Android to Play Store ===
echo "Uploading to Google Play..."
fastlane supply \
  --aab build/app/outputs/bundle/release/app-release.aab \
  --package_name $PACKAGE \
  --track production \
  --json_key "$PLAY_JSON" \
  --release_status completed \
  --skip_upload_metadata --skip_upload_images --skip_upload_screenshots
echo "Android upload complete"

# === STEP 4: Build iOS (no-codesign) ===
echo "Building iOS (no-codesign)..."
flutter build ios --release --no-codesign

# === STEP 5: Manual codesigning ===
APP_PATH="$GQ_DIR/build/ios/iphoneos/Runner.app"
PROFILE=~/Library/MobileDevice/Provisioning\ Profiles/${PROFILE_UUID}.mobileprovision

echo "Embedding provisioning profile..."
cp "$PROFILE" "$APP_PATH/embedded.mobileprovision"

echo "Creating entitlements..."
cat > /tmp/gq_runner.entitlements << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>application-identifier</key>
    <string>828Q2S3G4Q.com.gentlequest.app</string>
    <key>com.apple.developer.associated-domains</key>
    <array>
        <string>applinks:gentlequest.app</string>
        <string>applinks:www.gentlequest.app</string>
        <string>applinks:app.gentlequest.app</string>
        <string>webcredentials:gentlequest.app</string>
    </array>
    <key>com.apple.developer.team-identifier</key>
    <string>828Q2S3G4Q</string>
    <key>get-task-allow</key>
    <false/>
</dict>
</plist>
PLIST

echo "Signing frameworks..."
find "$APP_PATH/Frameworks" -name "*.framework" -type d | while read fw; do
    /usr/bin/codesign --force --sign "$CERT" --timestamp=none "$fw"
done

echo "Signing main app..."
/usr/bin/codesign --force --sign "$CERT" \
    --entitlements /tmp/gq_runner.entitlements \
    --timestamp=none "$APP_PATH"

echo "Verifying signature..."
codesign -vvv "$APP_PATH"

# === STEP 6: Package IPA ===
echo "Creating IPA..."
IPA_DIR="$GQ_DIR/build/ios/ipa"
rm -rf "$IPA_DIR/Payload"
mkdir -p "$IPA_DIR/Payload"
cp -r "$APP_PATH" "$IPA_DIR/Payload/"
rm -f "$IPA_DIR/ai_buddy_web.ipa"
/usr/bin/python3 -c "
import zipfile, os
ipa_path = '$IPA_DIR/ai_buddy_web.ipa'
payload_dir = '$IPA_DIR/Payload'
with zipfile.ZipFile(ipa_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(payload_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, os.path.dirname(payload_dir))
            zf.write(file_path, arcname)
print(f'IPA created: {os.path.getsize(ipa_path)} bytes')
"

# === STEP 7: Upload IPA to App Store ===
echo "Uploading to App Store Connect..."
xcrun altool --upload-app -t ios \
  -f "$IPA_DIR/ai_buddy_web.ipa" \
  --apiKey $ASC_KEY \
  --apiIssuer $ASC_ISSUER

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo "Android: LIVE on Play Store (no review needed)"
echo "iOS: Uploaded, processing (15-60 min). Check App Store Connect."
echo "Next step: Submit iOS for review after processing completes."
```

---

## Blog Deployment

Blog is a Render static site — auto-deploys on git push to `main`:
```bash
cd /Users/lokeshgarg/gentlequest
git add gentlequest-blog/
git commit -m "blog: <description>"
git push origin main
# Render auto-builds from render.yaml → gentlequest-blog service
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

---

## Troubleshooting (Real Issues Encountered 2026-08-04)

### Issue 1: Flutter SDK not found
**Symptom:** `flutter: No such file or directory`
**Cause:** Flutter is on an external SSD that isn't mounted.
**Fix:** Ask user to mount the Samsung SSD 990 PRO. Verify:
```bash
ls "/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin/flutter"
```

### Issue 2: iOS build fails with "No signing certificate iOS Development"
**Symptom:** `Error (Xcode): No signing certificate "iOS Development" found`
**Cause:** Xcode automatic signing needs an Apple ID account in Xcode GUI.
**Fix:** Build with `--no-codesign` and manually sign (see Steps 4-5 above).

### Issue 3: iOS build fails with "conflicting provisioning settings"
**Symptom:** `Runner is automatically signed for development, but a conflicting
code signing identity iPhone Distribution has been manually specified`
**Cause:** The Xcode project uses `CODE_SIGN_STYLE = Automatic` which requires
an interactive Apple ID session. You can't override it from the command line.
**Fix:** Use `flutter build ios --release --no-codesign` + manual codesigning.

### Issue 4: App Store rejects with "Missing Provisioning Profile" (90174)
**Symptom:** `Apps must contain a provisioning profile in a file named
embedded.mobileprovision`
**Cause:** The provisioning profile wasn't embedded in the .app bundle.
**Fix:** Step 5a — copy the .mobileprovision file into Runner.app.

### Issue 5: App Store rejects with "Missing or invalid signature" (90034)
**Symptom:** `The bundle 'io.flutter.flutter.app' at bundle path
'Payload/Runner.app/Frameworks/App.framework' is not signed`
**Cause:** Frameworks inside the app bundle weren't individually signed.
**Fix:** Step 5c — sign every .framework in Runner.app/Frameworks/.

### Issue 6: App Store rejects with "application-identifier entitlement missing" (90075)
**Symptom:** `The application-identifier entitlement is missing; it should
contain your 10-character Apple Developer ID, followed by a dot, followed by
your bundle identifier`
**Cause:** The default Runner.entitlements file doesn't include
`application-identifier` or `team-identifier`.
**Fix:** Step 5b — create a custom entitlements file with
`application-identifier: 828Q2S3G4Q.com.gentlequest.app` and pass it to
codesign with `--entitlements`.

### Issue 7: App Store rejects with "Invalid Pre-Release Train" (90186)
**Symptom:** `The train version '1.5.1' is closed for new build submissions`
**Cause:** You already submitted version 1.5.1 for review and Apple closed
the train. You can't upload more builds to that version.
**Fix:** Bump the marketing version (e.g., 1.5.1 → 1.5.2) in pubspec.yaml.

### Issue 8: App Store rejects with "IPA does not include Payload directory" (90072)
**Symptom:** `The IPA is invalid. It does not include a Payload directory.`
**Cause:** The ZIP file was created incorrectly (e.g., using `ditto` on the
Payload directory instead of its parent).
**Fix:** Step 6 — use Python's zipfile module to create the IPA with
`Payload/Runner.app/...` as the archive path structure.

### Issue 9: Play Store rejects with "Version code already used"
**Symptom:** `Google Api Error: Invalid request - Version code N has already
been used`
**Cause:** The build number in pubspec.yaml matches a previously uploaded build.
**Fix:** Bump the build number in pubspec.yaml (e.g., 26080401 → 26080402),
rebuild the AAB, and re-upload.

### Issue 10: Build not appearing in `altool --list-apps` after upload
**Symptom:** Upload succeeded but version doesn't show in list-apps.
**Cause:** Apple is still processing the binary (15-60 minutes typical).
**Fix:** Wait. Verify the build is in Apple's system by running
`xcrun altool --validate-app` — if it returns `DUPLICATE`, the build was
received and is processing.

---

## Blog Deployment (Cloudflare Pages)

> **CRITICAL:** The blog at `gentlequest.app/blog/` is served from **Cloudflare Pages**,
> NOT from the Render static site. The Render static site (`gentlequest-blog.onrender.com`)
> is a red herring — the domain `gentlequest.app` is a CNAME to `gentlequest-www.pages.dev`.

### Architecture

| Component | Value |
|-----------|-------|
| Cloudflare Pages project | `gentlequest-www` |
| Pages subdomain | `gentlequest-www.pages.dev` |
| Custom domains | `gentlequest.app`, `www.gentlequest.app` |
| Cloudflare zone ID | `da0309f5d36dc458e96b65457c9ad112` |
| Cloudflare account ID | `0ccfed02970a5a08f1e54d9f3c42d3f9` |
| Production branch | `main` |
| Blog source | `gentlequest-blog/` (Astro project) |
| Astro base path | `/blog` |

### Deploy Blog (manual steps)

```bash
# 1. Build the blog
npm run build --prefix /Users/lokeshgarg/gentlequest/gentlequest-blog

# 2. Restructure dist/ (Astro outputs at root, but we need /blog/ prefix)
rm -rf /tmp/gq-blog-deploy
mkdir -p /tmp/gq-blog-deploy/blog
cp -r /Users/lokeshgarg/gentlequest/gentlequest-blog/dist/* /tmp/gq-blog-deploy/blog/

# 3. Create _redirects file
echo "/ /blog/ 302" > /tmp/gq-blog-deploy/_redirects
echo "/blog/* /blog/:splat 200" >> /tmp/gq-blog-deploy/_redirects

# 4. Deploy to Cloudflare Pages
wrangler pages deploy /tmp/gq-blog-deploy \
  --project-name gentlequest-www \
  --branch main \
  --commit-dirty

# 5. Purge Cloudflare CDN cache (via MCP or API)
# Using Cloudflare MCP:
# mcp_call_tool cloudflare execute with:
#   zoneId = "da0309f5d36dc458e96b65457c9ad112"
#   POST /zones/{zoneId}/purge_cache with { purge_everything: true }

# 6. Verify
curl -sL "https://gentlequest.app/blog/iip-vs-chatgpt-stress-test/" | grep -o 'ref=blog_cta_[a-z_]*'
# Should show: ref=blog_cta_end
```

### Known Issues

1. **Astro base path mismatch**: Astro `base: '/blog'` generates URLs with `/blog/`
   prefix but outputs files at the root of `dist/`. The restructure step (2) is required
   until this is fixed.

2. **Cloudflare CDN cache**: After deploying to Pages, the CDN cache must be purged.
   The cache-control header is `s-maxage=604800` (7 days), so stale content persists
   without explicit purge.

3. **Render static site is NOT the blog origin**: The `render.yaml` has a
   `gentlequest-blog` static site config, but `gentlequest.app` DNS points to
   Cloudflare Pages. Deploying to Render does NOT update the live blog.
