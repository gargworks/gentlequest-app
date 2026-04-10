#!/usr/bin/env python3
"""flywheel_ticket — file a failure ticket via the 6-action accountability helper.

Usage:
    python scripts/flywheel_ticket.py --step phase_a_classify --error "timeout in mood provider"
    python scripts/flywheel_ticket.py --step driver_phase_c --error "no PR created" --logs "$(tail -c 2000 run.log)"

Writes to .brain/flywheel/{pending_issues,pending_tasks,gh_issue_queue}.jsonl plus
.brain/training/exports/unified_dpo_pending.jsonl plus .brain/flywheel/week-N.md.
Attempts to create a GitHub issue via `gh`; queues if gh is unavailable.

Honors NUCLEUS_BRAIN_PATH env var. Exit 0 always (best-effort).
"""

import argparse
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
sys.path.insert(0, str(_REPO / "mcp-server-nucleus" / "src"))

from mcp_server_nucleus.flywheel import file_ticket  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", required=True, help="failing step identifier")
    parser.add_argument("--error", required=True, help="short error description")
    parser.add_argument("--logs", default="", help="optional log snippet (max 2KB)")
    parser.add_argument("--phase", default="", help="optional phase label")
    parser.add_argument(
        "--brain-path",
        default=os.environ.get("NUCLEUS_BRAIN_PATH"),
        help="override .brain path",
    )
    args = parser.parse_args()

    brain_path = Path(args.brain_path) if args.brain_path else None
    report = file_ticket(
        step=args.step,
        error=args.error,
        logs=args.logs,
        phase=args.phase,
        brain_path=brain_path,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
