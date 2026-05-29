#!/bin/bash
# Complete Launch Checklist for GentleQuest
# Run this before submitting to App Store and Play Store

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 GentleQuest Launch Readiness Checklist"
echo "=========================================="
echo ""

READY=true

# Function to check requirement
check_requirement() {
    local name=$1
    local check_command=$2
    local help_text=$3
    
    echo -n "Checking $name... "
    if eval $check_command 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo "  ${YELLOW}→ $help_text${NC}"
        READY=false
    fi
}

echo "📱 App Configuration:"
echo "--------------------"

check_requirement "Bundle ID configured" \
    "grep -q 'APP_BUNDLE_ID = com.gentlequest' ai_buddy_web/ios/Config/AppIdentifiers.xcconfig" \
    "Set bundle ID in ios/Config/AppIdentifiers.xcconfig"

check_requirement "Android package name" \
    "grep -qE 'applicationId[[:space:]]+[\"0-9a-zA-Z._]+' ai_buddy_web/android/app/build.gradle" \
    "Set applicationId in android/app/build.gradle"

check_requirement "App version set" \
    "grep -qE '^version:[[:space:]]+[0-9]+\.[0-9]+\.[0-9]+(\+[0-9]+)?' ai_buddy_web/pubspec.yaml" \
    "Update version in pubspec.yaml"

echo ""
echo "🔐 Signing & Certificates:"
echo "-------------------------"

check_requirement "Android keystore exists" \
    "test -f ai_buddy_web/android/app/upload-keystore.jks" \
    "Generate keystore: keytool -genkey -v -keystore upload-keystore.jks"

check_requirement "iOS signing secrets configured" \
    "gh secret list -R $(git remote get-url origin | sed 's/.*github.com[\/:]//;s/\.git//') | grep -q IOS_P12_BASE64" \
    "Add iOS signing secrets to GitHub"

echo ""
echo "🔥 Firebase Configuration:"
echo "-------------------------"

check_requirement "Android google-services.json" \
    "test -f ai_buddy_web/android/app/google-services.json" \
    "Download from Firebase Console and place in android/app/"

check_requirement "iOS GoogleService-Info.plist" \
    "test -f ai_buddy_web/ios/Runner/GoogleService-Info.plist" \
    "Download from Firebase Console and place in ios/Runner/"

check_requirement "Firebase dependencies added" \
    "grep -q 'firebase_core:' ai_buddy_web/pubspec.yaml" \
    "Run: flutter pub add firebase_core firebase_analytics firebase_crashlytics"

echo ""
echo "📸 App Store Assets:"
echo "-------------------"

check_requirement "App icon (iOS)" \
    "ls ai_buddy_web/ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024*.png >/dev/null 2>&1" \
    "Generate app icons with flutter_launcher_icons"

check_requirement "App icon (Android)" \
    "test -f ai_buddy_web/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png" \
    "Generate app icons with flutter_launcher_icons"

check_requirement "Screenshots directory" \
    "test -d app_store_assets/ios/screenshots" \
    "Run: ./scripts/generate_app_screenshots.sh"

echo ""
echo "📄 Legal & Compliance:"
echo "---------------------"

check_requirement "Privacy Policy" \
    "test -f ai_buddy_web/assets/legal/privacy.md" \
    "Create privacy policy in assets/legal/"

check_requirement "Terms of Service" \
    "test -f ai_buddy_web/assets/legal/terms.md" \
    "Create terms of service in assets/legal/"

check_requirement "App Store listing content" \
    "test -f docs/APP_STORE_LISTING.md" \
    "Prepare app descriptions and metadata"

echo ""
echo "🧪 Testing & Quality:"
echo "--------------------"

check_requirement "Unit tests exist" \
    "test -d ai_buddy_web/test" \
    "Add unit tests in test/"

check_requirement "Integration tests" \
    "test -f ai_buddy_web/test/screenshot_test.dart" \
    "Add integration tests (test/screenshot_test.dart)"

check_requirement "Flutter analyze passes" \
    "(cd ai_buddy_web && flutter analyze)" \
    "Fix linting issues: flutter analyze"

echo ""
echo "🌐 Deep Linking:"
echo "---------------"

check_requirement "iOS Universal Links configured" \
    "grep -q 'FlutterDeepLinkingEnabled' ai_buddy_web/ios/Runner/Info.plist" \
    "Configure Universal Links in Info.plist"

check_requirement "Android App Links configured" \
    "grep -q 'android:autoVerify=\"true\"' ai_buddy_web/android/app/src/main/AndroidManifest.xml" \
    "Configure App Links in AndroidManifest.xml"

echo ""
echo "📊 Analytics & Monitoring:"
echo "-------------------------"

check_requirement "Sentry configured" \
    "(grep -q 'SENTRY_DSN_FRONTEND' .env.production || grep -q 'SENTRY_DSN_FRONTEND' .env)" \
    "Add Sentry DSN to environment"

check_requirement "Firebase Analytics integrated" \
    "grep -q 'FirebaseService' ai_buddy_web/lib/main.dart" \
    "Initialize Firebase in main.dart"

echo ""
echo "🚀 CI/CD Pipeline:"
echo "-----------------"

check_requirement "Android Release workflow" \
    "test -f .github/workflows/android_release.yml" \
    "Android release workflow exists"

check_requirement "iOS Release workflow" \
    "test -f .github/workflows/ios_release.yml" \
    "iOS release workflow exists"

check_requirement "Mobile Release orchestrator" \
    "test -f .github/workflows/mobile_release.yml" \
    "Combined mobile release workflow exists"

echo ""
echo "📦 Production Backend:"
echo "---------------------"

check_requirement "Backend deployed" \
    "curl -s https://app.gentlequest.app/api/health | grep -E -q 'healthy|green'" \
    "Deploy backend to production"

check_requirement "Environment variables set" \
    "(test -f .env.production || test -f .env)" \
    "Configure production environment variables"

echo ""
echo "=========================================="
if [ "$READY" = true ]; then
    echo -e "${GREEN}✅ All checks passed! Ready for launch!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run final build: ./scripts/mobile_release.sh"
    echo "2. Upload to TestFlight via Transporter"
    echo "3. Upload to Play Console Internal Testing"
    echo "4. Submit for review"
else
    echo -e "${RED}❌ Some checks failed. Fix issues above before launching.${NC}"
    exit 1
fi

echo ""
echo "📋 Manual Checklist:"
echo "-------------------"
echo "[ ] Developer accounts registered (Apple/Google)"
echo "[ ] App Store Connect app created"
echo "[ ] Play Console app created"
echo "[ ] Beta testers invited"
echo "[ ] Support email configured"
echo "[ ] Crash reporting verified"
echo "[ ] Privacy policy URL live"
echo "[ ] Terms of service URL live"
echo "[ ] App preview video created (optional)"
echo "[ ] Release notes written"
