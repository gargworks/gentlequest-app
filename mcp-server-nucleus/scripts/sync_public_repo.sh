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

# ── cli.py: Strip Claude Code provider secrets ──
CLI="src/mcp_server_nucleus/cli.py"
if [ -f "$CLI" ]; then
    # Remove --dangerously-skip-permissions flag from subprocess call
    sed -i '' 's/, "--dangerously-skip-permissions"//' "$CLI"
    # Remove claude-code and local from argparse choices
    sed -i '' "s/'gemini', 'anthropic', 'groq', 'claude-code', 'local'/'gemini', 'anthropic', 'groq'/" "$CLI"
    # Strip "claude-code (Max sub)" from help text
    sed -i '' 's/, or claude-code (Max sub)//' "$CLI"
    # Strip "free via Max subscription" from /provider help
    sed -i '' 's/(free via Max subscription)//' "$CLI"
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
    echo "  Sanitized: $CLI (claude-code provider refs)"
fi

# ── orchestrator.py: Strip Third Brother routing ──
ORCH="src/mcp_server_nucleus/runtime/orchestrator.py"
if [ -f "$ORCH" ]; then
    sed -i '' '/Third Brother/d' "$ORCH"
    sed -i '' '/LocalLLM/d' "$ORCH"
    sed -i '' '/_local_available/d' "$ORCH"
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

# ── cli.py: Strip archive/Third Brother/DPO references ──
if [ -f "$CLI" ]; then
    # Remove archive_pipeline import + record_turn block (try/except wrapped, safe to strip)
    sed -i '' '/archive_pipeline/d' "$CLI"
    sed -i '' '/Third Brother/d' "$CLI"
    sed -i '' '/training.flywheel/d' "$CLI"
    # Remove the archive subparser block entirely
    sed -i '' "/ARCHIVE COMMAND/,/archive_record.add_argument.*decisions/d" "$CLI"
    # Remove archive dispatch
    sed -i '' "/cli_command == 'archive'/d" "$CLI"
    sed -i '' '/handle_archive_command/d' "$CLI"
    # Strip DPO preference capture (private training infrastructure)
    sed -i '' '/DPO/d' "$CLI"
    sed -i '' '/_retry_rejected/d' "$CLI"
    sed -i '' '/_retry_prompt/d' "$CLI"
    sed -i '' '/_DPOArchive/d' "$CLI"
    sed -i '' '/record_preference/d' "$CLI"
    sed -i '' '/is_correction/d' "$CLI"
    sed -i '' '/dpo_count/d' "$CLI"
    sed -i '' '/count_preferences/d' "$CLI"
    sed -i '' '/preference pair/d' "$CLI"
    sed -i '' '/export_dpo/d' "$CLI"
    sed -i '' '/get_preference_stats/d' "$CLI"
    # Strip CoT/reasoning chain refs (Phase 5 training)
    sed -i '' '/CoT/d' "$CLI"
    sed -i '' '/_reasoning_steps/d' "$CLI"
    sed -i '' '/_reasoning_prompt/d' "$CLI"
    sed -i '' '/_CoTArchive/d' "$CLI"
    sed -i '' '/record_reasoning_chain/d' "$CLI"
    sed -i '' '/COT_CAPTURE/d' "$CLI"
    sed -i '' '/cot-status/d' "$CLI"
    sed -i '' '/cot-export/d' "$CLI"
    sed -i '' '/cot_count/d' "$CLI"
    sed -i '' '/cot_flag/d' "$CLI"
    sed -i '' '/count_reasoning/d' "$CLI"
    sed -i '' '/reasoning chain/d' "$CLI"
    sed -i '' '/get_reasoning/d' "$CLI"
    sed -i '' '/export_reasoning/d' "$CLI"
    sed -i '' '/Chain-of-Thought/d' "$CLI"
    sed -i '' '/mine_preferences/d' "$CLI"
    sed -i '' '/mine_reasoning/d' "$CLI"
    sed -i '' "/'mine'/d" "$CLI"
    sed -i '' '/MINING/d' "$CLI"
    # Strip eval harness (Phase 6) — block delete + subparser + help lines
    sed -i '' '/EVAL_BLOCK_START/,/EVAL_BLOCK_END/d' "$CLI"
    sed -i '' '/archive_eval/d' "$CLI"
    sed -i '' '/eval_results/d' "$CLI"
    sed -i '' '/eval_suite/d' "$CLI"
    sed -i '' '/generate_eval_suite/d' "$CLI"
    sed -i '' '/export_eval_suite/d' "$CLI"
    sed -i '' '/run_eval/d' "$CLI"
    sed -i '' '/EVAL BENCHMARK/d' "$CLI"
    sed -i '' '/eval_path/d' "$CLI"
    sed -i '' '/eval\.jsonl/d' "$CLI"
    sed -i '' '/eval pairs/d' "$CLI"
    sed -i '' '/eval chains/d' "$CLI"
    sed -i '' '/archive eval/d' "$CLI"
    # Strip self-play synthesis (Phase 7) — block delete + subparser + help lines
    sed -i '' '/SYNTH_BLOCK_START/,/SYNTH_BLOCK_END/d' "$CLI"
    sed -i '' '/archive_synth/d' "$CLI"
    sed -i '' '/synthesize_preferences/d' "$CLI"
    sed -i '' '/self_play/d' "$CLI"
    sed -i '' '/SELF-PLAY/d' "$CLI"
    sed -i '' '/Manufacturing DPO/d' "$CLI"
    sed -i '' '/archive synthesize/d' "$CLI"
    # Strip SPIN / iterative self-play (Phase 8)
    sed -i '' '/SPIN_BLOCK_START/,/SPIN_BLOCK_END/d' "$CLI"
    sed -i '' '/archive_spin/d' "$CLI"
    sed -i '' '/iterative_self_play/d' "$CLI"
    sed -i '' '/SPIN/d' "$CLI"
    sed -i '' '/spin_round/d' "$CLI"
    sed -i '' '/spin_count/d' "$CLI"
    sed -i '' '/archive spin/d' "$CLI"
    # Strip active learning (Phase 9)
    sed -i '' '/ACTIVE_LEARN_BLOCK_START/,/ACTIVE_LEARN_BLOCK_END/d' "$CLI"
    sed -i '' '/archive_active/d' "$CLI"
    sed -i '' '/active-learn/d' "$CLI"
    sed -i '' '/active_learn/d' "$CLI"
    sed -i '' '/identify_weaknesses/d' "$CLI"
    sed -i '' '/synthesize_for_weaknesses/d' "$CLI"
    sed -i '' '/ACTIVE LEARNING/d' "$CLI"
    # Strip LLM-as-Judge refs
    sed -i '' '/build_judge_fn/d' "$CLI"
    sed -i '' '/LLM-as-Judge/d' "$CLI"
    sed -i '' '/judge_model_fn/d' "$CLI"
    # Strip Training Conductor (Phase 10)
    sed -i '' '/CONDUCTOR_BLOCK_START/,/CONDUCTOR_BLOCK_END/d' "$CLI"
    sed -i '' '/archive_conductor/d' "$CLI"
    sed -i '' '/archive conductor/d' "$CLI"
    sed -i '' '/TRAINING CONDUCTOR/d' "$CLI"
    sed -i '' '/training_status/d' "$CLI"
    # Strip Training Pipeline (Phase 10)
    sed -i '' '/PIPELINE_BLOCK_START/,/PIPELINE_BLOCK_END/d' "$CLI"
    sed -i '' '/archive_pipeline/d' "$CLI"
    sed -i '' '/archive pipeline/d' "$CLI"
    sed -i '' '/TRAINING PIPELINE/d' "$CLI"
    sed -i '' '/run_full_pipeline/d' "$CLI"
    sed -i '' '/pipe_provider/d' "$CLI"
    sed -i '' '/pipe_judge/d' "$CLI"
    sed -i '' '/pipe_dry_run/d' "$CLI"
    # Strip Constitutional AI (Phase 11)
    sed -i '' '/CONSTITUTIONAL_BLOCK_START/,/CONSTITUTIONAL_BLOCK_END/d' "$CLI"
    sed -i '' '/archive_constitutional/d' "$CLI"
    sed -i '' '/constitutional_revise/d' "$CLI"
    sed -i '' '/constitutional_hash/d' "$CLI"
    sed -i '' '/CONSTITUTIONAL/d' "$CLI"
    sed -i '' '/CONSTITUTION/d' "$CLI"
    sed -i '' '/archive constitutional/d' "$CLI"
    # Strip Data Quality Scoring (Phase 11)
    sed -i '' '/QUALITY_BLOCK_START/,/QUALITY_BLOCK_END/d' "$CLI"
    sed -i '' '/archive_quality/d' "$CLI"
    sed -i '' '/score_training_data/d' "$CLI"
    sed -i '' '/export_filtered/d' "$CLI"
    sed -i '' '/DATA QUALITY/d' "$CLI"
    sed -i '' '/min_quality/d' "$CLI"
    sed -i '' '/archive quality/d' "$CLI"
    echo "  Sanitized: $CLI (all training refs: DPO/CoT/mine/eval/synth/spin/active/conductor/pipeline/constitutional/quality)"
fi

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
    sed -i '' '/archive_pipeline/d' "$DAEMON"
    sed -i '' '/should_retrain/d' "$DAEMON"
    sed -i '' '/Third Brother/d' "$DAEMON"
    sed -i '' '/training_status/d' "$DAEMON"
    sed -i '' '/Training Conductor/d' "$DAEMON"
    sed -i '' '/conductor_signal/d' "$DAEMON"
    sed -i '' '/next_action/d' "$DAEMON"
    sed -i '' '/sft_turns/d' "$DAEMON"
    sed -i '' '/dpo_pairs/d' "$DAEMON"
    sed -i '' '/cot_quality/d' "$DAEMON"
    SANITIZE_COUNT=$((SANITIZE_COUNT + 1))
    echo "  Sanitized: $DAEMON (training conductor hook)"
fi
BRIEF="src/mcp_server_nucleus/runtime/morning_brief_ops.py"
if [ -f "$BRIEF" ]; then
    sed -i '' '/archive_pipeline/d' "$BRIEF"
    sed -i '' '/should_retrain/d' "$BRIEF"
    sed -i '' '/Third Brother/d' "$BRIEF"
    sed -i '' '/THIRD BROTHER/d' "$BRIEF"
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
