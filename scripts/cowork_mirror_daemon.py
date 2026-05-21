#!/usr/bin/env python3
"""Shim: delegates to mcp_server_nucleus.mirror.daemon.

The real implementation lives in the shipped package. This shim keeps the
existing launchd plist (/usr/bin/python3 scripts/cowork_mirror_daemon.py)
working without a package install. In-tree src wins over any globally
installed mcp_server_nucleus so dev work in this worktree takes precedence
over a stale pip install.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "mcp-server-nucleus" / "src"
if _SRC.is_dir():
    sys.path.insert(0, str(_SRC))

from mcp_server_nucleus.mirror.daemon import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
