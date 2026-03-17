#!/usr/bin/env bash
# ============================================================
# validate_public_surface.sh — Publication Protocol Gate
# ============================================================
# Run BEFORE every sync_public_repo.sh or PyPI publish.
# Exits non-zero if SOVEREIGN content would leak.
#
# Usage:
#   ./scripts/validate_public_surface.sh          # full check
#   ./scripts/validate_public_surface.sh --quick   # file count + identity only
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILURES=0
WARNINGS=0

fail() { echo -e "${RED}FAIL${NC}: $1"; FAILURES=$((FAILURES + 1)); }
warn() { echo -e "${YELLOW}WARN${NC}: $1"; WARNINGS=$((WARNINGS + 1)); }
pass() { echo -e "${GREEN}PASS${NC}: $1"; }

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

echo "================================================"
echo "  PUBLICATION PROTOCOL GATE"
echo "  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "================================================"
echo ""

# ── Step 1: Generate archive ──
echo "Generating git archive from HEAD..."
git archive HEAD --format=tar | tar -xf - -C "$TMPDIR"
FILE_COUNT=$(find "$TMPDIR" -type f | wc -l | tr -d ' ')
echo "Archive: $FILE_COUNT files"
echo ""

# ── Step 2: Identity scan ──
echo "── IDENTITY SCAN ──"
IDENTITY_HITS=$(grep -rln 'lokeshgarg\|lokesh\|gentlequest\.app' "$TMPDIR" 2>/dev/null | wc -l | tr -d ' ')
if [ "$IDENTITY_HITS" -gt 0 ]; then
  fail "Identity leak: $IDENTITY_HITS files contain 'lokeshgarg' or 'gentlequest.app'"
  grep -rln 'lokeshgarg\|lokesh\|gentlequest\.app' "$TMPDIR" 2>/dev/null | sed "s|$TMPDIR/||" | head -10
else
  pass "No identity leaks"
fi

# ── Step 3: Moat language scan ──
echo ""
echo "── MOAT LANGUAGE SCAN ──"
MOAT_HITS=$(grep -rln 'data.moat\|#1 moat\|compounding.advantage\|exponential.loop' "$TMPDIR" 2>/dev/null | wc -l | tr -d ' ')
if [ "$MOAT_HITS" -gt 0 ]; then
  fail "Moat language: $MOAT_HITS files"
  grep -rln 'data.moat\|#1 moat\|compounding.advantage\|exponential.loop' "$TMPDIR" 2>/dev/null | sed "s|$TMPDIR/||"
else
  pass "No moat language"
fi

# ── Step 4: Competitor attack scan ──
echo ""
echo "── COMPETITOR ATTACK SCAN ──"
ATTACK_HITS=$(grep -rln 'OpenClaw.*leak\|OpenClaw.*sleeper\|OpenClaw.*crisis\|OpenClaw.*banned' "$TMPDIR" 2>/dev/null | wc -l | tr -d ' ')
if [ "$ATTACK_HITS" -gt 0 ]; then
  fail "Competitor attack: $ATTACK_HITS files name competitors by security failures"
  grep -rln 'OpenClaw.*leak\|OpenClaw.*sleeper\|OpenClaw.*crisis' "$TMPDIR" 2>/dev/null | sed "s|$TMPDIR/||"
else
  pass "No competitor attacks"
fi

# ── Step 5: Hardcoded paths scan ──
echo ""
echo "── HARDCODED PATHS SCAN ──"
PATH_HITS=$(grep -rn '/Users/[a-z]' "$TMPDIR/src/" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PATH_HITS" -gt 0 ]; then
  fail "Hardcoded user paths in src/: $PATH_HITS hits"
  grep -rn '/Users/[a-z]' "$TMPDIR/src/" 2>/dev/null | head -5
else
  pass "No hardcoded user paths in src/"
fi

# ── Step 6: Hardcoded credentials scan ──
echo ""
echo "── CREDENTIALS SCAN ──"
CRED_HITS=$(grep -rn 'gen-lang-client-\|srv-d2r3i1f\|0ccfed02970a' "$TMPDIR" 2>/dev/null | wc -l | tr -d ' ')
if [ "$CRED_HITS" -gt 0 ]; then
  fail "Hardcoded credentials/service IDs: $CRED_HITS hits"
  grep -rn 'gen-lang-client-\|srv-d2r3i1f\|0ccfed02970a' "$TMPDIR" 2>/dev/null | head -5
else
  pass "No hardcoded credentials"
fi

# ── Step 7: SOVEREIGN files that must NOT be in archive ──
echo ""
echo "── SOVEREIGN FILE GATE ──"
SOVEREIGN_FILES=(
  "src/mcp_server_nucleus/runtime/growth_ops.py"
  "src/mcp_server_nucleus/runtime/outbound_ops.py"
  "src/mcp_server_nucleus/runtime/dogfood_tracker.py"
  "src/mcp_server_nucleus/runtime/capabilities/marketing_engine.py"
  "src/mcp_server_nucleus/runtime/compounding_loop.py"
  "src/mcp_server_nucleus/runtime/autopilot.py"
  "src/mcp_server_nucleus/runtime/god_combos/fusion_reactor.py"
  "src/mcp_server_nucleus/runtime/god_combos/pulse_and_polish.py"
  "src/mcp_server_nucleus/runtime/god_combos/self_healing_v2.py"
  "src/mcp_server_nucleus/runtime/emergence_rate.py"
  "src/mcp_server_nucleus/runtime/siphon_engine.py"
  "src/mcp_server_nucleus/runtime/llm_pattern_learner.py"
  "src/share_to_spotify.py"
  "scripts/validate_public_surface.sh"
  "scripts/sync_public_repo.sh"
  "docs/Sovereign_Compliance_Officer_Handbook.md"
  "docs/strategy/"
  "docs/COMPARISON.md"
  ".wrangler/"
  "engrams/"
  "brain/"
)

for f in "${SOVEREIGN_FILES[@]}"; do
  if [ -e "$TMPDIR/$f" ]; then
    fail "SOVEREIGN file in archive: $f"
  fi
done

SOVEREIGN_LEAKED=$(echo $FAILURES) # capture current count
if [ "$SOVEREIGN_LEAKED" -eq 0 ]; then
  pass "No SOVEREIGN files in archive"
fi

# ── Step 8: /tmp/ hardcoding (Windows compat) ──
echo ""
echo "── CROSS-PLATFORM SCAN ──"
TMP_HITS=$(grep -rn '"/tmp/' "$TMPDIR/src/" 2>/dev/null | wc -l | tr -d ' ')
if [ "$TMP_HITS" -gt 0 ]; then
  warn "Hardcoded /tmp/ in src/: $TMP_HITS hits (breaks Windows)"
  grep -rn '"/tmp/' "$TMPDIR/src/" 2>/dev/null | head -5
else
  pass "No hardcoded /tmp/ paths"
fi

# ── Step 9: FORCE_VERTEX default ──
echo ""
echo "── FRESH INSTALL SCAN ──"
VERTEX_HITS=$(grep -rn 'FORCE_VERTEX.*"1"' "$TMPDIR/src/" 2>/dev/null | grep -v '== "1"' | wc -l | tr -d ' ')
if [ "$VERTEX_HITS" -gt 0 ]; then
  fail "FORCE_VERTEX defaults to 1 (breaks fresh installs)"
  grep -rn 'FORCE_VERTEX.*"1"' "$TMPDIR/src/" 2>/dev/null | grep -v '== "1"'
else
  pass "FORCE_VERTEX defaults to 0 (API key mode)"
fi

# ── Summary ──
echo ""
echo "================================================"
echo "  RESULTS: $FAILURES failures, $WARNINGS warnings"
echo "  Files in archive: $FILE_COUNT"
echo "================================================"

if [ "$FAILURES" -gt 0 ]; then
  echo -e "${RED}BLOCKED${NC}: Fix $FAILURES failures before syncing to public."
  exit 1
else
  echo -e "${GREEN}PASSED${NC}: Safe to sync to public."
  exit 0
fi
