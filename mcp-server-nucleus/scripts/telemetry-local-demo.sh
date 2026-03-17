#!/usr/bin/env bash
set -euo pipefail

# Run Nucleus against the local Phase B telemetry stack.
# Usage:
#   scripts/telemetry-local-demo.sh morning-brief
#   scripts/telemetry-local-demo.sh <any-nucleus-command>

cd "$(dirname "$0")/.."

NUCLEUS_ANON_TELEMETRY=true \
NUCLEUS_ANON_TELEMETRY_ENDPOINT=http://localhost:4318 \
nucleus "$@"
