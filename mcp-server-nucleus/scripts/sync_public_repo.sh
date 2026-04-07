#!/bin/bash
# =============================================================================
# PRECISION SYNC PROTOCOL (PUBLIC REPO MIRROR)
# =============================================================================
# Safely mirrors the tracked codebase from this active development repository
# directly into the public release repository (nucleus-mcp).
#
# Mechanism: Uses `git archive` to ensure ONLY committed, tracked files are 
# transferred. Mathematically prevents leakage of .env, ledgers, .brain, and 
# uncommitted test files.
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define paths relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_REPO="$(dirname "$SCRIPT_DIR")"
TARGET_REPO="$(dirname "$SOURCE_REPO")/nucleus-mcp"

echo -e "${BLUE}🚀 Initiating Precision Sync Protocol${NC}"
echo "Source: $SOURCE_REPO"
echo "Target: $TARGET_REPO"
echo ""

# 1. Validation Checks
if [ ! -d "$TARGET_REPO" ] || [ ! -d "$TARGET_REPO/.git" ]; then
    echo -e "${RED}ERROR: Target repository not found at $TARGET_REPO${NC}"
    echo "Make sure nucleus-mcp is cloned side-by-side with mcp-server-nucleus."
    exit 1
fi

# Ensure source is clean (optional but recommended)
cd "$SOURCE_REPO"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}WARNING: You have uncommitted changes in the source repository.${NC}"
    echo "git archive will ONLY copy files that are currently committed."
    read -p "Do you want to continue anyway? [y/N]: " proceed
    if [[ "$proceed" != "y" && "$proceed" != "Y" ]]; then
        echo "Sync aborted."
        exit 1
    fi
fi

# 1b. Publication Protocol Gate (MANDATORY)
echo -e "${BLUE}🔒 Running Publication Protocol Gate...${NC}"
cd "$SOURCE_REPO"
if ! bash scripts/validate_public_surface.sh; then
    echo -e "${RED}BLOCKED: Publication Protocol Gate failed. Fix issues before syncing.${NC}"
    exit 1
fi
echo ""

# 1c. LLM Review Gate (runs if GEMINI_API_KEY or ANTHROPIC_API_KEY is set)
if [ -n "${GEMINI_API_KEY:-}" ] || [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo -e "${BLUE}🧠 Running LLM Review Gate (two-persona paranoid review)...${NC}"
    cd "$SOURCE_REPO"
    PROVIDER="gemini"
    [ -z "${GEMINI_API_KEY:-}" ] && PROVIDER="anthropic"
    if ! python3 scripts/llm_review_gate.py --quick --provider "$PROVIDER"; then
        echo -e "${RED}BLOCKED: LLM Review Gate found CRITICAL issues.${NC}"
        exit 1
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping LLM Review Gate (no API key set). Set GEMINI_API_KEY to enable.${NC}"
    echo ""
fi

# 2. Target Preparation (The Wipe)
echo -e "${BLUE}🧹 Wiping target repository working tree...${NC}"
cd "$TARGET_REPO"
# Reset to HEAD and clean untracked files
git reset --hard > /dev/null
git clean -fd > /dev/null
# Remove all tracked files to ensure deleted files in source are deleted in target
git ls-files | xargs rm -f

# 3. Source Extraction (The Precision Copy)
echo -e "${BLUE}📦 Extracting clean archive from source...${NC}"
cd "$SOURCE_REPO"
# git archive creates a tar of the HEAD tree, we pipe it to tar to extract in the target
git archive HEAD | tar -x -C "$TARGET_REPO"

# 3b. Minimal text sanitization (public copy only)
# ─────────────────────────────────────────────────────────────────
# Sovereign code lives in sovereign/ (export-ignored by .gitattributes).
# LocalLLM, PrivateGraphTrainer, handle_archive_command etc. are
# structurally excluded — no AST surgery or sed needed.
#
# Only two files need cosmetic text patches:
#   tool_tiers.py — Plaintext beta token names + SHA256 hashes
#   README.md     — "Brother" naming → "Chat" for public
# ─────────────────────────────────────────────────────────────────
echo -e "${BLUE}🔒 Sanitizing feature exposure in target...${NC}"
cd "$TARGET_REPO"
SANITIZE_COUNT=0

# ── tool_tiers.py: Strip beta token names and hash values ──
TT="src/mcp_server_nucleus/tool_tiers.py"
if [ -f "$TT" ]; then
    sed -i '' 's/- "sovereign-launch-alpha":   Tier 1/- (set NUCLEUS_BETA_TOKEN):    Tier 1/' "$TT"
    sed -i '' 's/- "titan-sovereign-godmode":  Tier 2/- (set NUCLEUS_BETA_TOKEN):    Tier 2/' "$TT"
    sed -i '' 's/token_hash == "72904664178873eb"/token_hash == os.environ.get("_NT2H", "")/' "$TT"
    sed -i '' 's/token_hash == "ded5b57a0e65ab5d"/token_hash == os.environ.get("_NT1H", "")/' "$TT"
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
    echo "  Sanitized: $TT (token hashes + names)"
fi

# ── README.md: Strip family architecture + cascade details ──
if [ -f "README.md" ]; then
    sed -i '' 's/Cascades across models on rate limit (70b → scout → qwen → 8b)/Cascades across models on rate limit/' "README.md"
    sed -i '' 's/nucleus brother/nucleus chat/g' "README.md"
    sed -i '' 's/Brother Interface/Interactive Chat/g' "README.md"
    sed -i '' 's/Talk to a Brother/Interactive AI chat/g' "README.md"
    sed -i '' 's/\*\*Brother\*\*/\*\*Chat\*\*/g' "README.md"
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
    echo "  Sanitized: README.md (cascade + family naming)"
fi

echo "  $SANITIZE_COUNT files sanitized."
echo ""

# 4. Staging
echo -e "${BLUE}📝 Staging changes in target repository...${NC}"
cd "$TARGET_REPO"
git add -A
STATUS=$(git status --porcelain)

if [ -z "$STATUS" ]; then
    echo -e "${YELLOW}No changes detected between the source and target repositories.${NC}"
    exit 0
fi

echo -e "${GREEN}✅ Synchronization complete!${NC}"
echo ""

# 5. Enforce Clean Author Config
CURRENT_NAME=$(git config user.name 2>/dev/null || echo "")
CURRENT_EMAIL=$(git config user.email 2>/dev/null || echo "")
if [[ "$CURRENT_NAME" != "Nucleus Team" || "$CURRENT_EMAIL" != "hello@nucleusos.dev" ]]; then
    echo -e "${YELLOW}⚠️  Setting clean author config in target repo...${NC}"
    git config user.name "Nucleus Team"
    git config user.email "hello@nucleusos.dev"
fi

echo "The changes have been staged in the nucleus-mcp repository."
echo "You can now navigate there to review and commit:"
echo ""
echo "  cd ../nucleus-mcp"
echo "  git status"
echo "  git diff --cached --stat"
echo "  git commit -m \"🚀 Sync: <your message>\""
echo "  git push origin main"
echo ""
echo -e "${RED}⛔ NEVER run 'git push' from the mono-repo to the public remote.${NC}"
echo -e "${RED}   This script is the ONLY safe way to sync.${NC}"
echo ""
