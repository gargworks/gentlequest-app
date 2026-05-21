#!/bin/bash
# whats_next.py personal-test runner — append a single JSON observation row
# to .brain/research/2026-04-28_tier_architecture/personal_test_log.jsonl.
#
# Per main's relay_20260501_041352_caa8f645: personal-test over 3-5 sessions
# is the validation gate before surfacing whats_next.py v0.1 to Lokesh as
# ready-for-beta.
#
# CRON SUGGESTION (Lokesh-keyboard, NOT auto-installed by this script):
#
#     crontab -e
#     # Run every 90 minutes during awake hours, log to ~/.cache/wn-test.log
#     */90 9-23 * * * /Users/lokeshgarg/ai-mvp-backend/scripts/whats_next_personal_test_run.sh \
#         >> ~/.cache/wn-test.log 2>&1
#
# Or via launchd if cron isn't preferred. Safe to run by hand any time.
#
# Usage:
#     scripts/whats_next_personal_test_run.sh         # uses defaults
#     scripts/whats_next_personal_test_run.sh peer    # explicit viewer
#     scripts/whats_next_personal_test_run.sh founder

set -eu

REPO_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LOG="${REPO_ROOT}/.brain/research/2026-04-28_tier_architecture/personal_test_log.jsonl"
VIEWER="${1:-peer}"

mkdir -p "$(dirname "${LOG}")"

# Run whats_next.py as JSON; capture top-3 actions for compact log row.
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
output=$(cd "${REPO_ROOT}" && python3 scripts/whats_next.py --as "${VIEWER}" --top 5 --format json 2>&1) || {
    echo "{\"ts\":\"${ts}\",\"viewer\":\"${VIEWER}\",\"error\":\"whats_next.py failed\"}" >> "${LOG}"
    exit 1
}

# Compact the row: just timestamp + viewer + top-3 (rank, score, source, summary)
python3 <<EOF >> "${LOG}"
import json
data = json.loads('''${output}''')
row = {
    "ts": "${ts}",
    "viewer": "${VIEWER}",
    "n_total": data.get("n_total", 0),
    "top": [
        {"rank": a["rank"], "score": a["score"], "source": a["source"],
         "summary": a["summary"][:80]}
        for a in data.get("actions", [])[:3]
    ],
}
print(json.dumps(row, separators=(",", ":")))
EOF

# Optional: print last row for human eyeball when running interactively
if [ -t 1 ]; then
    tail -1 "${LOG}"
fi
