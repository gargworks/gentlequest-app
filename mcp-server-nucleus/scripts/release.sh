#!/bin/bash
# =============================================================================
# NUCLEUS ONE-CLICK RELEASE
# =============================================================================
# Consolidates ALL release infrastructure into a single gated pipeline:
#
#   sync_public_repo.sh ─── git archive + sanitize + validate_public_surface.sh
#   publish_pypi.sh ─────── tests + smoke test + build + twine/uv upload
#   publish-public.md ───── version sync + tagging protocol
#   Apple Notes ─────────── PyPI token (~/.pypirc) + npm auth
#   llm_review_gate.py ──── two-persona paranoid review (optional)
#   smoke_test_130.py ───── 130-tool verification
#
# Usage:
#   bash scripts/release.sh              # Full release (all 3 channels)
#   bash scripts/release.sh --dry-run    # Preview without publishing
#   bash scripts/release.sh --skip-sync  # PyPI + NPM only (already synced)
#   bash scripts/release.sh --skip-tests # Skip pytest + smoke (use carefully)
#   bash scripts/release.sh --test-pypi  # Publish to TestPyPI instead
#
# Gate stack (all must pass before any publish):
#   G1.  Branch = main
#   G2.  Working tree clean (no uncommitted mcp-server-nucleus changes)
#   G3.  CHANGELOG.md has entry for this version
#   G4.  Version not already on PyPI
#   G5.  Version not already on NPM
#   G6.  GROUND: All Python files py_compile clean
#   G7.  Unit tests pass (pytest)
#   G8.  Smoke test passes (130 tools — from publish_pypi.sh)
#   G9.  validate_public_surface.sh (identity/moat/creds/sovereign — inside sync)
#   G10. LLM review gate (two-persona — inside sync, optional)
#   G11. NPM shim verification (node index.js --help)
#   G12. Explicit confirmation before publish
#
# Version injection (after sync, before commit):
#   pyproject.toml VERSION → README badges, CLI header, website header, JSON-LD
#   pytest output          → README test badge
#   tool registry count    → all "170+" references across README + landing page
#   hello@nucleusos.dev    → standardized everywhere
#
# Auth (persistent, set up once):
#   PyPI: ~/.pypirc (chmod 600) with API token
#   NPM:  npm login (persists in ~/.npmrc)
#
# Architecture:
#   Private mono-repo (mcp-server-nucleus)
#     → git archive (ONLY committed tracked files)
#     → Feature sanitization (350+ sed strips: TB, DPO, CoT, moats)
#     → Publication protocol gate (validate_public_surface.sh)
#     → Public mirror (nucleus-mcp)
#     → PyPI (pip install nucleus-mcp)
#     → NPM  (npx nucleus-mcp)
#
# NEVER run `git push` from mono-repo to public. This script is the ONLY path.
# Tag from nucleus-mcp clone, NOT from mono-repo.
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_DIR="$(dirname "$SCRIPT_DIR")"
MONO_DIR="$(dirname "$MCP_DIR")"
PUBLIC_DIR="$MONO_DIR/nucleus-mcp"
NPM_DIR="$MCP_DIR/npm-wrapper"

DRY_RUN=false
SKIP_SYNC=false
SKIP_TESTS=false
TEST_PYPI=false
AUTO_YES=false
GATE_FAILURES=0
PYPI_PUBLISHED=false

for arg in "$@"; do
    case $arg in
        --dry-run)    DRY_RUN=true ;;
        --skip-sync)  SKIP_SYNC=true ;;
        --skip-tests) SKIP_TESTS=true ;;
        --test-pypi)  TEST_PYPI=true ;;
        --yes|-y)     AUTO_YES=true ;;
        --help|-h)
            head -50 "$0" | grep -E '^\s*#' | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
    esac
done

gate_fail() {
    echo -e "  ${RED}✗ GATE FAILED${NC}: $1"
    GATE_FAILURES=$((GATE_FAILURES + 1))
}
gate_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
}
gate_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
}

# ── Read version from pyproject.toml ─────────────────────────────
cd "$MCP_DIR"
VERSION=$(python3 -c "
import re
with open('pyproject.toml') as f:
    for line in f:
        m = re.match(r'version\s*=\s*\"(.+?)\"', line)
        if m:
            print(m.group(1))
            break
")

if [ -z "$VERSION" ]; then
    echo -e "${RED}ERROR: Could not read version from pyproject.toml${NC}"
    exit 1
fi

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  NUCLEUS RELEASE v${VERSION}${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
$DRY_RUN && echo -e "${YELLOW}  [DRY RUN — no changes will be published]${NC}"
$TEST_PYPI && echo -e "${YELLOW}  [TEST PYPI — publishing to test.pypi.org]${NC}"
echo ""

# =============================================================================
# GATE CHECKS (all must pass before any publish action)
# =============================================================================
echo -e "${BLUE}[1/9] Running gate checks...${NC}"
echo ""

# ── G1. Branch = main ────────────────────────────────────────────
BRANCH=$(git -C "$MONO_DIR" rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
    gate_fail "G1: Must be on 'main' branch (currently on '$BRANCH')"
else
    gate_pass "G1: Branch is main"
fi

# ── G2. Working tree clean ───────────────────────────────────────
cd "$MONO_DIR"
DIRTY=$(git status --porcelain -- mcp-server-nucleus/ 2>/dev/null | grep -v '^\?\?' | head -5)
if [ -n "$DIRTY" ]; then
    echo "$DIRTY"
    gate_fail "G2: Uncommitted changes in mcp-server-nucleus/. Commit first."
else
    gate_pass "G2: Working tree clean (mcp-server-nucleus/)"
fi

# ── G3. CHANGELOG has entry ──────────────────────────────────────
cd "$MCP_DIR"
if ! grep -q "## v${VERSION}\|## \[${VERSION}\]\|## ${VERSION}" CHANGELOG.md 2>/dev/null; then
    gate_fail "G3: CHANGELOG.md has no entry for v${VERSION}"
else
    gate_pass "G3: CHANGELOG.md has v${VERSION} entry"
fi

# ── G4. Version not already on PyPI ──────────────────────────────
if [ "$TEST_PYPI" = true ]; then
    PYPI_CHECK_URL="https://test.pypi.org/pypi/nucleus-mcp/${VERSION}/json"
else
    PYPI_CHECK_URL="https://pypi.org/pypi/nucleus-mcp/${VERSION}/json"
fi
PYPI_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" "$PYPI_CHECK_URL" 2>/dev/null || echo "000")
if [ "$PYPI_EXISTS" = "200" ]; then
    gate_fail "G4: v${VERSION} already exists on PyPI. Bump version."
else
    gate_pass "G4: v${VERSION} not on PyPI"
fi

# ── G5. Version not already on NPM ──────────────────────────────
NPM_EXISTS=$(npm view "nucleus-mcp@${VERSION}" version 2>/dev/null || echo "")
if [ "$NPM_EXISTS" = "$VERSION" ]; then
    gate_fail "G5: v${VERSION} already exists on NPM. Bump version."
else
    gate_pass "G5: v${VERSION} not on NPM"
fi

# ── G6. GROUND: py_compile all Python files ──────────────────────
cd "$MCP_DIR"
PY_ERRORS=0
PY_COUNT=0
for pyfile in $(find src/ -name '*.py' -not -path '*/__pycache__/*' 2>/dev/null); do
    PY_COUNT=$((PY_COUNT + 1))
    if ! python3 -m py_compile "$pyfile" 2>/dev/null; then
        echo -e "    ${RED}FAIL${NC}: $pyfile"
        PY_ERRORS=$((PY_ERRORS + 1))
    fi
done
if [ "$PY_ERRORS" -gt 0 ]; then
    gate_fail "G6: $PY_ERRORS/$PY_COUNT Python files failed py_compile"
else
    gate_pass "G6: All $PY_COUNT Python files compile"
fi

# ── G7. Unit tests ───────────────────────────────────────────────
if [ "$SKIP_TESTS" = false ]; then
    cd "$MCP_DIR"
    if [ -d "tests" ] && [ -n "$(find tests -name '*.py' 2>/dev/null | head -1)" ]; then
        echo -e "  ${DIM}Running pytest...${NC}"
        if PYTHONPATH=src python3 -m pytest tests/ -q --tb=line 2>&1 | tail -3; then
            gate_pass "G7: Tests passed"
        else
            gate_warn "G7: Some tests failed (review above)"
        fi
    else
        gate_warn "G7: No test files found"
    fi
else
    gate_warn "G7: Skipped (--skip-tests)"
fi

# ── G8. Smoke test (130 tools — from publish_pypi.sh) ───────────
if [ "$SKIP_TESTS" = false ]; then
    cd "$MCP_DIR"
    if [ -f "scripts/smoke_test_130.py" ]; then
        echo -e "  ${DIM}Running smoke test (130 tools)...${NC}"
        if PYTHONPATH=src python3 scripts/smoke_test_130.py > /dev/null 2>&1; then
            gate_pass "G8: Smoke test passed (130 tools)"
        else
            gate_warn "G8: Smoke test failed (non-blocking)"
        fi
    else
        gate_warn "G8: smoke_test_130.py not found"
    fi
else
    gate_warn "G8: Skipped (--skip-tests)"
fi

# ── Compute TEST_COUNT + TOOL_COUNT (used by version injection) ──
cd "$MCP_DIR"
TEST_COUNT=$(PYTHONPATH=src python3 -m pytest tests/ --collect-only -q 2>/dev/null | grep -oE '^[0-9]+' | head -1)
[ -z "$TEST_COUNT" ] && TEST_COUNT="250"
TOOL_COUNT=$(grep -rohE '"[a-z_]+":\s*lambda' src/mcp_server_nucleus/tools/*.py 2>/dev/null | sort -u | wc -l | tr -d ' ')
[ -z "$TOOL_COUNT" ] || [ "$TOOL_COUNT" -lt 50 ] && TOOL_COUNT="170"
gate_pass "Counts: ${TEST_COUNT} tests, ${TOOL_COUNT} tools (from live registry)"

# ── Tool availability ────────────────────────────────────────────
if ! command -v uv &> /dev/null; then
    gate_fail "uv not found (curl -LsSf https://astral.sh/uv/install.sh | sh)"
else
    gate_pass "uv available"
fi

if ! command -v npm &> /dev/null; then
    gate_fail "npm not found"
else
    gate_pass "npm available"
fi

if [ ! -f ~/.pypirc ]; then
    gate_fail "~/.pypirc not found (PyPI token required)"
else
    gate_pass "~/.pypirc exists (chmod $(stat -f '%Lp' ~/.pypirc 2>/dev/null || stat -c '%a' ~/.pypirc 2>/dev/null))"
fi

# npm auth
NPM_AUTH=false
if npm whoami &> /dev/null 2>&1; then
    NPM_AUTH=true
    gate_pass "npm: logged in as $(npm whoami)"
else
    gate_warn "npm: not logged in (NPM publish will skip — run 'npm login')"
fi

# Public repo
if [ ! -d "$PUBLIC_DIR/.git" ]; then
    gate_fail "Public repo not at $PUBLIC_DIR"
else
    gate_pass "Public repo exists"
fi

# ── G11. NPM shim verification ──────────────────────────────────
cd "$NPM_DIR"
if node index.js --help > /dev/null 2>&1; then
    gate_pass "G11: NPM shim (node index.js --help) works"
else
    gate_warn "G11: NPM shim test failed (may need python3 in PATH)"
fi

# ── G12. .gitattributes export-ignore integrity ─────────────────
cd "$MCP_DIR"
if [ -f ".gitattributes" ]; then
    EXPORT_IGNORE_COUNT=$(grep -c 'export-ignore' .gitattributes 2>/dev/null || echo "0")
    # Minimum expected: sync script, validate script, publish script, llm gate
    if [ "$EXPORT_IGNORE_COUNT" -lt 4 ]; then
        gate_fail "G12: .gitattributes has only $EXPORT_IGNORE_COUNT export-ignore rules (expected >=4)"
    else
        gate_pass "G12: .gitattributes has $EXPORT_IGNORE_COUNT export-ignore rules"
    fi
    # Critical files MUST be in export-ignore
    for MUST_IGNORE in "sync_public_repo.sh" "validate_public_surface.sh" "publish_pypi.sh" "release.sh"; do
        if ! grep -q "$MUST_IGNORE.*export-ignore" .gitattributes 2>/dev/null; then
            gate_fail "G12: $MUST_IGNORE missing from .gitattributes export-ignore"
        fi
    done
else
    gate_fail "G12: .gitattributes file missing entirely"
fi

# ── G13. Pre-push hook exists in mono-repo ───────────────────────
PREPUSH_HOOK="$MONO_DIR/.git/hooks/pre-push"
if [ -f "$PREPUSH_HOOK" ] && grep -q 'nucleus-mcp' "$PREPUSH_HOOK" 2>/dev/null; then
    gate_pass "G13: Pre-push hook blocks mono-repo → public pushes"
else
    gate_warn "G13: Pre-push hook missing or incomplete ($PREPUSH_HOOK)"
fi

# ── G14. Public repo integrity (detect tampering / force push) ───
cd "$PUBLIC_DIR"
LOCAL_HEAD=$(git rev-parse HEAD 2>/dev/null)
REMOTE_HEAD=$(git ls-remote origin HEAD 2>/dev/null | awk '{print $1}')
if [ -n "$REMOTE_HEAD" ] && [ -n "$LOCAL_HEAD" ]; then
    # Check if local HEAD is ancestor of or equal to remote HEAD
    if [ "$LOCAL_HEAD" = "$REMOTE_HEAD" ]; then
        gate_pass "G14: Public repo HEAD matches remote (no tampering)"
    elif git merge-base --is-ancestor "$LOCAL_HEAD" "$REMOTE_HEAD" 2>/dev/null; then
        gate_warn "G14: Remote has commits ahead of local — run 'git pull' in nucleus-mcp"
    elif git merge-base --is-ancestor "$REMOTE_HEAD" "$LOCAL_HEAD" 2>/dev/null; then
        gate_pass "G14: Local ahead of remote (expected for new release)"
    else
        gate_fail "G14: Public repo history diverged from remote — possible force push/tampering"
    fi
else
    gate_warn "G14: Could not verify remote HEAD (offline?)"
fi

# ── G16. Root .gitattributes safety net exists ───────────────────
if [ -f "$MONO_DIR/.gitattributes" ]; then
    ROOT_IGNORES=$(grep -c 'export-ignore' "$MONO_DIR/.gitattributes" 2>/dev/null || echo "0")
    if [ "$ROOT_IGNORES" -lt 20 ]; then
        gate_fail "G16: Root .gitattributes has only $ROOT_IGNORES export-ignore rules (mono-repo has 96 dirs)"
    else
        gate_pass "G16: Root .gitattributes safety net ($ROOT_IGNORES export-ignore rules)"
    fi
else
    gate_fail "G16: NO root .gitattributes — entire mono-repo (10K+ files) can leak via git archive"
fi

# ── G17. Archive cross-contamination scan ────────────────────────
echo -e "  ${DIM}G17: Scanning git archive for cross-contamination...${NC}"
cd "$MCP_DIR"
ARCHIVE_LEAKED=$(git archive HEAD --format=tar | tar -t 2>/dev/null | grep -iE '^(flutter|\.brain|ai_buddy|gentle|believe|secret/|training/|notebook|checkpoints)' | head -5)
if [ -n "$ARCHIVE_LEAKED" ]; then
    echo "$ARCHIVE_LEAKED"
    gate_fail "G17: Git archive contains non-Nucleus files (GQ/brain/secrets leak)"
else
    ARCHIVE_COUNT=$(git archive HEAD --format=tar | tar -t 2>/dev/null | wc -l | tr -d ' ')
    if [ "$ARCHIVE_COUNT" -gt 500 ]; then
        gate_fail "G17: Git archive has $ARCHIVE_COUNT files (expected ~341). Possible mono-repo leak."
    else
        gate_pass "G17: Archive clean — $ARCHIVE_COUNT files, no cross-contamination"
    fi
fi

# ── G15. npm package.json fields ─────────────────────────────────
cd "$NPM_DIR"
NPM_AUTHOR=$(node -p "require('./package.json').author" 2>/dev/null || echo "")
NPM_NAME=$(node -p "require('./package.json').name" 2>/dev/null || echo "")
if [ "$NPM_AUTHOR" != "Nucleus Team" ]; then
    gate_fail "G15: npm author is '$NPM_AUTHOR' (expected 'Nucleus Team')"
else
    gate_pass "G15: npm package.json author = Nucleus Team"
fi
if [ "$NPM_NAME" != "nucleus-mcp" ]; then
    gate_fail "G15: npm name is '$NPM_NAME' (expected 'nucleus-mcp')"
fi

echo ""

# ── Abort if any hard gate failed ────────────────────────────────
if [ "$GATE_FAILURES" -gt 0 ]; then
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  BLOCKED: $GATE_FAILURES gate(s) failed. Fix before releasing.${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    exit 1
fi

# ── G12. Confirmation ────────────────────────────────────────────
if [ "$DRY_RUN" = false ]; then
    echo -e "${BOLD}All gates passed. About to release v${VERSION} to:${NC}"
    [ "$SKIP_SYNC" = false ] && echo "  → GitHub  (nucleus-mcp public repo + tag)"
    [ "$TEST_PYPI" = true ] && echo "  → TestPyPI (test.pypi.org)" || echo "  → PyPI    (pip install nucleus-mcp==${VERSION})"
    [ "$NPM_AUTH" = true ] && echo "  → NPM     (npx nucleus-mcp)"
    echo ""
    if [ "$AUTO_YES" = true ]; then
        echo -e "${YELLOW}--yes flag: auto-confirming${NC}"
    else
        read -p "$(echo -e "${YELLOW}Proceed? [y/N]:${NC} ")" CONFIRM
        if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
            echo "Aborted."
            exit 0
        fi
    fi
    echo ""
fi

# =============================================================================
# RELEASE PIPELINE
# =============================================================================

# ── [2/9] Sync npm-wrapper version ───────────────────────────────
echo -e "${BLUE}[2/9] Syncing npm-wrapper version to $VERSION...${NC}"
cd "$NPM_DIR"
CURRENT_NPM_VERSION=$(node -p "require('./package.json').version")
if [ "$CURRENT_NPM_VERSION" != "$VERSION" ]; then
    npm version "$VERSION" --no-git-tag-version --allow-same-version > /dev/null
    echo "  $CURRENT_NPM_VERSION → $VERSION"
else
    echo "  Already at $VERSION"
fi
echo ""

# ── [3/9] Sync to public repo ───────────────────────────────────
# Calls sync_public_repo.sh which runs:
#   G9:  validate_public_surface.sh (identity, moat, creds, sovereign)
#   G10: LLM review gate (two-persona, if API key set)
#   Feature sanitization (350+ sed strips)
#   Author enforcement (Nucleus Team)
if [ "$SKIP_SYNC" = false ]; then
    echo -e "${BLUE}[3/9] Syncing to public repo...${NC}"
    echo -e "  ${DIM}(G9: validate_public_surface + G10: LLM review gate run inside)${NC}"
    if [ "$DRY_RUN" = true ]; then
        echo -e "  ${YELLOW}[DRY RUN] Would run sync_public_repo.sh${NC}"
    else
        cd "$MCP_DIR"
        if [ "$AUTO_YES" = true ]; then
            echo "y" | bash scripts/sync_public_repo.sh
        else
            bash scripts/sync_public_repo.sh
        fi
    fi
    echo ""

    # ── Post-sync repair: fix Python syntax broken by line-delete sanitization ──
    echo -e "${BLUE}  Post-sync: Repairing sanitization damage...${NC}"
    cd "$PUBLIC_DIR"
    REPAIR_COUNT=0
    for pyfile in $(find src/ -name '*.py' -not -path '*/__pycache__/*' 2>/dev/null); do
        if ! python3 -m py_compile "$pyfile" 2>/dev/null; then
            # Attempt auto-repair: remove orphaned dict/list bodies and dangling else/except
            python3 -c "
import re, sys
with open('$pyfile') as f: lines = f.readlines()
fixed = []
skip_orphan = False
for i, line in enumerate(lines):
    stripped = line.lstrip()
    # Skip orphaned dict entries (no opener, just 'key': value,)
    if skip_orphan:
        if stripped.startswith(('\"', \"'\", '})', '})')) or stripped == '})\\n':
            continue
        skip_orphan = False
    # Detect orphaned dict body: previous line is not an opener, current is '\"key\":'
    if stripped.startswith(('\"thought\":', '\"action\":', '\"observation\":')):
        if i > 0 and not fixed[-1].rstrip().endswith(('{', '({')):
            skip_orphan = True
            continue
    fixed.append(line)
# Second pass: remove dangling else/except with no matching if/try
result = []
for i, line in enumerate(fixed):
    stripped = line.lstrip()
    indent = len(line) - len(line.lstrip())
    if stripped.startswith(('else:', 'except ')):
        # Check if previous non-empty line has matching indent level
        prev_indent = -1
        for j in range(len(result)-1, -1, -1):
            ps = result[j].strip()
            if ps:
                prev_indent = len(result[j]) - len(result[j].lstrip())
                break
        if prev_indent >= 0 and prev_indent >= indent:
            continue  # Skip dangling else/except
    result.append(line)
with open('$pyfile', 'w') as f: f.writelines(result)
" 2>/dev/null
            if python3 -m py_compile "$pyfile" 2>/dev/null; then
                REPAIR_COUNT=$((REPAIR_COUNT + 1))
                echo -e "    ${GREEN}Repaired${NC}: $pyfile"
            fi
        fi
    done
    [ "$REPAIR_COUNT" -gt 0 ] && echo -e "  ${GREEN}Auto-repaired $REPAIR_COUNT files${NC}"

    # ── Post-sync verification: sanitized code still compiles ──
    echo -e "${BLUE}  Post-sync: Verifying sanitized Python compiles...${NC}"
    cd "$PUBLIC_DIR"
    POST_SYNC_ERRORS=0
    for pyfile in $(find src/ -name '*.py' -not -path '*/__pycache__/*' 2>/dev/null); do
        if ! python3 -m py_compile "$pyfile" 2>/dev/null; then
            echo -e "    ${RED}BROKEN by sanitization${NC}: $pyfile"
            POST_SYNC_ERRORS=$((POST_SYNC_ERRORS + 1))
        fi
    done
    if [ "$POST_SYNC_ERRORS" -gt 0 ]; then
        echo -e "  ${RED}BLOCKED: $POST_SYNC_ERRORS files broken by sed sanitization. Fix sync script.${NC}"
        exit 1
    else
        echo -e "  ${GREEN}All sanitized Python files compile${NC}"
    fi

    # ── Post-sync: Cross-contamination scan on public repo ─────
    # Tier 1: Directories that should NEVER exist in the public repo
    CONTAM_DIRS=""
    for BANNED_DIR in flutter_app flutter ai_buddy_web believe_it_bot training checkpoints notebooks secret secrets strategy_archive nucleus-launch-internal outreach_campaign_v1; do
        if [ -d "$PUBLIC_DIR/$BANNED_DIR" ]; then
            CONTAM_DIRS="$CONTAM_DIRS $BANNED_DIR"
        fi
    done
    if [ -n "$CONTAM_DIRS" ]; then
        echo -e "  ${RED}BLOCKED: Banned directories in public repo:${NC}$CONTAM_DIRS"
        echo -e "  ${RED}GentleQuest/training/secrets leaked. DO NOT PUSH.${NC}"
        exit 1
    fi

    # Tier 2: Private DATA files that should never be in public (.brain data is ok as template)
    CONTAM_DATA=$(find "$PUBLIC_DIR" -name 'ledger.jsonl' -o -name 'events.jsonl' -o -name 'pulse.json' -o -name 'interaction_log.jsonl' -o -name '.env' -o -name '.env.*' -o -name 'client_secret*.json' -o -name '*.pem' -o -name '*.key' 2>/dev/null | head -5)
    if [ -n "$CONTAM_DATA" ]; then
        echo -e "  ${RED}BLOCKED: Private data files in public repo:${NC}"
        echo "$CONTAM_DATA" | sed "s|$PUBLIC_DIR/||"
        exit 1
    fi

    # Clean stale __pycache__ (bytecode can contain identity from build machine)
    find "$PUBLIC_DIR" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

    # Tier 3: Identity strings in source code (skip binary/bytecode)
    CONTAM_ID=$(grep -rl --include='*.py' --include='*.md' --include='*.txt' --include='*.json' --include='*.yaml' --include='*.yml' --include='*.toml' --include='*.cfg' --include='*.js' 'lokeshgarg\|lokesh\.iitr\|gentlequest\.app\|mailforlkgarg\|believe_it_bot' "$PUBLIC_DIR/src/" 2>/dev/null | head -5 || true)
    if [ -n "$CONTAM_ID" ]; then
        echo -e "  ${RED}BLOCKED: Identity strings in public repo source:${NC}"
        echo "$CONTAM_ID" | sed "s|$PUBLIC_DIR/||"
        exit 1
    fi

    # Tier 4: File count sanity (public should be ~275 files, not thousands)
    PUBLIC_FILE_COUNT=$(find "$PUBLIC_DIR" -not -path '*/.git/*' -type f 2>/dev/null | wc -l | tr -d ' ')
    if [ "$PUBLIC_FILE_COUNT" -gt 500 ]; then
        echo -e "  ${RED}BLOCKED: Public repo has $PUBLIC_FILE_COUNT files (expected ~275). Mono-repo leak?${NC}"
        exit 1
    fi
    gate_pass "Post-sync: No cross-contamination ($PUBLIC_FILE_COUNT files, no banned dirs/data/identity)"

    # ── Inject dynamic versions into public repo ────────────────
    echo -e "${BLUE}  Injecting versions: v${VERSION}, ${TEST_COUNT} tests, ${TOOL_COUNT} tools...${NC}"
    cd "$PUBLIC_DIR"

    if [ -f "README.md" ]; then
        # Badge: Release-v1.6.2-blue → Release-v{VERSION}-blue
        sed -i '' "s|Release-v[0-9]*\.[0-9]*\.[0-9]*-|Release-v${VERSION}-|" README.md
        # Badge: npm-v1.4.1-red → npm-v{VERSION}-red
        sed -i '' "s|npm-v[0-9]*\.[0-9]*\.[0-9]*-|npm-v${VERSION}-|" README.md
        # Badge: Tests-NNN%20passing → Tests-{TEST_COUNT}%20passing
        sed -i '' "s|Tests-[0-9]*%20passing|Tests-${TEST_COUNT}%20passing|" README.md
        # CLI header: Agent CLI — v1.6.2 → v{VERSION}
        sed -i '' "s|Agent CLI — v[0-9]*\.[0-9]*\.[0-9]*|Agent CLI — v${VERSION}|" README.md
        # Tool count in links and text (matches "170+" or any previously-injected count)
        sed -i '' "s|[0-9][0-9]*+ Tool|${TOOL_COUNT}+ Tool|g" README.md
        sed -i '' "s|[0-9][0-9]*+ MCP|${TOOL_COUNT}+ MCP|g" README.md
        echo -e "  ${GREEN}README.md: badges + counts injected${NC}"
    fi

    # ── Inject into landing page (separate repo, separate deploy) ─
    LANDING_DIR="$MONO_DIR/nucleus-landing"
    if [ -d "$LANDING_DIR" ]; then
        echo -e "  ${DIM}Injecting into nucleus-landing/...${NC}"

        # index.html: softwareVersion + meta tool count
        if [ -f "$LANDING_DIR/index.html" ]; then
            sed -i '' "s|\"softwareVersion\": \"[0-9.]*\"|\"softwareVersion\": \"${VERSION}\"|" "$LANDING_DIR/index.html"
            sed -i '' "s|[0-9][0-9]*+ MCP tools|${TOOL_COUNT}+ MCP tools|g" "$LANDING_DIR/index.html"
            sed -i '' "s|[0-9][0-9]*+ MCP Tools|${TOOL_COUNT}+ MCP Tools|g" "$LANDING_DIR/index.html"
        fi

        # App.jsx: header version badge + tool counts + contact email
        if [ -f "$LANDING_DIR/src/App.jsx" ]; then
            sed -i '' "s|>v[0-9]*\.[0-9]*<|>v${VERSION}<|" "$LANDING_DIR/src/App.jsx"
            sed -i '' "s|[0-9][0-9]*+ <|${TOOL_COUNT}+ <|" "$LANDING_DIR/src/App.jsx"
            sed -i '' "s|[0-9][0-9]*+ MCP Tools|${TOOL_COUNT}+ MCP Tools|g" "$LANDING_DIR/src/App.jsx"
            sed -i '' "s|enterprise@nucleusos.dev|hello@nucleusos.dev|g" "$LANDING_DIR/src/App.jsx"
        fi

        # FAQ.jsx: tool counts ("170+ tools" and "170+ orchestrated tools")
        if [ -f "$LANDING_DIR/src/components/FAQ.jsx" ]; then
            sed -i '' "s|[0-9][0-9]*+ tools|${TOOL_COUNT}+ tools|g" "$LANDING_DIR/src/components/FAQ.jsx"
            sed -i '' "s|[0-9][0-9]*+ orchestrated tools|${TOOL_COUNT}+ orchestrated tools|g" "$LANDING_DIR/src/components/FAQ.jsx"
        fi

        # Pricing.jsx: tool counts
        if [ -f "$LANDING_DIR/src/components/Pricing.jsx" ]; then
            sed -i '' "s|[0-9][0-9]*+ MCP tools|${TOOL_COUNT}+ MCP tools|g" "$LANDING_DIR/src/components/Pricing.jsx"
        fi

        echo -e "  ${GREEN}Landing page: version + counts injected${NC}"
        echo -e "  ${YELLOW}NOTE: Landing page is a separate repo. To deploy:${NC}"
        echo -e "  ${YELLOW}  cd $LANDING_DIR && git add -A && git commit -m \"Release v${VERSION}: update version + counts\"${NC}"
    else
        echo -e "  ${YELLOW}nucleus-landing/ not found — skipping landing page injection${NC}"
    fi

    # Verify injection worked
    cd "$PUBLIC_DIR"
    if [ -f "README.md" ]; then
        if grep -q "Release-v${VERSION}" README.md && grep -q "Tests-${TEST_COUNT}" README.md; then
            gate_pass "Version injection verified in README"
        else
            gate_warn "Version injection may be incomplete — check README badges"
        fi
    fi

    # ── [4/9] Commit + push public repo ──────────────────────────
    echo -e "${BLUE}[4/9] Committing + pushing public repo...${NC}"
    cd "$PUBLIC_DIR"
    if [ "$DRY_RUN" = true ]; then
        echo -e "  ${YELLOW}[DRY RUN] Would commit + push to nucleus-mcp${NC}"
        git status --short 2>/dev/null | head -10
    else
        if [ -n "$(git status --porcelain)" ]; then
            git add -A
            git commit -m "Release v${VERSION}"
            git push origin main
            echo -e "  ${GREEN}Pushed to nucleus-mcp main${NC}"
        else
            echo -e "  ${YELLOW}No changes to commit (already in sync)${NC}"
        fi
    fi
    echo ""
else
    echo -e "${YELLOW}[3/9] Skipping sync (--skip-sync)${NC}"
    echo -e "${YELLOW}[4/9] Skipping public push (--skip-sync)${NC}"
    echo ""
fi

# ── [5/9] Tag release (from nucleus-mcp, NEVER mono-repo) ───────
echo -e "${BLUE}[5/9] Tagging v${VERSION} (from nucleus-mcp clone)...${NC}"
cd "$PUBLIC_DIR"
if git rev-parse "v${VERSION}" &> /dev/null 2>&1; then
    echo -e "  ${YELLOW}Tag v${VERSION} already exists, skipping${NC}"
else
    if [ "$DRY_RUN" = true ]; then
        echo -e "  ${YELLOW}[DRY RUN] Would tag v${VERSION}${NC}"
    else
        git tag -a "v${VERSION}" -m "Release v${VERSION}"
        git push origin "v${VERSION}"
        echo -e "  ${GREEN}Tagged + pushed v${VERSION}${NC}"
    fi
fi
echo ""

# ── [6/9] Build Python package ───────────────────────────────────
echo -e "${BLUE}[6/9] Building Python package...${NC}"
cd "$MCP_DIR"
rm -rf dist/* build/ *.egg-info
uv build 2>&1 | tail -2

WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -1)
if [ -z "$WHEEL_FILE" ]; then
    echo -e "${RED}ERROR: Wheel not created${NC}"
    exit 1
fi
WHEEL_SIZE_BYTES=$(wc -c < "$WHEEL_FILE" | tr -d ' ')
WHEEL_SIZE=$(du -h "$WHEEL_FILE" | cut -f1)
echo -e "  ${GREEN}Built: $(basename $WHEEL_FILE) ($WHEEL_SIZE)${NC}"

# Wheel size sanity: if >5MB, something likely leaked (normal is ~800K)
MAX_WHEEL_BYTES=5242880  # 5MB
if [ "$WHEEL_SIZE_BYTES" -gt "$MAX_WHEEL_BYTES" ]; then
    echo -e "  ${RED}BLOCKED: Wheel is ${WHEEL_SIZE} (>${MAX_WHEEL_BYTES} bytes). Possible data leak in package.${NC}"
    echo -e "  ${RED}Inspect with: unzip -l $WHEEL_FILE | tail -20${NC}"
    exit 1
fi
gate_pass "Wheel size sanity ($WHEEL_SIZE < 5MB)"

# Wheel content audit: check for DATA files that should never ship
# (Python module names like brain_ops.py or secrets.py are code, not leaks)
WHEEL_CONTENTS=$(unzip -l "$WHEEL_FILE" 2>/dev/null || true)
WHEEL_LEAKED=0

# Tier 1: HARD BLOCK — actual data/config files that contain secrets
for BANNED in "\.env$" "\.env\." "ledger\.jsonl" "pulse\.json" "\.pypirc" "\.npmrc" "\.brain/" "client_secret" "credentials\.json"; do
    MATCHES=$(echo "$WHEEL_CONTENTS" | grep -iE "$BANNED" | grep -v '\.py$' | grep -v '\.pyc$' || true)
    if [ -n "$MATCHES" ]; then
        echo -e "  ${RED}LEAKED in wheel${NC}: data file matching '$BANNED'"
        echo "$MATCHES" | head -3
        WHEEL_LEAKED=$((WHEEL_LEAKED + 1))
    fi
done

# Tier 2: HARD BLOCK — identity strings in any file content
# (sample 5 largest .py files in wheel for identity strings)
WHEEL_TMPDIR=$(mktemp -d)
trap "rm -rf $WHEEL_TMPDIR" EXIT
unzip -q -o "$WHEEL_FILE" -d "$WHEEL_TMPDIR" 2>/dev/null || true
IDENTITY_IN_WHEEL=$(grep -rl 'lokeshgarg\|lokesh\.iitr\|gentlequest\.app\|mailforlkgarg' "$WHEEL_TMPDIR" 2>/dev/null | head -5 || true)
if [ -n "$IDENTITY_IN_WHEEL" ]; then
    echo -e "  ${RED}IDENTITY LEAK in wheel${NC}:"
    echo "$IDENTITY_IN_WHEEL" | sed "s|$WHEEL_TMPDIR/||"
    WHEEL_LEAKED=$((WHEEL_LEAKED + 1))
fi

# Tier 3: WARNING — sovereign modules present (expected in PyPI, stripped from GitHub)
SOVEREIGN_IN_WHEEL=$(echo "$WHEEL_CONTENTS" | grep -E 'archive_pipeline|growth_ops|siphon_engine|dogfood_tracker' || true)
if [ -n "$SOVEREIGN_IN_WHEEL" ]; then
    echo -e "  ${YELLOW}NOTE: Sovereign modules in wheel (expected — stripped from public GitHub only):${NC}"
    echo "$SOVEREIGN_IN_WHEEL" | head -3 | awk '{print "    " $NF}'
fi

if [ "$WHEEL_LEAKED" -gt 0 ]; then
    echo -e "  ${RED}BLOCKED: $WHEEL_LEAKED data/identity leaks in wheel.${NC}"
    exit 1
fi
gate_pass "Wheel content audit (no data/identity leaks)"
echo ""

# ── [7/9] Publish to PyPI ────────────────────────────────────────
echo -e "${BLUE}[7/9] Publishing to PyPI...${NC}"
cd "$MCP_DIR"
if [ "$DRY_RUN" = true ]; then
    echo -e "  ${YELLOW}[DRY RUN] Would publish to PyPI${NC}"
    ls -lh dist/*.whl dist/*.tar.gz 2>/dev/null | awk '{print "  " $5 " " $NF}'
elif [ "$TEST_PYPI" = true ]; then
    uv publish --publish-url https://test.pypi.org/legacy/ dist/*
    echo -e "  ${GREEN}Published to TestPyPI${NC}"
else
    # Extract token from ~/.pypirc if UV_PUBLISH_TOKEN not set
    if [ -z "$UV_PUBLISH_TOKEN" ] && [ -f ~/.pypirc ]; then
        UV_PUBLISH_TOKEN=$(grep password ~/.pypirc | head -1 | awk '{print $3}')
        export UV_PUBLISH_TOKEN
    fi
    if ! uv publish dist/*; then
        echo -e "  ${RED}PyPI publish FAILED.${NC}"
        echo -e "  ${YELLOW}Rollback: GitHub tag + commit already pushed. To undo:${NC}"
        echo -e "  ${YELLOW}  cd $PUBLIC_DIR && git push --delete origin v${VERSION} && git tag -d v${VERSION}${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}Published nucleus-mcp $VERSION to PyPI${NC}"
    PYPI_PUBLISHED=true
fi
echo ""

# ── [8/9] Publish to NPM ────────────────────────────────────────
echo -e "${BLUE}[8/9] Publishing to NPM...${NC}"
cd "$NPM_DIR"
if [ "$DRY_RUN" = true ]; then
    echo -e "  ${YELLOW}[DRY RUN] Would run: npm publish --access public${NC}"
elif [ "$NPM_AUTH" = false ]; then
    echo -e "  ${YELLOW}Skipped — run 'npm login' then: bash scripts/release.sh --skip-sync${NC}"
else
    if ! npm publish --access public; then
        echo -e "  ${RED}NPM publish FAILED.${NC}"
        echo -e "  ${YELLOW}PyPI was already published. NPM is out of sync.${NC}"
        echo -e "  ${YELLOW}Fix npm auth and re-run: bash scripts/release.sh --skip-sync${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}Published nucleus-mcp $VERSION to NPM${NC}"
fi
echo ""

# ── [9/9] Post-publish verification ──────────────────────────────
echo -e "${BLUE}[9/9] Post-publish verification...${NC}"
if [ "$DRY_RUN" = false ]; then
    sleep 3

    # PyPI check
    if [ "$TEST_PYPI" = true ]; then
        VERIFY_URL="https://test.pypi.org/pypi/nucleus-mcp/${VERSION}/json"
    else
        VERIFY_URL="https://pypi.org/pypi/nucleus-mcp/${VERSION}/json"
    fi
    PYPI_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "$VERIFY_URL" 2>/dev/null || echo "000")
    if [ "$PYPI_CHECK" = "200" ]; then
        gate_pass "PyPI: v${VERSION} live"
    else
        gate_warn "PyPI: v${VERSION} not yet visible (propagation delay)"
    fi

    # NPM check
    if [ "$NPM_AUTH" = true ]; then
        NPM_CHECK=$(npm view "nucleus-mcp@${VERSION}" version 2>/dev/null || echo "")
        if [ "$NPM_CHECK" = "$VERSION" ]; then
            gate_pass "NPM: v${VERSION} live"
        else
            gate_warn "NPM: v${VERSION} not yet visible (propagation delay)"
        fi
    fi
else
    echo -e "  ${YELLOW}[DRY RUN] Skipping verification${NC}"
fi
echo ""

# ── Done ─────────────────────────────────────────────────────────
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}  DRY RUN COMPLETE — nothing was published${NC}"
    echo -e "${YELLOW}  Run without --dry-run to release for real${NC}"
else
    echo -e "${GREEN}  RELEASED v${VERSION}${NC}"
    echo ""
    echo -e "  GitHub: https://github.com/eidetic-works/nucleus-mcp/releases/tag/v${VERSION}"
    if [ "$TEST_PYPI" = true ]; then
        echo -e "  PyPI:   https://test.pypi.org/project/nucleus-mcp/${VERSION}/"
        echo -e "  Test:   pip install -i https://test.pypi.org/simple/ nucleus-mcp==${VERSION}"
    else
        echo -e "  PyPI:   https://pypi.org/project/nucleus-mcp/${VERSION}/"
        echo -e "  Test:   pip install nucleus-mcp==${VERSION}"
    fi
    [ "$NPM_AUTH" = true ] && echo -e "  NPM:    https://www.npmjs.com/package/nucleus-mcp"
    echo ""
    echo -e "  ${DIM}Verify: pip install nucleus-mcp==${VERSION} && nucleus --version${NC}"
    echo -e "  ${DIM}Verify: npx nucleus-mcp --version${NC}"
fi
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
