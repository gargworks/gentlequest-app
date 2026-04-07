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

# ── Auto mode: skip interactive prompts, auto-commit + push ──
AUTO_MODE=0
[ "$1" = "--auto" ] && AUTO_MODE=1

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define paths relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_REPO="$(dirname "$SCRIPT_DIR")"
TARGET_REPO="$(dirname "$SOURCE_REPO")/nucleus-mcp"

# ── Directory guard: ensure we're running from the PRIVATE repo ──
if [ ! -f "$SOURCE_REPO/src/mcp_server_nucleus/sovereign/status.py" ] 2>/dev/null &&
   [ ! -f "$SOURCE_REPO/scripts/sync_public_repo.sh" ]; then
    echo -e "${RED}FATAL: This script must run from mcp-server-nucleus (private repo).${NC}"
    echo "  Expected: $SOURCE_REPO/scripts/sync_public_repo.sh"
    exit 1
fi
if [ "$(cd "$SOURCE_REPO" && git remote get-url origin 2>/dev/null)" = "https://github.com/eidetic-works/nucleus-mcp.git" ]; then
    echo -e "${RED}FATAL: SOURCE_REPO points to the PUBLIC repo. Refusing to sync.${NC}"
    echo "  Source remote: $(cd "$SOURCE_REPO" && git remote get-url origin)"
    echo "  This script must run from the PRIVATE mcp-server-nucleus repo."
    exit 1
fi

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
    if [ "$AUTO_MODE" -eq 1 ]; then
        : # Auto mode: archive uses committed files only, uncommitted changes are expected
    else
        echo -e "${YELLOW}WARNING: You have uncommitted changes in the source repository.${NC}"
        echo "git archive will ONLY copy files that are currently committed."
        read -p "Do you want to continue anyway? [y/N]: " proceed
        if [[ "$proceed" != "y" && "$proceed" != "Y" ]]; then
            echo "Sync aborted."
            exit 1
        fi
    fi
fi

# 1b. Publication Protocol Gate (MANDATORY)
# Capture output to prevent drift warnings from consuming stdin for read prompts
echo -e "${BLUE}🔒 Running Publication Protocol Gate...${NC}"
cd "$SOURCE_REPO"
GATE_LOG=$(mktemp)
if ! bash scripts/validate_public_surface.sh > "$GATE_LOG" 2>&1; then
    echo -e "${RED}BLOCKED: Publication Protocol Gate failed:${NC}"
    cat "$GATE_LOG"
    rm -f "$GATE_LOG"
    exit 1
fi
# Show summary line only (RESULTS + PASSED/FAILED)
grep -E '(RESULTS|PASSED|FAILED|BLOCKED|FAIL)' "$GATE_LOG" || true
# Persist full log for review
GATE_LOG_SAVED="$SOURCE_REPO/.sync_gate_log_$(date +%Y%m%d_%H%M%S).txt"
mv "$GATE_LOG" "$GATE_LOG_SAVED"
echo "  Full gate log: $GATE_LOG_SAVED"
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

# 2. Deletion Safety Check
# Compare what's in the target vs what git archive would produce.
# Warn if files in the target would be deleted (indicates they aren't
# committed in the source — likely a back-port gap).
echo -e "${BLUE}🔍 Checking for files that would be deleted...${NC}"
cd "$SOURCE_REPO"
ARCHIVE_FILES=$(git archive HEAD | tar -tf - | sort)
cd "$TARGET_REPO"
TARGET_FILES=$(git ls-files | sort)
WOULD_DELETE=$(comm -23 <(echo "$TARGET_FILES") <(echo "$ARCHIVE_FILES") | grep -v '\.mcp\.json' || true)
if [ -n "$WOULD_DELETE" ]; then
    DEL_COUNT=$(echo "$WOULD_DELETE" | wc -l | tr -d ' ')
    if [ "$AUTO_MODE" -eq 1 ]; then
        echo "Auto-sync: $DEL_COUNT files will be removed from public (expected after export-ignore changes)"
    else
        echo -e "${RED}WARNING: $DEL_COUNT files in public repo are NOT in private git archive:${NC}"
        echo "$WOULD_DELETE"
        echo ""
        echo "These files will be DELETED from the public repo."
        echo "If this is unintentional, commit them in the private repo first."
        read -p "Continue with deletion? [y/N]: " del_proceed
        if [[ "$del_proceed" != "y" && "$del_proceed" != "Y" ]]; then
            echo "Sync aborted. Commit missing files first."
            exit 1
        fi
    fi
fi

# 3. Backup tag (recovery safety net)
cd "$TARGET_REPO"
BACKUP_TAG="pre-sync-$(date +%Y%m%d-%H%M%S)"
if ! git tag "$BACKUP_TAG" HEAD; then
    echo -e "${RED}FATAL: Could not create backup tag. Refusing to wipe.${NC}"
    exit 1
fi
echo -e "${BLUE}📌 Backup created: $BACKUP_TAG${NC}"
echo -e "${BLUE}   Restore: cd $TARGET_REPO && git reset --hard $BACKUP_TAG${NC}"

# ── Auto-restore trap: if anything fails after wipe, restore from backup ──
WIPE_STARTED=0
auto_restore() {
    if [ "$WIPE_STARTED" -eq 1 ]; then
        echo -e "${RED}SYNC FAILED — auto-restoring target from $BACKUP_TAG${NC}"
        cd "$TARGET_REPO"
        git reset --hard "$BACKUP_TAG" > /dev/null 2>&1
        git clean -fd > /dev/null 2>&1
        echo -e "${GREEN}Target restored to pre-sync state.${NC}"
    fi
}
trap auto_restore ERR

# 3b. Target Preparation (The Wipe)
echo -e "${BLUE}🧹 Wiping target repository working tree...${NC}"
WIPE_STARTED=1
# Reset to HEAD and clean untracked files
git reset --hard > /dev/null
git clean -fd > /dev/null
# Remove all tracked files to ensure deleted files in source are deleted in target
git ls-files | xargs rm -f

# 4. Source Extraction (The Precision Copy)
echo -e "${BLUE}📦 Extracting clean archive from source...${NC}"
cd "$SOURCE_REPO"
# Verify we're in the right directory before archive
if [ ! -f "src/mcp_server_nucleus/__init__.py" ]; then
    echo -e "${RED}FATAL: Not in mcp-server-nucleus root. pwd=$(pwd)${NC}"
    echo -e "${BLUE}   Restoring target: cd $TARGET_REPO && git reset --hard $BACKUP_TAG${NC}"
    cd "$TARGET_REPO" && git reset --hard "$BACKUP_TAG" > /dev/null
    exit 1
fi
# git archive creates a tar of the HEAD tree, we pipe it to tar to extract in the target
git archive HEAD | tar -x -C "$TARGET_REPO"

# 4b. Text sanitization — ELIMINATED
# ─────────────────────────────────────────────────────────────────
# Token hashes moved to env vars, README cleaned in source.
# Archive output is now identical to public — zero sed patches needed.
# ─────────────────────────────────────────────────────────────────

# 5. Staging
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

# 6. Enforce Clean Author Config
CURRENT_NAME=$(git config user.name 2>/dev/null || echo "")
CURRENT_EMAIL=$(git config user.email 2>/dev/null || echo "")
if [[ "$CURRENT_NAME" != "Nucleus Team" || "$CURRENT_EMAIL" != "hello@nucleusos.dev" ]]; then
    echo -e "${YELLOW}⚠️  Setting clean author config in target repo...${NC}"
    git config user.name "Nucleus Team"
    git config user.email "hello@nucleusos.dev"
fi

# ── Auto mode: commit + push automatically ──
if [ "$AUTO_MODE" -eq 1 ]; then
    PRIVATE_MSG=$(cd "$SOURCE_REPO" && git log --format='%s' -1)
    git commit -m "sync: $PRIVATE_MSG" --allow-empty-message > /dev/null 2>&1
    if git push origin main > /dev/null 2>&1; then
        echo "Auto-sync pushed: sync: $PRIVATE_MSG"
    else
        echo -e "${RED}Auto-sync: push failed — manual push needed${NC}"
        exit 1
    fi
    exit 0
fi

echo "The changes have been staged in the nucleus-mcp repository."
echo "You can now navigate there to review and commit:"
echo ""
echo "  cd ../nucleus-mcp"
echo "  git status"
echo "  git diff --cached --stat"
echo "  git commit -m \"sync: <your message>\""
echo "  git push origin main"
echo ""
echo -e "${RED}⛔ NEVER run 'git push' from the mono-repo to the public remote.${NC}"
echo -e "${RED}   This script is the ONLY safe way to sync.${NC}"
echo ""
