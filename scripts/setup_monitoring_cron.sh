#!/bin/bash
# Setup Monitoring Cron Jobs
# Part of Phase 68: Agent Runtime V2 Enhancement
#
# This script adds monitoring cron jobs to the crontab

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment
if [[ -f "$PROJECT_DIR/.env" ]]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

echo "📋 Setting up monitoring cron jobs..."

# Create a temporary file with new cron entries
CRON_ENTRIES=$(cat <<EOF
# Nucleus Monitoring Jobs (Phase 68)
# DB Health Check - every 6 hours
0 */6 * * * cd $PROJECT_DIR && /usr/bin/python3 scripts/monitor_db_health.py >> /tmp/nucleus_db_health.log 2>&1
# SSL Certificate Check - daily at 9 AM
0 9 * * * cd $PROJECT_DIR && /usr/bin/python3 scripts/monitor_ssl_cert.py >> /tmp/nucleus_ssl_check.log 2>&1
EOF
)

# Check if entries already exist
if crontab -l 2>/dev/null | grep -q "Nucleus Monitoring Jobs"; then
    echo "⚠️  Monitoring cron jobs already exist. Skipping..."
    crontab -l | grep -A3 "Nucleus Monitoring Jobs"
else
    # Add new entries
    (crontab -l 2>/dev/null || echo "") | { cat; echo "$CRON_ENTRIES"; } | crontab -
    echo "✅ Cron jobs added successfully!"
    echo ""
    echo "Current monitoring jobs:"
    crontab -l | grep -A3 "Nucleus Monitoring Jobs" || echo "Jobs added"
fi

echo ""
echo "📊 To verify cron jobs:"
echo "  crontab -l | grep nucleus"
echo ""
echo "📝 Log locations:"
echo "  DB Health: /tmp/nucleus_db_health.log"
echo "  SSL Check: /tmp/nucleus_ssl_check.log"
