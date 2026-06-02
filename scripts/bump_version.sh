#!/bin/bash
# bump_version.sh patch|minor|major
#
# Bumps ai_buddy_web/pubspec.yaml version (semver) + creates an
# app_store_assets/v<new>/RELEASE_NOTES.md stub for release_mobile.sh
# to auto-load from on the next release_mobile.sh public invocation.
#
# Usage:
#   ./scripts/bump_version.sh           # defaults to patch
#   ./scripts/bump_version.sh patch     # 1.3.0 → 1.3.1
#   ./scripts/bump_version.sh minor     # 1.3.0 → 1.4.0
#   ./scripts/bump_version.sh major     # 1.3.0 → 2.0.0
#
# Build number is auto-generated as YYMMDDHH (date-stamped, strictly
# increasing across release cadence assumptions).

set -e

BUMP_TYPE="${1:-patch}"
PUBSPEC="ai_buddy_web/pubspec.yaml"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ ! -f "$PUBSPEC" ]; then
    echo -e "${RED}Error: $PUBSPEC not found. Run from repo root.${NC}"
    exit 1
fi

# Extract current version + build number from "version: 1.3.0+26051612"
CURRENT_LINE=$(grep -E '^version:' "$PUBSPEC" | head -1)
CURRENT_VERSION=$(echo "$CURRENT_LINE" | sed -E 's/version:[[:space:]]*([0-9.]+)\+([0-9]+).*/\1/')
CURRENT_BUILD=$(echo "$CURRENT_LINE" | sed -E 's/version:[[:space:]]*([0-9.]+)\+([0-9]+).*/\2/')

if [ -z "$CURRENT_VERSION" ] || [ -z "$CURRENT_BUILD" ]; then
    echo -e "${RED}Error: Could not parse version from $PUBSPEC line: $CURRENT_LINE${NC}"
    exit 1
fi

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

case "$BUMP_TYPE" in
    patch) PATCH=$((PATCH + 1)) ;;
    minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
    major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
    *) echo "Usage: $0 patch|minor|major"; exit 1 ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
NEW_BUILD=$(date +%y%m%d%H)

echo -e "${GREEN}Bumping pubspec:${NC} ${CURRENT_VERSION}+${CURRENT_BUILD} → ${NEW_VERSION}+${NEW_BUILD}"

# In-place update of pubspec.yaml (BSD/GNU sed compat via .bak)
sed -i.bak -E "s/^version:[[:space:]]*[0-9.]+\+[0-9]+.*/version: ${NEW_VERSION}+${NEW_BUILD}/" "$PUBSPEC"
rm -f "${PUBSPEC}.bak"

# Stage release notes stub
NOTES_DIR="app_store_assets/v${NEW_VERSION}"
NOTES_FILE="${NOTES_DIR}/RELEASE_NOTES.md"
mkdir -p "$NOTES_DIR"

if [ -f "$NOTES_FILE" ]; then
    echo -e "${YELLOW}ℹ️ ${NOTES_FILE} already exists — not overwriting${NC}"
else
    cat > "$NOTES_FILE" <<EOF
v${NEW_VERSION} — <one-line summary>

What's new:
• <change 1>
• <change 2>
• <change 3>

Bug fixes:
• <fix 1>
EOF
    echo -e "${GREEN}📝 Created ${NOTES_FILE}${NC} (edit before shipping)"
fi

echo ""
echo "Next steps:"
echo "  1. Edit ${NOTES_FILE} with the real release notes"
echo "  2. git commit -am \"release: v${NEW_VERSION}\""
echo "  3. ./scripts/release_mobile.sh public   # auto-loads release notes from filesystem"
