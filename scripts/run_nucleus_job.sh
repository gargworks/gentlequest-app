#!/bin/bash
# Nucleus Job Runner - Sets up environment and runs specified script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set environment
export NUCLEAR_BRAIN_PATH="$PROJECT_ROOT/.brain"
export PATH="/usr/local/bin:/usr/bin:$PATH"

# Load .env if exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Change to project directory
cd "$PROJECT_ROOT"

# Run the specified script
SCRIPT_NAME="${1:-health_check}"

case "$SCRIPT_NAME" in
    "health_check")
        python3 scripts/nucleus_health_check.py --emit-event >> /tmp/nucleus_health.log 2>&1
        ;;
    "orchestrator")
        python3 scripts/orchestrator.py >> /tmp/nucleus_orchestrator.log 2>&1
        ;;
    "meta_optimizer")
        python3 scripts/meta_optimizer.py >> /tmp/nucleus_meta_optimizer.log 2>&1
        ;;
    "nightly")
        python3 scripts/nightly_agent.py >> /tmp/nucleus_nightly.log 2>&1
        ;;
    *)
        echo "Unknown script: $SCRIPT_NAME"
        exit 1
        ;;
esac
