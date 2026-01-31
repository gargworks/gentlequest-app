#!/bin/bash

# release_mobile.sh
# 
# A resilient wrapper to trigger the "One-Button Release" GitHub Action.
# Can be invoked by any agent in any thread.
#
# Usage: ./scripts/release_mobile.sh [internal|production|dry-run] "Optional Release Notes"

set -e

# Default values
TRACK="internal"
UPLOAD="true"
NOTES="Automated release via /release-mobile"
BUILD_NUMBER="" # Empty = auto-increment

# Parse arguments
if [ -n "$1" ]; then
    case "$1" in
        internal)
            TRACK="internal"
            ;;
        production)
            TRACK="production"
            # TODO: Add safety check for production?
            ;;
        dry-run)
            UPLOAD="false"
            NOTES="Dry Run Verification"
            ;;
        *)
            echo "Usage: $0 [internal|production|dry-run] [\"notes\"]"
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

echo "🚀 Preparing One-Button Mobile Release..."
echo "   Start Time: $(date)"
echo "   Track: $TRACK"
echo "   Upload: $UPLOAD"
echo "   Notes: $NOTES"

# Construct JSON Params
# We use printf '%s' to avoid issues with newlines/escaping in simple variables, 
# but for the JSON we construct carefully.

# Android Params
ANDROID_JSON=$(printf '{"app_id":"%s","package_name":"%s","track":"%s","upload":"%s","preflight":"false","crashlytics_upload":"false"}' \
    "$ANDROID_APP_ID" "$ANDROID_APP_ID" "$TRACK" "$UPLOAD")

# iOS Params
# Note: Production track for iOS usually implies TestFlight (export_method: app-store) until manual promotion
IOS_JSON=$(printf '{"bundle_id":"%s","scheme":"Runner","export_method":"app-store","upload":"%s","preflight":"false"}' \
    "$IOS_BUNDLE_ID" "$UPLOAD")

echo "⏳ Triggering GitHub Action..."

gh workflow run release_one_button.yml \
  --ref main \
  -f release_notes="$NOTES" \
  -f build_number="$BUILD_NUMBER" \
  -f android_params="$ANDROID_JSON" \
  -f ios_params="$IOS_JSON"

echo "✅ Triggered successfully!"
echo "👉 Monitor progress: gh run watch"
