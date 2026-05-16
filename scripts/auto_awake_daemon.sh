#!/bin/bash
# Nucleus auto-awake daemon launcher (Sub-slice B, Tier 1 headless proxy).
# Invoked by launchd com.nucleus.auto_awake_daemon.plist on a 30s interval,
# or runnable directly for ad-hoc testing.

set -e

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

export PYTHONPATH="${REPO_ROOT}/mcp-server-nucleus/src${PYTHONPATH:+:${PYTHONPATH}}"
export NUCLEUS_BRAIN_PATH="${NUCLEUS_BRAIN_PATH:-${REPO_ROOT}/.brain}"

exec python3 -m mcp_server_nucleus.runtime.auto_awake --once
