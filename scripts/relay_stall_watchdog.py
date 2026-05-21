#!/usr/bin/env python3
"""Shim: delegates to mcp_server_nucleus.watchdog.stall.

Preserves:
  - Hammerspoon's 15-min invocation path (python3 scripts/relay_stall_watchdog.py).
  - Existing unit tests that ``import relay_stall_watchdog as watchdog`` and call
    module-level helpers (``watchdog.age_min``, ``watchdog.find_ack_then_stalls``,
    ``watchdog.find_refuse_without_reason``). The ``from ... import *`` below
    re-exports every public name at this module's scope.

In-tree src wins over any globally installed mcp_server_nucleus so that dev
work in this worktree takes precedence over a stale pip install.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "mcp-server-nucleus" / "src"
if _SRC.is_dir():
    sys.path.insert(0, str(_SRC))

from mcp_server_nucleus.watchdog.stall import main  # noqa: F401,E402
from mcp_server_nucleus.watchdog.stall import *  # noqa: F401,F403,E402

if __name__ == "__main__":
    sys.exit(main())
