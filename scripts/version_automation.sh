#!/bin/bash
# Version and Build Number Automation for GentleQuest
# Handles semantic versioning and build numbers for both platforms

set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "📱 GentleQuest Version Manager"
echo "=============================="

# Configuration
PUBSPEC_PATH="ai_buddy_web/pubspec.yaml"
ANDROID_GRADLE="ai_buddy_web/android/app/build.gradle"
IOS_PROJECT="ai_buddy_web/ios/Runner.xcodeproj/project.pbxproj"

# Parse current version
CURRENT_VERSION=$(grep "^version:" $PUBSPEC_PATH | sed 's/version: //g' | sed 's/+.*//g')
CURRENT_BUILD=$(grep "^version:" $PUBSPEC_PATH | sed 's/.*+//g')

echo "Current version: $CURRENT_VERSION+$CURRENT_BUILD"
echo ""

# Function to increment version
increment_version() {
    local version=$1
    local type=$2
    
    IFS='.' read -ra PARTS <<< "$version"
    MAJOR=${PARTS[0]}
    MINOR=${PARTS[1]}
    PATCH=${PARTS[2]}
    
    case $type in
        major)
            MAJOR=$((MAJOR + 1))
            MINOR=0
            PATCH=0
            ;;
        minor)
            MINOR=$((MINOR + 1))
            PATCH=0
            ;;
        patch)
            PATCH=$((PATCH + 1))
            ;;
    esac
    
    echo "$MAJOR.$MINOR.$PATCH"
}

# Menu
echo "Select version update type:"
echo "1) Major release (1.0.0 -> 2.0.0)"
echo "2) Minor release (1.0.0 -> 1.1.0)"
echo "3) Patch release (1.0.0 -> 1.0.1)"
echo "4) Build number only"
echo "5) Custom version"
read -p "Choice [1-5]: " choice

case $choice in
    1)
        NEW_VERSION=$(increment_version $CURRENT_VERSION major)
        ;;
    2)
        NEW_VERSION=$(increment_version $CURRENT_VERSION minor)
        ;;
    3)
        NEW_VERSION=$(increment_version $CURRENT_VERSION patch)
        ;;
    4)
        NEW_VERSION=$CURRENT_VERSION
        ;;
    5)
        read -p "Enter new version (e.g., 1.2.3): " NEW_VERSION
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

# Auto-increment build number
NEW_BUILD=$((CURRENT_BUILD + 1))

# Option to use custom build number
read -p "Use auto build number $NEW_BUILD? [Y/n]: " use_auto
if [[ $use_auto == "n" || $use_auto == "N" ]]; then
    read -p "Enter build number: " NEW_BUILD
fi

echo ""
echo -e "${YELLOW}New version will be: $NEW_VERSION+$NEW_BUILD${NC}"
read -p "Proceed? [Y/n]: " confirm

if [[ $confirm == "n" || $confirm == "N" ]]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "Updating version numbers..."

# Update pubspec.yaml
sed -i.bak "s/^version: .*/version: $NEW_VERSION+$NEW_BUILD/" $PUBSPEC_PATH
echo "✓ Updated pubspec.yaml"

# Update Android build.gradle
sed -i.bak "s/versionCode .*/versionCode $NEW_BUILD/" $ANDROID_GRADLE
sed -i.bak "s/versionName .*/versionName \"$NEW_VERSION\"/" $ANDROID_GRADLE
echo "✓ Updated Android build.gradle"

# Update iOS Info.plist (via Flutter)
# Flutter handles this automatically from pubspec.yaml

# Git tag
read -p "Create git tag v$NEW_VERSION? [Y/n]: " create_tag
if [[ $create_tag != "n" && $create_tag != "N" ]]; then
    git add $PUBSPEC_PATH $ANDROID_GRADLE
    git commit -m "Release v$NEW_VERSION+$NEW_BUILD"
    git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"
    echo "✓ Created git tag v$NEW_VERSION"
fi

# Generate changelog entry
echo ""
echo "Generating changelog entry..."
cat > RELEASE_NOTES_v$NEW_VERSION.md << EOF
# Release Notes - v$NEW_VERSION

## Date: $(date +"%Y-%m-%d")
## Build: $NEW_BUILD

### What's New
- [Add new features here]

### Improvements
- [Add improvements here]

### Bug Fixes
- [Add bug fixes here]

### Platform Updates
- iOS: Build $NEW_BUILD
- Android: Build $NEW_BUILD

---
EOF

echo "✓ Created RELEASE_NOTES_v$NEW_VERSION.md"

echo ""
echo -e "${GREEN}✅ Version updated successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit RELEASE_NOTES_v$NEW_VERSION.md"
echo "2. Run: ./scripts/one_click_release.sh"
echo "3. Upload to TestFlight/Play Console"

# Clean up backup files
rm -f $PUBSPEC_PATH.bak $ANDROID_GRADLE.bak 2>/dev/null || true
