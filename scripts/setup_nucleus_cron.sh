#!/bin/bash
#
# Nucleus Automation Scheduler
# ============================
# Sets up cron jobs for full Nucleus automation
#
# Run this script once to install all scheduled tasks:
#   bash scripts/setup_nucleus_cron.sh
#
# Location: scripts/setup_nucleus_cron.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Nucleus Automation Scheduler"
echo "======================================"
echo ""

# Create the wrapper script that sets environment
cat > "$SCRIPT_DIR/run_nucleus_job.sh" << 'WRAPPER'
#!/bin/bash
# Nucleus Job Runner - Sets up environment and runs specified script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set environment
export NUCLEUS_BRAIN_PATH="$PROJECT_ROOT/.brain"
export PATH="/usr/local/bin:/usr/bin:$PATH"

# Load .env if exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
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
WRAPPER

chmod +x "$SCRIPT_DIR/run_nucleus_job.sh"
echo "✅ Created job runner: scripts/run_nucleus_job.sh"

# Generate cron entries
CRON_ENTRIES="
# ==========================================
# NUCLEUS AUTOMATION - Installed $(date +%Y-%m-%d)
# ==========================================

# Health Check - Every 6 hours
0 */6 * * * $SCRIPT_DIR/run_nucleus_job.sh health_check

# Orchestrator (Daily Digest) - Every morning at 9 AM
0 9 * * * $SCRIPT_DIR/run_nucleus_job.sh orchestrator

# Meta-Optimizer - Every 72 hours (every 3rd day at midnight)
0 0 */3 * * $SCRIPT_DIR/run_nucleus_job.sh meta_optimizer

# Nightly Agent - Every night at 11 PM
0 23 * * * $SCRIPT_DIR/run_nucleus_job.sh nightly

# ==========================================
# END NUCLEUS AUTOMATION
# ==========================================
"

echo ""
echo "📅 Cron Schedule (copy to 'crontab -e'):"
echo "--------------------------------------------"
echo "$CRON_ENTRIES"
echo "--------------------------------------------"

# Save cron entries to file for reference
echo "$CRON_ENTRIES" > "$PROJECT_ROOT/.brain/meta/nucleus_cron.txt"
echo ""
echo "✅ Saved cron config to .brain/meta/nucleus_cron.txt"

# Ask if user wants to install
echo ""
echo "To install, run: crontab -e"
echo "Then paste the cron entries above."
echo ""
echo "Or to install automatically, run:"
echo "  (crontab -l 2>/dev/null | grep -v 'NUCLEUS AUTOMATION'; cat .brain/meta/nucleus_cron.txt) | crontab -"
