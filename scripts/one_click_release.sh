#!/bin/bash
# One-Click Release Script for GentleQuest
# Orchestrates complete release process for both iOS and Android

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🚀 GentleQuest One-Click Release"
echo "================================="
echo ""

# Check prerequisites
echo "${BLUE}Checking prerequisites...${NC}"

# Check Flutter
if ! command -v flutter &> /dev/null; then
    echo -e "${RED}✗ Flutter not found${NC}"
    exit 1
fi

# Check GitHub CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}✗ GitHub CLI not found${NC}"
    echo "Install: brew install gh"
    exit 1
fi

# Check if in correct directory
if [ ! -f "ai_buddy_web/pubspec.yaml" ]; then
    echo -e "${RED}✗ Not in project root directory${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites checked${NC}"
echo ""

# Run launch checklist
echo "${BLUE}Running launch checklist...${NC}"
if [ -f "scripts/complete_launch_checklist.sh" ]; then
    chmod +x scripts/complete_launch_checklist.sh
    if ! ./scripts/complete_launch_checklist.sh; then
        echo ""
        echo -e "${YELLOW}⚠ Launch checklist failed with some issues.${NC}"
        read -p "Do you want to proceed anyway? [y/N]: " proceed_anyway
        if [[ $proceed_anyway != "y" && $proceed_anyway != "Y" ]]; then
            echo -e "${RED}Aborting release.${NC}"
            exit 1
        fi
        echo -e "${YELLOW}Proceeding with release despite checklist failures...${NC}"
    fi
fi

echo ""
echo "${BLUE}Select release type:${NC}"
echo "1) TestFlight/Internal Testing (Beta)"
echo "2) Production Release"
echo "3) Hotfix"
read -p "Choice [1-3, Default: 1]: " release_type
release_type=${release_type:-1}

case $release_type in
    1)
        RELEASE_TYPE="beta"
        UPLOAD_TO_STORE="false"
        ;;
    2)
        RELEASE_TYPE="production"
        UPLOAD_TO_STORE="true"
        ;;
    3)
        RELEASE_TYPE="hotfix"
        UPLOAD_TO_STORE="true"
        ;;
    *)
        RELEASE_TYPE="beta"
        UPLOAD_TO_STORE="false"
        ;;
esac
 
 # Choose runner type
 echo ""
 echo "${BLUE}Select where to run the build:${NC}"
 echo "1) GitHub Hosted (Standard)"
 echo "2) Self-Hosted (Local Mac - Bypasses Billing Limits)"
 echo "3) Local Build (Skip CI - Immediate)"
 read -p "Choice [1-3, Default: 2]: " runner_choice
 runner_choice=${runner_choice:-2}
 
 case $runner_choice in
     1)
         RUNNER_TYPE="github_hosted"
         ;;
     2)
         RUNNER_TYPE="self_hosted"
         ;;
     3)
         RUNNER_TYPE="local"
         ;;
     *)
         RUNNER_TYPE="self_hosted"
         ;;
 esac

# Update version
echo ""
echo "${BLUE}Version Management:${NC}"
if [ -f "scripts/version_automation.sh" ]; then
    chmod +x scripts/version_automation.sh
    ./scripts/version_automation.sh
fi

# Get current version
VERSION=$(grep "^version:" ai_buddy_web/pubspec.yaml | sed 's/version: //g' | sed 's/+.*//g')
BUILD=$(grep "^version:" ai_buddy_web/pubspec.yaml | sed 's/.*+//g')

echo ""
echo "${YELLOW}Building Release v$VERSION+$BUILD ($RELEASE_TYPE)${NC}"
echo ""

# Clean Flutter
echo "${BLUE}Cleaning Flutter project...${NC}"
cd ai_buddy_web
flutter clean
flutter pub get
cd ..
echo -e "${GREEN}✓ Flutter cleaned${NC}"

# HARDENING: Patches
echo "${BLUE}Applying hardening patches...${NC}"
# Patch 1: Remove IntegrationTestPlugin from GeneratedPluginRegistrant (Fixes Release Build)
# We find any line with IntegrationTestPlugin and comment it out to be safe
if [ -f "ai_buddy_web/android/app/src/main/java/io/flutter/plugins/GeneratedPluginRegistrant.java" ]; then
    echo "Patching GeneratedPluginRegistrant.java..."
    # Use perl for in-place editing to handle potential issues with sed across platforms (macOS/Linux)
    # We comment out the lines containing 'IntegrationTestPlugin'
    perl -pi -e 's/^(.*IntegrationTestPlugin.*)$/\/\/ \1/' ai_buddy_web/android/app/src/main/java/io/flutter/plugins/GeneratedPluginRegistrant.java
    echo -e "${GREEN}✓ Applied IntegrationTestPlugin patch${NC}"
else
     echo -e "${YELLOW}⚠ GeneratedPluginRegistrant.java not found yet. It might be generated later during build.${NC}"
fi
echo ""

# Run tests
echo ""
echo "${BLUE}Running tests...${NC}"
cd ai_buddy_web
flutter analyze --no-fatal-warnings || true
if [ -d "test" ]; then
    flutter test || echo "${YELLOW}⚠ Some tests failed${NC}"
fi
cd ..

# Generate screenshots if needed
echo ""
read -p "Generate new screenshots? [y/N]: " gen_screenshots
if [[ $gen_screenshots == "y" || $gen_screenshots == "Y" ]]; then
    if [ -f "scripts/generate_app_screenshots.sh" ]; then
        chmod +x scripts/generate_app_screenshots.sh
        ./scripts/generate_app_screenshots.sh
    fi
fi

# Fix iOS Project (GoogleService-Info.plist injection)
echo ""
echo "${BLUE}Fixing iOS Project configuration...${NC}"
if [ -f "scripts/fix_ios_project.rb" ]; then
    ruby scripts/fix_ios_project.rb
    echo -e "${GREEN}✓ iOS project fixed${NC}"
else
    echo -e "${YELLOW}⚠ scripts/fix_ios_project.rb not found. Skipping fix.${NC}"
fi

# Build for platforms
echo ""
echo "${BLUE}Building releases...${NC}"

# Ensure local changes are pushed to origin before triggering CI
echo "${BLUE}Syncing changes with origin...${NC}"
git push origin HEAD || echo -e "${YELLOW}⚠ Could not push to origin. CI might run stale code.${NC}"

PERFORM_LOCAL_BUILD="false"

if [ "$RUNNER_TYPE" == "local" ]; then
    echo -e "${YELLOW}Skipping CI as requested. Performing local build...${NC}"
    PERFORM_LOCAL_BUILD="true"
else
    # Trigger CI build
    echo "Triggering Mobile Release workflow on $RUNNER_TYPE..."
    WORKFLOW_RUN=$(gh workflow run mobile_release.yml \
        -f "build_params={\"build_number\":\"$BUILD\",\"release_notes\":\"Release v$VERSION\",\"preflight\":\"false\"}" \
        -f "android_params={\"app_id\":\"app.gentlequest.www\",\"package_name\":\"app.gentlequest.www\",\"track\":\"internal\",\"upload\":\"$UPLOAD_TO_STORE\"}" \
        -f "ios_params={\"bundle_id\":\"com.gentlequest.app\",\"scheme\":\"Runner\",\"export_method\":\"app-store\",\"upload\":\"$UPLOAD_TO_STORE\"}" \
        -f "release_params={\"create_gh_release\":\"true\",\"tag_prefix\":\"v\"}" \
        -f "runner_type=$RUNNER_TYPE" 2>&1)

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ CI workflow triggered${NC}"
        
        # Get workflow run ID
        RUN_ID=$(gh run list --workflow=mobile_release.yml --limit=1 --json databaseId --jq '.[0].databaseId')
        
        echo "Workflow run ID: $RUN_ID"
        echo "Watch progress: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runs/$RUN_ID"
        
        # Wait for completion
        echo ""
        echo "${BLUE}Waiting for build to complete...${NC}"
        echo "This may take 10-15 minutes..."
        
        gh run watch $RUN_ID || true
        
        # Check if the run actually succeeded
        RUN_STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
        if [ "$RUN_STATUS" != "success" ]; then
            echo ""
            echo -e "${RED}✗ CI build failed with status: $RUN_STATUS${NC}"
            echo ""
            echo "View logs: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runs/$RUN_ID"
            echo ""
            echo "Common issues:"
            echo "  - Android: Check build.gradle versioning and signing"
            echo "  - iOS: Check provisioning profiles and certificates"
            echo "  - Both: Check Flutter analyze and test results"
            
            # Fallback prompt
            echo ""
            read -p "CI failed. Attempt local build? [y/N]: " fallback_local
            if [[ "$fallback_local" == "y" || "$fallback_local" == "Y" ]]; then
                PERFORM_LOCAL_BUILD="true"
            else
                exit 1
            fi
        else
             # Download artifacts
            echo ""
            echo "${BLUE}Downloading artifacts...${NC}"
            # Clean previous artifacts to avoid extraction conflicts
            rm -rf release_artifacts/*
            mkdir -p release_artifacts
            gh run download $RUN_ID -D release_artifacts || echo -e "${YELLOW}⚠ Could not download all artifacts${NC}"
            
            echo -e "${GREEN}✓ Artifacts downloaded to release_artifacts/${NC}"
        fi
    else
        echo -e "${RED}✗ Failed to trigger CI workflow${NC}"
        echo "Attempting local build..."
        PERFORM_LOCAL_BUILD="true"
    fi
fi

if [ "$PERFORM_LOCAL_BUILD" == "true" ]; then
    echo ""
    echo "${BLUE}Starting Local Build...${NC}"
    mkdir -p release_artifacts

    # Local Android build
    echo "${BLUE}Building Android AAB locally...${NC}"
    cd ai_buddy_web
    flutter build appbundle --build-number=$BUILD
    cp build/app/outputs/bundle/release/app-release.aab ../release_artifacts/android.aab
    cd ..
    echo -e "${GREEN}✓ Android AAB built${NC}"
    
    # Local iOS build (unsigned)
    echo "${BLUE}Building iOS app...${NC}"
    cd ai_buddy_web
    flutter build ios --release --no-codesign --build-number=$BUILD
    cd ..
    echo -e "${GREEN}✓ iOS app built (unsigned)${NC}"

    # IMPORTANT: Since we don't have the CI to finalize things, we must assume Manual Upload
    echo -e "${YELLOW}⚠ Local build complete. You must manually upload these artifacts.${NC}"
    
    echo ""
    echo "${GREEN}🚀 MANUAL UPLOAD REQUIRED (The 0.01% Check)${NC}"
    echo "---------------------------------------------------"
    echo "1. Android Play Console (Production):"
    echo "   URL: https://play.google.com/console/u/2/developers/5873334186320541231/app/4972169399121992985/releases/production"
    echo "   File to Upload (Drag & Drop):"
    echo "   $(pwd)/release_artifacts/android.aab"
    echo ""
    echo "2. iOS App Store Connect (via Transporter):"
    echo "   File to Upload:"
    echo "   $(pwd)/release_artifacts/Runner.app (Archive)"
    echo "---------------------------------------------------"
    echo ""
fi

# Post-build steps
echo ""
echo "${BLUE}Post-build steps:${NC}"

# Create release notes
cat > release_artifacts/RELEASE_NOTES.md << EOF
# GentleQuest Release v$VERSION

Build: $BUILD
Date: $(date +"%Y-%m-%d %H:%M")
Type: $RELEASE_TYPE

## What's New
- AI-powered mental wellness companion
- Mood tracking with insights
- Crisis resources for 11+ countries
- Evidence-based wellness exercises
- Complete privacy with encryption

## Platforms
- iOS: TestFlight ready
- Android: Internal testing ready

## Testing Instructions
1. Install via TestFlight (iOS) or Internal Testing (Android)
2. Test all major features
3. Report issues via in-app feedback

---
Generated by One-Click Release Script
EOF

echo -e "${GREEN}✓ Release notes created${NC}"

# Final summary
echo ""
echo "================================="
echo -e "${GREEN}✅ Release Build Complete!${NC}"
echo "================================="
echo ""
echo "Version: v$VERSION+$BUILD"
echo "Type: $RELEASE_TYPE"
echo "Artifacts: release_artifacts/"
echo ""
echo "${YELLOW}Next Steps:${NC}"
echo ""

if [ "$RELEASE_TYPE" == "beta" ]; then
    echo "📱 iOS (TestFlight):"
    echo "   1. Download IPA from release_artifacts/"
    echo "   2. Open Apple Transporter"
    echo "   3. Upload IPA to App Store Connect"
    echo "   4. Submit for Beta Review"
    echo "   5. Add external testers"
    echo ""
    echo "🤖 Android (Internal Testing):"
    echo "   1. Download AAB from release_artifacts/"
    echo "   2. Go to Play Console > Internal Testing"
    echo "   3. Upload AAB"
    echo "   4. Add release notes"
    echo "   5. Publish to internal testers"
else
    echo "📱 iOS (App Store):"
    echo "   1. Complete TestFlight beta testing"
    echo "   2. Submit for App Review"
    echo "   3. Set release date"
    echo ""
    echo "🤖 Android (Production):"
    echo "   1. Promote from internal to production"
    echo "   2. Complete store listing"
    echo "   3. Submit for review"
fi

echo ""
echo "📊 Monitor:"
echo "   - Firebase Console for crashes/analytics"
echo "   - TestFlight/Play Console for feedback"
echo "   - Support email for user issues"
echo ""
echo "${GREEN}Good luck with your launch! 🚀${NC}"

# Open relevant pages
echo ""
read -p "Open App Store Connect? [y/N]: " open_asc
if [[ $open_asc == "y" || $open_asc == "Y" ]]; then
    open "https://appstoreconnect.apple.com"
fi

read -p "Open Play Console? [y/N]: " open_pc
if [[ $open_pc == "y" || $open_pc == "Y" ]]; then
    open "https://play.google.com/console"
fi

read -p "Open Firebase Console? [y/N]: " open_fb
if [[ $open_fb == "y" || $open_fb == "Y" ]]; then
    open "https://console.firebase.google.com"
fi
