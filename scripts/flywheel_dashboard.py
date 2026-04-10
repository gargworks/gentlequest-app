#!/usr/bin/env python3
"""flywheel_dashboard — print flywheel state as JSON.

Usage:
    python scripts/flywheel_dashboard.py
    python scripts/flywheel_dashboard.py --html > dashboard.html
    python scripts/flywheel_dashboard.py --brain-path /tmp/fw-test
"""

import argparse
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
sys.path.insert(0, str(_REPO / "mcp-server-nucleus" / "src"))

from mcp_server_nucleus.flywheel import render_dashboard_html, render_dashboard_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", action="store_true", help="emit HTML instead of JSON")
    parser.add_argument(
        "--brain-path",
        default=os.environ.get("NUCLEUS_BRAIN_PATH"),
        help="override .brain path",
    )
    args = parser.parse_args()

    brain_path = Path(args.brain_path) if args.brain_path else Path.cwd() / ".brain"
    if args.html:
        print(render_dashboard_html(brain_path))
    else:
        print(json.dumps(render_dashboard_json(brain_path), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
