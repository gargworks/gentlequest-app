#!/usr/bin/env python3
"""flywheel_curriculum — close the compound loop.

Walks pending DPO pairs in .brain/training/exports/unified_dpo_pending.jsonl
and promotes any whose step has since survived verification. Promoted pairs
are appended to unified_dpo_ready.jsonl and removed from the pending file.

Usage:
    python scripts/flywheel_curriculum.py
    python scripts/flywheel_curriculum.py --brain-path /tmp/fw-test
"""

import argparse
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
sys.path.insert(0, str(_REPO / "mcp-server-nucleus" / "src"))

from mcp_server_nucleus.flywheel import curriculum_refresh  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--brain-path",
        default=os.environ.get("NUCLEUS_BRAIN_PATH"),
        help="override .brain path",
    )
    args = parser.parse_args()

    brain_path = Path(args.brain_path) if args.brain_path else Path.cwd() / ".brain"
    result = curriculum_refresh(brain_path)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
