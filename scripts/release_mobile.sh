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

echo "⏳ Triggering GitHub Action..."

gh workflow run release_one_button.yml \
  --ref main \
  -f release_notes="$NOTES" \
  -f build_number="$BUILD_NUMBER" \
  -f android_params="$ANDROID_JSON" \
  -f ios_params="$IOS_JSON"

echo -e "${GREEN}✅ Triggered successfully!${NC}"
echo "👉 Monitor progress: gh run watch"
