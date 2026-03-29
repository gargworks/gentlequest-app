#!/bin/bash
# Install GROUND pre-commit hook for any fresh clone.
# .git/hooks/ is not tracked by git — run this once after cloning.
#
# Usage: bash scripts/install_ground_hooks.sh

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK_FILE="$REPO_ROOT/.git/hooks/pre-commit"

# If hook already has GROUND, skip
if [ -f "$HOOK_FILE" ] && grep -q "GROUND" "$HOOK_FILE"; then
    echo "GROUND hook already installed in $HOOK_FILE"
    exit 0
fi

# Append GROUND block before the final 'exit 0' if hook exists,
# otherwise create a minimal hook.
if [ -f "$HOOK_FILE" ]; then
    # Remove trailing 'exit 0' so we can append before it
    sed -i.bak '/^exit 0$/d' "$HOOK_FILE"
    rm -f "$HOOK_FILE.bak"
fi

cat >> "$HOOK_FILE" << 'HOOK_EOF'

# ── GROUND: Commit coherence check ──
MANIFEST=".brain/driver/session_manifest.json"
if [ -f "$MANIFEST" ]; then
    OVERLAP=$(python3 -c "
import json, subprocess
m = json.load(open('$MANIFEST'))
pre = set(m.get('pre_staged_files', []))
r = subprocess.run(['git','diff','--cached','--name-only'], capture_output=True, text=True)
staged = set(r.stdout.strip().splitlines())
overlap = pre & staged
print(len(overlap))
for f in sorted(overlap): print(f'  - {f}')
" 2>/dev/null || echo "0")
    COUNT=$(echo "$OVERLAP" | head -1)
    if [ "$COUNT" -gt 0 ] 2>/dev/null; then
        echo -e "\033[0;31mGROUND COHERENCE: ${COUNT} file(s) were staged BEFORE this session.\033[0m"
        echo "$OVERLAP" | tail -n +2
        echo -e "\033[0;31mCommit blocked. Unstage contaminating files or use --no-verify.\033[0m"
        exit 1
    fi
fi

# ── Heuristic: suspiciously large commit ──
STAGED_COUNT=$(git diff --cached --name-only | wc -l | tr -d ' ')
if [ "$STAGED_COUNT" -gt 20 ]; then
    echo -e "\033[0;31mWARNING: ${STAGED_COUNT} files staged — possible contamination.\033[0m"
    echo "If intentional: git commit --no-verify"
    exit 1
fi

# ── GROUND: Tier 0,1 syntax verification ──
# Fast path (~1-2s): syntax only. No imports (Tier 2) or tests (Tier 3).
if command -v nucleus &>/dev/null; then
    echo "Running GROUND verification (Tiers 0,1)..."
    if ! nucleus verify --tiers 0,1 --timeout 10; then
        echo -e "\033[0;31mGROUND: Syntax verification failed. Commit blocked.\033[0m"
        echo "Fix syntax errors above, then retry."
        echo "To skip: git commit --no-verify"
        exit 1
    fi
    echo -e "\033[0;32mGROUND passed.\033[0m"
fi

exit 0
HOOK_EOF

chmod +x "$HOOK_FILE"
echo "GROUND pre-commit hook installed at $HOOK_FILE"
