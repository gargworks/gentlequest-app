#!/usr/bin/env bash
# Shim: delegates to mcp-server-nucleus/bin/backup-brain.
#
# Legacy entry point; the portable primitive lives in the package bin/.
# Required env (set by operator / cron):
#   NUCLEUS_BACKUP_SOURCE, NUCLEUS_BACKUP_ARCHIVE, optional NUCLEUS_BACKUP_CLOUD,
#   optional NUCLEUS_BACKUP_GIT_PUSH=1.

set -euo pipefail
_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
_TARGET="${_DIR}/../mcp-server-nucleus/bin/backup-brain"
exec "$_TARGET" "$@"
