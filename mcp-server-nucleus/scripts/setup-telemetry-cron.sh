#!/bin/bash
# Setup automated telemetry drain (every 5 minutes)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 NUCLEUS TELEMETRY CRON SETUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if crontab exists
if ! crontab -l >/dev/null 2>&1; then
    echo "No existing crontab. Creating new one..."
    echo "# Nucleus Telemetry Drain (every 5 minutes)" | crontab -
fi

# Check if drain job already exists
if crontab -l 2>/dev/null | grep -q "telemetry:drain"; then
    echo "⚠️  Telemetry drain job already exists in crontab."
    echo ""
    echo "Current crontab:"
    crontab -l | grep -A1 -B1 "telemetry:drain"
    echo ""
    read -p "Replace existing job? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping cron setup."
        exit 0
    fi
    # Remove old job
    crontab -l | grep -v "telemetry:drain" | crontab -
fi

# Add new cron job (every 5 minutes)
(crontab -l 2>/dev/null; echo "# Nucleus Telemetry Drain (every 5 minutes)"; echo "*/5 * * * * cd $PROJECT_ROOT && npm run telemetry:drain >> .telemetry/drain.log 2>&1") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "Schedule: Every 5 minutes"
echo "Command: cd $PROJECT_ROOT && npm run telemetry:drain"
echo "Log: $PROJECT_ROOT/.telemetry/drain.log"
echo ""
echo "To verify:"
echo "  crontab -l"
echo ""
echo "To remove:"
echo "  crontab -e  # then delete the telemetry:drain line"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
