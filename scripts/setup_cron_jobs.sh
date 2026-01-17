#!/bin/bash
# Setup cron jobs for automated tasks

echo "⏰ SETTING UP CRON JOBS"
echo "======================="

# Create crontab entries
CRON_FILE="/tmp/gentlequest_cron"

cat > $CRON_FILE << 'EOF'
# GentleQuest Automated Tasks

# Daily tasks (2am every day)
0 2 * * * /Users/lokeshgarg/ai-mvp-backend/cron/daily_tasks.sh

# Weekly tasks (Monday 3am)
0 3 * * 1 /Users/lokeshgarg/ai-mvp-backend/scripts/automated_weekly_tasks.sh

# Monthly tasks (1st of month, 4am)
0 4 1 * * /Users/lokeshgarg/ai-mvp-backend/scripts/automated_monthly_tasks.sh

# Health check (every 6 hours)
0 */6 * * * /Users/lokeshgarg/ai-mvp-backend/scripts/daily_health_check.py >> /Users/lokeshgarg/ai-mvp-backend/logs/health.log 2>&1

EOF

# Install crontab
crontab $CRON_FILE

echo "✅ Cron jobs installed"
echo ""
echo "Scheduled tasks:"
echo "  - Daily (2am): Health check, cleanup, backup"
echo "  - Weekly (Mon 3am): Performance, engagement, reports"
echo "  - Monthly (1st 4am): Security audit, outcomes, exports"
echo "  - Every 6 hours: Health check"
echo ""
echo "View cron jobs: crontab -l"
echo "Remove cron jobs: crontab -r"
