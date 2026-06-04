#!/bin/bash

# release_mobile.sh
# 
# A resilient wrapper to trigger the "One-Button Release" GitHub Action.
# Can be invoked by any agent in any thread.
#
# Usage: ./scripts/release_mobile.sh [internal|public|dry-run] "Optional Release Notes"

set -e

# Default values
TRACK="internal"
UPLOAD="true"
STATUS="draft" # Default to draft for safety
# Auto-generate meaningful build number: YYMMDDHH (e.g. 26020314)
# This ensures strictly increasing versions and avoids conflicts with previous lower numbers.
# Android Max: 2,100,000,000. Our format 26020314 is ~26 million (Safe).
DEFAULT_BN=$(date +%y%m%d%H)
BUILD_NUMBER="${3:-$DEFAULT_BN}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
if [ -n "$1" ]; then
    case "$1" in
        internal)
            TRACK="internal"
            STATUS="completed" # Internal releases can usually go straight to completed if build # increments
            ;;
        public|production)
            TRACK="production"
            echo -e "${RED}🚨  WARNING: YOU ARE TARGETING PRODUCTION (PUBLIC USERS) 🚨${NC}"
            echo -e "${YELLOW}Track: ${TRACK}${NC}"
            
            # Interactive check for status
            echo ""
            echo "Select Release Status:"
            echo "  [1] Draft     (Safe - Requires manual 'Review' in Console)"
            echo "  [2] Completed (LIVE - Immediately publishes to users if valid)"
            read -p "Enter selection [1/2] (default 1): " status_choice
            
            if [ "$status_choice" == "2" ]; then
                STATUS="completed"
                echo -e "${RED}⚠️  STATUS SET TO: COMPLETED (LIVE RELEASE)${NC}"
            else
                STATUS="draft"
                echo -e "${GREEN}✅  Status set to: Draft (Safe)${NC}"
            fi

            # Final Confirmation
            echo ""
            read -p "Are you sure you want to proceed? (y/N): " confirm
            if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
                echo "Aborted."
                exit 0
            fi
            ;;
        dry-run)
            UPLOAD="false"
            NOTES="Dry Run Verification"
            ;;
        *)
            echo "Usage: $0 [internal|public|dry-run] [\"notes\"]"
            exit 1
            ;;
    esac
fi

if [ -n "$2" ]; then
    NOTES="$2"
fi

# Auto-derive release notes from filesystem when no $2 provided.
# Convention: app_store_assets/v<pubspec-version>/RELEASE_NOTES.md
# (use scripts/bump_version.sh to create the stub when bumping pubspec.)
if [ -z "$NOTES" ] && [ -f "ai_buddy_web/pubspec.yaml" ]; then
    PUBSPEC_VERSION=$(grep -E '^version:' ai_buddy_web/pubspec.yaml | head -1 | sed -E 's/version:[[:space:]]*([0-9.]+).*/\1/')
    NOTES_FILE="app_store_assets/v${PUBSPEC_VERSION}/RELEASE_NOTES.md"
    if [ -f "$NOTES_FILE" ]; then
        NOTES=$(cat "$NOTES_FILE")
        echo -e "${GREEN}📝 Auto-loaded release notes from ${NOTES_FILE} (${#NOTES} chars)${NC}"
    else
        echo -e "${YELLOW}⚠️  No release notes provided and ${NOTES_FILE} not found. whatsNew will not be updated.${NC}"
    fi
fi

# Constants
ANDROID_APP_ID="app.gentlequest.www"
IOS_BUNDLE_ID="com.gentlequest.app"

echo -e "${GREEN}🚀 Preparing One-Button Mobile Release...${NC}"
echo "   Start Time: $(date)"
echo "   Track:      $TRACK"
echo "   Status:     $STATUS"
echo "   Build #:    $BUILD_NUMBER"
echo "   Upload:     $UPLOAD"
echo "   Notes:      $NOTES"

# Construct JSON Params
# We use printf '%s' to avoid issues with newlines/escaping in simple variables, 
# but for the JSON we construct carefully.

# Android Params
# Only production track supports 'status' field meaningful usage here effectively
ANDROID_JSON=$(printf '{"app_id":"%s","package_name":"%s","track":"%s","status":"%s","upload":"%s","preflight":"false","crashlytics_upload":"false"}' \
    "$ANDROID_APP_ID" "$ANDROID_APP_ID" "$TRACK" "$STATUS" "$UPLOAD")

# iOS Params
# For 'public' track, also submit to App Store Review after TestFlight upload.
# 'internal' / 'dry-run' stay TestFlight-only.
IOS_SUBMIT_FOR_REVIEW="false"
if [ "$TRACK" == "production" ]; then
    IOS_SUBMIT_FOR_REVIEW="true"
fi
IOS_JSON=$(printf '{"bundle_id":"%s","scheme":"Runner","export_method":"app-store","upload":"%s","preflight":"false","submit_for_review":"%s"}' \
    "$IOS_BUNDLE_ID" "$UPLOAD" "$IOS_SUBMIT_FOR_REVIEW")

# iOS pre-flight: warn if flutterfire CLI is missing.
# Without it, the Xcode build phase 'flutterfire upload-crashlytics-symbols'
# silent-skips on the local machine and crashes will land in Firebase
# Crashlytics with obfuscated hex stack traces. Catch fresh-machine setups
# before they ship a un-symbolicated build.
if ! command -v flutterfire >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠  flutterfire CLI not found in PATH.${NC}"
    echo "   If this run produces an iOS artifact, dSYMs will NOT be uploaded"
    echo "   and Firebase Crashlytics will show obfuscated stack traces."
    echo "   Fix:  dart pub global activate flutterfire_cli"
    echo "         firebase login"
    echo "         flutterfire configure --project=gentlequestapp --platforms=ios,android,web --yes"
    echo "   See docs/release/MANUAL_RELEASE_PLAYBOOK.md §7.2 for retro upload."
    echo ""
fi

echo "⏳ Triggering GitHub Action..."

gh workflow run release_one_button.yml \
  --ref main \
  -f release_notes="$NOTES" \
  -f build_number="$BUILD_NUMBER" \
  -f android_params="$ANDROID_JSON" \
  -f ios_params="$IOS_JSON"

echo -e "${GREEN}✅ Triggered successfully!${NC}"

# GHA billing-exhaustion detection (added 2026-06-04 after billing-cap-hit
# silently killed the Android v1.3.0 cron-fire). Poll the workflow conclusion
# for ~25 seconds. If the run fails before then, it's the billing-exhaustion
# signature (sub-30s failure on a freshly dispatched workflow); surface the
# manual fallback path so the operator doesn't waste time waiting.
echo ""
echo "🔎 Watching workflow for early failure (billing-exhaustion check, ~25s)..."
sleep 5
RUN_ID=$(gh run list --workflow=release_one_button.yml --limit 1 --json databaseId --jq '.[0].databaseId' 2>/dev/null || echo "")
sleep 20
CONCLUSION=$(gh run view "$RUN_ID" --json conclusion --jq '.conclusion' 2>/dev/null || echo "")

if [ "$CONCLUSION" = "failure" ]; then
    cat <<EOF

${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
${RED}⚠  GHA workflow failed in <25s. Billing-exhaustion signature.${NC}
${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

Pivot to LOCAL BUILD per docs/release/MANUAL_RELEASE_PLAYBOOK.md:

  iOS:
    cd ai_buddy_web && flutter build ipa --release
    xcrun altool --upload-app --type ios \\
      --file build/ios/ipa/ai_buddy_web.ipa \\
      --apiKey \$ASC_KEY_ID \\
      --apiIssuer \$(cat ~/.appstoreconnect/issuer_id.txt) --verbose
    # then: python3 scripts/asc_submit_for_review.py
    #         --app-id 6756537464 --version-id <NEW_VERSION_ID>

  Android:
    cd ai_buddy_web && flutter build appbundle --release
    # AAB at build/app/outputs/bundle/release/app-release.aab
    # manual drag-drop to Play Console (operator-action) OR fastlane supply

EOF
    exit 2
fi

echo -e "${GREEN}✅ Workflow not in early-failure state (conclusion=${CONCLUSION:-pending}).${NC}"
echo "👉 Monitor progress: gh run watch"
