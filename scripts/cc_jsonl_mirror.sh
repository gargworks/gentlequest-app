#!/usr/bin/env bash
# Shim: delegates to mcp-server-nucleus/bin/cc-jsonl-mirror.
#
# Preserves the historical path referenced by launchd / existing cron jobs
# (e.g. com.nucleus.cc_jsonl_mirror.plist) while the portable primitive
# lives in the package's bin/ directory.

set -euo pipefail
_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
_TARGET="${_DIR}/../mcp-server-nucleus/bin/cc-jsonl-mirror"
exec "$_TARGET" "$@"
