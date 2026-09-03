#!/usr/bin/env bash
# Build, manually sign, package and upload the iOS app to TestFlight.
#
# Codified 2026-09-03 from docs/STORE_DEPLOYMENT.md steps 4-7. Every step there
# was previously run by hand. `flutter build ipa` needs an interactive Apple ID
# session in Xcode, so this builds --no-codesign and signs by hand with the
# distribution cert + AppStore profile. Each stage verifies its own output
# before the next runs; an upload of a mis-signed IPA fails only at Apple's
# end with an opaque error number, which is the slow way to find out.
set -euo pipefail

FLUTTER="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin"
export PATH="$FLUTTER:$PATH"
APP_DIR="$HOME/gq-wo/ai_buddy_web"
APP_PATH="$APP_DIR/build/ios/iphoneos/Runner.app"
IPA_DIR="$APP_DIR/build/ios/ipa"
IPA="$IPA_DIR/GentleQuest.ipa"
CERT="7672A7A08EC2B97B93C35A8A843D1A2DEE93E591"          # Apple Distribution (828Q2S3G4Q)
PROFILE="$HOME/Library/MobileDevice/Provisioning Profiles/251fc563-82c5-45cf-94f9-b7d0701ee56d.mobileprovision"
API_KEY="L6BQY5DFKM"
ISSUER="$(tr -d '[:space:]' < "$HOME/.appstoreconnect/issuer_id.txt")"
ENT="$(mktemp -t gq_ent).plist"

[ -f "$PROFILE" ] || { echo "profile missing: $PROFILE" >&2; exit 1; }
security find-identity -v -p codesigning | grep -q "$CERT" || { echo "distribution cert $CERT not in keychain" >&2; exit 1; }
EXP=$(security cms -D -i "$PROFILE" | plutil -extract ExpirationDate raw -)
[[ "$EXP" > "$(date -u +%Y-%m-%dT%H:%M:%SZ)" ]] || { echo "profile EXPIRED $EXP" >&2; exit 1; }

FREE_GB=$(df -g / | awk 'NR==2{print $4}')
[ "$FREE_GB" -ge 5 ] || { echo "only ${FREE_GB}G free; an iOS build needs ~5G (errno 28 has bitten twice today)" >&2; exit 1; }

cd "$APP_DIR"
if [ "${1:-}" = "--skip-build" ]; then
  echo "==> 1/6 build SKIPPED (reusing existing Runner.app)"
else
  echo "==> 1/6 build (no codesign)"
  flutter build ios --release --no-codesign 2>&1 | tail -3
fi
[ -d "$APP_PATH" ] || { echo "no Runner.app at $APP_PATH" >&2; exit 1; }

echo "==> 2/6 embed profile + write entitlements"
cp "$PROFILE" "$APP_PATH/embedded.mobileprovision"
cat > "$ENT" <<'PLIST'
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

# Apple error 90360: App.framework (Flutter's AOT bundle) ships an Info.plist
# with no MinimumOSVersion, and App Store Connect rejects the upload for it.
# The value is the Podfile's deployment target. Injected into any framework
# that lacks it, BEFORE signing, since signing seals the plist.
MIN_OS=$(grep -m1 "^platform :ios" "$APP_DIR/ios/Podfile" | sed -E "s/.*'([0-9.]+)'.*/\1/")
[ -n "$MIN_OS" ] || MIN_OS="15.0"
for fw in "$APP_PATH"/Frameworks/*.framework; do
  if ! plutil -extract MinimumOSVersion raw "$fw/Info.plist" >/dev/null 2>&1; then
    plutil -insert MinimumOSVersion -string "$MIN_OS" "$fw/Info.plist"
    echo "    injected MinimumOSVersion=$MIN_OS into $(basename "$fw")"
  fi
done

echo "==> 3/6 sign frameworks, then the app"
# Every framework must be signed individually or Apple rejects with 90034.
find "$APP_PATH/Frameworks" -name "*.framework" -type d | while read -r fw; do
  /usr/bin/codesign --force --sign "$CERT" --timestamp=none "$fw"
done
/usr/bin/codesign --force --sign "$CERT" --entitlements "$ENT" --timestamp=none "$APP_PATH"

echo "==> 4/6 verify signature"
# Capture first, grep second. `cmd | grep -q` under pipefail is a trap: grep
# exits on the first match, codesign gets SIGPIPE, and the pipeline reports
# failure for a signature that is perfectly valid. That exact false alarm cost
# a re-run the first time this script ran.
VERIFY=$(codesign -vvv "$APP_PATH" 2>&1 || true)
echo "$VERIFY" | grep -q "valid on disk" || { echo "signature INVALID:"; echo "$VERIFY"; exit 1; } >&2
ENTS=$(codesign -d --entitlements - "$APP_PATH" 2>&1 || true)
echo "$ENTS" | grep -q "application-identifier" || { echo "application-identifier entitlement missing (Apple error 90075)" >&2; exit 1; }
# Every framework, not just the two that print "replacing existing signature".
UNSIGNED=0
for fw in "$APP_PATH"/Frameworks/*.framework; do
  codesign -v "$fw" 2>/dev/null || { echo "    UNSIGNED: $(basename "$fw")" >&2; UNSIGNED=1; }
done
[ "$UNSIGNED" -eq 0 ] || { echo "unsigned frameworks present (Apple error 90034)" >&2; exit 1; }
echo "    signed + entitlements ok"

echo "==> 5/6 package IPA (zip with Payload/ at root)"
rm -rf "$IPA_DIR/Payload" "$IPA"; mkdir -p "$IPA_DIR/Payload"
cp -R "$APP_PATH" "$IPA_DIR/Payload/"
/usr/bin/python3 - "$IPA" "$IPA_DIR/Payload" <<'PY'
import os, sys, zipfile
ipa, payload = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(ipa, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(payload):
        for f in files:
            p = os.path.join(root, f)
            zf.write(p, os.path.relpath(p, os.path.dirname(payload)))
print(f"    {os.path.getsize(ipa)//1_000_000} MB")
PY
LISTING=$(unzip -l "$IPA" || true)   # same SIGPIPE trap as step 4; capture first
echo "$LISTING" | grep -q "Payload/Runner.app/Info.plist" || { echo "IPA structure wrong (no Payload/Runner.app at root)" >&2; exit 1; }
V=$(unzip -p "$IPA" Payload/Runner.app/Info.plist | plutil -extract CFBundleShortVersionString raw - 2>/dev/null); B=$(unzip -p "$IPA" Payload/Runner.app/Info.plist | plutil -extract CFBundleVersion raw - 2>/dev/null)
echo "    version $V ($B)"

echo "==> 6/6 upload to App Store Connect"
xcrun altool --upload-app -t ios -f "$IPA" --apiKey "$API_KEY" --apiIssuer "$ISSUER" 2>&1 | grep -E "UPLOAD SUCCEEDED|Delivery UUID|error|ERROR" | head -5
echo "==> done: $V ($B) uploaded. TestFlight processing takes ~10-20 min."
