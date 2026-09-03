#!/usr/bin/env bash
# Build and upload the iOS app to TestFlight.
#
# REWRITTEN 2026-09-04, after the hand-signed path produced a build that
# installed, launched, and rendered NOTHING — black past 30s on a real iPhone
# (iOS 26.1) — while the previous TestFlight build was fine on the same phone.
# That ruled out a Flutter/iOS incompatibility and pointed at packaging.
#
# What the hand-rolled path got wrong. Both were silent; only a device showed it:
#
#   * The IPA was zipped with a Python os.walk over FILES only, dropping
#     symlinks and empty dirs — 42 MB where a correct export is 54 MB. It still
#     passed `codesign --verify --deep --strict` AND Apple's ingestion.
#   * ios/Flutter/AppFrameworkInfo.plist lacked MinimumOSVersion (Flutter's own
#     template has 12.0). That caused Apple error 90360, which is why a BUILT
#     framework's Info.plist was being patched by hand instead of the source.
#     The source is fixed now.
#   * docs/STORE_DEPLOYMENT.md says `flutter build ipa` needs an interactive
#     Xcode session. STALE: it builds headless with a manual-signing
#     ExportOptions.plist. Verified 2026-09-04.
#
# So: no hand signing, no hand zipping. `flutter build ipa` archives and exports
# through xcodebuild — the path CI uses, and the path behind every build that
# has actually worked.
set -euo pipefail

export PATH="/Volumes/Samsung SSD 990 PRO 2TB Media/Dev/flutter/bin:$PATH"
APP_DIR="$HOME/gq-wo/ai_buddy_web"
API_KEY="L6BQY5DFKM"
ISSUER="$(tr -d '[:space:]' < "$HOME/.appstoreconnect/issuer_id.txt")"
cd "$APP_DIR"

FREE_GB=$(df -g / | awk 'NR==2{print $4}')
[ "$FREE_GB" -ge 6 ] || { echo "only ${FREE_GB}G free; an iOS archive needs ~6G" >&2; exit 1; }

# Guard the source defect that started all this.
python3 -c "
import plistlib, sys
p='ios/Flutter/AppFrameworkInfo.plist'
if 'MinimumOSVersion' not in plistlib.load(open(p,'rb')):
    sys.exit(p + ' is missing MinimumOSVersion (Apple error 90360). Add 12.0.')
"

echo "==> building signed IPA (archive + export, manual signing)"
flutter build ipa --release --export-options-plist=ExportOptions.plist 2>&1 | tail -3
IPA=$(ls -t build/ios/ipa/*.ipa 2>/dev/null | head -1)
[ -n "$IPA" ] || { echo "no IPA produced" >&2; exit 1; }

echo "==> verifying the export before spending an upload on it"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
unzip -q "$IPA" -d "$T"
A="$T/Payload/Runner.app"
[ -d "$A" ] || { echo "IPA has no Payload/Runner.app" >&2; exit 1; }
codesign --verify --deep --strict "$A" 2>/dev/null || { echo "signature invalid" >&2; exit 1; }
ENTS=$(codesign -d --entitlements - "$A" 2>&1 || true)
echo "$ENTS" | grep -q application-identifier || { echo "missing application-identifier (Apple 90075)" >&2; exit 1; }
# Size floor. The symlink-dropping zip produced 42 MB while four signature and
# structure checks all passed; size was the only cheap signal that caught it.
SIZE_MB=$(( $(stat -f%z "$IPA") / 1000000 ))
[ "$SIZE_MB" -ge 50 ] || { echo "IPA is ${SIZE_MB} MB, expected >=50 — files may have been dropped" >&2; exit 1; }
V=$(plutil -extract CFBundleShortVersionString raw "$A/Info.plist")
B=$(plutil -extract CFBundleVersion raw "$A/Info.plist")
echo "    $V ($B), ${SIZE_MB} MB, signed + entitlements ok"

echo "==> uploading"
xcrun altool --upload-app -t ios -f "$IPA" --apiKey "$API_KEY" --apiIssuer "$ISSUER" 2>&1 | grep -E "UPLOAD SUCCEEDED|UPLOAD FAILED|Delivery UUID|ERROR" | head -5
echo "==> done: $V ($B). TestFlight processing ~10-20 min."
