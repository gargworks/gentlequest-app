#!/bin/bash
# Nucleus Orchestrator Runner
# Triggered by cron: 0 8 * * * /path/to/scripts/run_orchestrator.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Set brain path
export NUCLEUS_BRAIN_PATH="$PROJECT_ROOT/.brain"

# Run orchestrator
cd "$PROJECT_ROOT"
python3 scripts/orchestrator.py

echo "Orchestrator completed at $(date)"
