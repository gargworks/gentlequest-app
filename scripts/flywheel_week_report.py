#!/usr/bin/env python3
"""flywheel_week_report — regenerate the current week's markdown report.

Usage:
    python scripts/flywheel_week_report.py
    python scripts/flywheel_week_report.py --week 15
    python scripts/flywheel_week_report.py --brain-path /tmp/fw-test
"""

import argparse
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
sys.path.insert(0, str(_REPO / "mcp-server-nucleus" / "src"))

from mcp_server_nucleus.flywheel import generate_week_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", type=int, help="ISO week number (default: current)")
    parser.add_argument(
        "--brain-path",
        default=os.environ.get("NUCLEUS_BRAIN_PATH"),
        help="override .brain path",
    )
    args = parser.parse_args()

    brain_path = Path(args.brain_path) if args.brain_path else Path.cwd() / ".brain"
    out_path = generate_week_report(brain_path, week=args.week)
    print(f"wrote: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
