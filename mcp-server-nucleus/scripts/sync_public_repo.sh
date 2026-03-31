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

# 3b. Feature Exposure Sanitization (public copy only)
# ─────────────────────────────────────────────────────────────────
# Strips sensitive strings from files that are too coupled to
# export-ignore (cli.py, tool_tiers.py). Only modifies the TARGET
# (public copy). The private repo (mcp-server-nucleus) is NEVER touched.
#
# WHY each patch exists:
#   tool_tiers.py — Plaintext beta token names in docstring + SHA256
#                   hashes let anyone unlock tier 1/2 from source.
#                   Public build defaults to tier 0 (all tiers via
#                   hosted API only).
#   cli.py        — Claude Code subprocess trick with
#                   --dangerously-skip-permissions is our #1 moat.
#                   Also strips "claude-code" from argparse choices
#                   so it's not advertised as a provider option.
#
# TO RE-ENABLE a feature for public: remove the relevant sed block
# below and verify via validate_public_surface.sh.
# ─────────────────────────────────────────────────────────────────
echo -e "${BLUE}🔒 Sanitizing feature exposure in target...${NC}"
cd "$TARGET_REPO"
SANITIZE_COUNT=0

# ── tool_tiers.py: Strip beta token names and hash values ──
TT="src/mcp_server_nucleus/tool_tiers.py"
if [ -f "$TT" ]; then
    # Plaintext token names in docstring → generic placeholder
    sed -i '' 's/- "sovereign-launch-alpha":   Tier 1/- (set NUCLEUS_BETA_TOKEN):    Tier 1/' "$TT"
    sed -i '' 's/- "titan-sovereign-godmode":  Tier 2/- (set NUCLEUS_BETA_TOKEN):    Tier 2/' "$TT"
    # SHA256 hash values → env-var lookup (hash not readable from source)
    sed -i '' 's/token_hash == "72904664178873eb"/token_hash == os.environ.get("_NT2H", "")/' "$TT"
    sed -i '' 's/token_hash == "ded5b57a0e65ab5d"/token_hash == os.environ.get("_NT1H", "")/' "$TT"
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
    echo "  Sanitized: $TT (token hashes + names)"
fi

# ── cli.py: AST-guided sanitization (replaces sed line-deletion) ──
CLI="src/mcp_server_nucleus/cli.py"
if [ -f "$CLI" ]; then
    # Use Python AST sanitizer — handles text replacement, function removal,
    # surgical block deletion, and orphaned-syntax repair in one pass.
    # This replaces ~200 individual sed commands that broke Python control flow.
    SANITIZER="$SCRIPT_DIR/sanitize_cli.py"
    if [ -f "$SANITIZER" ]; then
        python3 "$SANITIZER" "$CLI"
    else
        echo "  ERROR: sanitize_cli.py not found at $SANITIZER" >&2
        exit 1
    fi
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
fi

# ── orchestrator.py: Strip Third Brother routing ──
ORCH="src/mcp_server_nucleus/runtime/orchestrator.py"
if [ -f "$ORCH" ]; then
    # Replace entire _get_best_model method with simplified version
    python3 -c "
import re
with open('$ORCH') as f: code = f.read()
# Replace the _get_best_model method
code = re.sub(
    r'    def _get_best_model\(self.*?\n(    def )',
    '''    def _get_best_model(self, job_type: str = \"ORCHESTRATION\"):
        \"\"\"Get the best available LLM for the given job type.\"\"\"
        from .llm_client import DualEngineLLM
        return DualEngineLLM(job_type=job_type)

\1''',
    code, flags=re.DOTALL
)
# Also strip remaining stray references
code = re.sub(r'.*Third Brother.*\n', '', code)
code = re.sub(r'.*_local_available.*\n', '', code)
code = re.sub(r'.*archive_pipeline.*\n', '', code)
with open('$ORCH', 'w') as f: f.write(code)
"
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
    echo "  Sanitized: $ORCH (Third Brother routing)"
fi

# ── llm_client.py: Strip LocalLLM (Third Brother provider) ──
LLM="src/mcp_server_nucleus/runtime/llm_client.py"
if [ -f "$LLM" ]; then
    # Remove the entire LocalLLM class block
    sed -i '' '/^class LocalLLM:/,/^def get_llm_client/{ /^def get_llm_client/!d; }' "$LLM"
    # Remove local/third-brother from factory
    sed -i '' '/third-brother/d' "$LLM"
    sed -i '' "s/, LocalLLM//" "$LLM"
    sed -i '' "s/'gemini', 'anthropic', 'groq', 'local'/'gemini', 'anthropic', 'groq'/" "$LLM"
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
    echo "  Sanitized: $LLM (LocalLLM/Third Brother provider)"
fi

# ── cli.py sed sanitization removed ──
# All cli.py sanitization is now handled by sanitize_cli.py (AST-guided) above.
# The old approach used ~160 sed '/pattern/d' commands that broke Python
# try/except/else/finally control flow. See sanitize_cli.py for details.

# ── engram_hooks.py: Strip training archive bridge (block delete) ──
HOOKS="src/mcp_server_nucleus/runtime/engram_hooks.py"
if [ -f "$HOOKS" ]; then
    # Remove the entire TRAINING ARCHIVE BRIDGE section via python (sed can't match unicode ═)
    python3 -c "
import re, pathlib
p = pathlib.Path('$HOOKS')
txt = p.read_text()
# Remove the block between TRAINING ARCHIVE BRIDGE and METRICS & MONITORING headers
txt = re.sub(r'# .*TRAINING ARCHIVE BRIDGE.*?\n# .*METRICS & MONITORING', '# METRICS & MONITORING', txt, flags=re.DOTALL)
# Remove the call site
txt = re.sub(r'.*_record_to_training_archive.*\n', '', txt)
txt = re.sub(r'.*Feed high-value events.*\n', '', txt)
p.write_text(txt)
"
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
    echo "  Sanitized: $HOOKS (training archive bridge)"
fi

# ── daemon.py + morning_brief_ops.py: Strip Third Brother retrain blocks ──
DAEMON="src/mcp_server_nucleus/runtime/daemon.py"
if [ -f "$DAEMON" ]; then
    # Block-delete the entire Training Conductor block (safe range delete)
    sed -i '' '/TRAINING_CONDUCTOR_START/,/TRAINING_CONDUCTOR_END/d' "$DAEMON"
    # Catch any remaining stray references
    sed -i '' '/archive_pipeline/d' "$DAEMON"
    sed -i '' '/should_retrain/d' "$DAEMON"
    sed -i '' '/Third Brother/d' "$DAEMON"
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
    echo "  Sanitized: $DAEMON (training conductor hook)"
fi
BRIEF="src/mcp_server_nucleus/runtime/morning_brief_ops.py"
if [ -f "$BRIEF" ]; then
    sed -i '' '/archive_pipeline/d' "$BRIEF"
    sed -i '' '/Third Brother/d' "$BRIEF"
    sed -i '' '/THIRD BROTHER/d' "$BRIEF"
    # Delete entire training if/else block (should_retrain + its else) — keep indentation valid
    sed -i '' '/should_retrain/{N;N;N;d;}' "$BRIEF"
    # Delete the whole "Training status" section (from comment to empty line)
    sed -i '' '/# Training status/,/^$/{/^$/!d;}' "$BRIEF"
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
    echo "  Sanitized: $BRIEF (training status section)"
fi

# ── tools/__init__.py: Strip archive tool registration ──
TOOLS_INIT="src/mcp_server_nucleus/tools/__init__.py"
if [ -f "$TOOLS_INIT" ]; then
    sed -i '' '/archive/d' "$TOOLS_INIT"
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
    echo "  Sanitized: $TOOLS_INIT (archive module)"
fi

# ── README.md: Strip family architecture + cascade details ──
if [ -f "README.md" ]; then
    sed -i '' 's/Cascades across models on rate limit (70b → scout → qwen → 8b)/Cascades across models on rate limit/' "README.md"
    # Revert "Brother" naming to neutral "Chat" for public
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
