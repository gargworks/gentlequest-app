#!/bin/bash
# Daily Automated Tasks for GentleQuest
# Add to crontab: 0 2 * * * /path/to/daily_tasks.sh

cd /Users/lokeshgarg/ai-mvp-backend

# Health check
python scripts/daily_health_check.py >> logs/health_$(date +%Y%m%d).log

# Cleanup old data
python scripts/cleanup_old_data.py >> logs/cleanup_$(date +%Y%m%d).log

# Backup database
./scripts/backup_database.sh >> logs/backup_$(date +%Y%m%d).log

# Performance analysis (weekly, on Mondays)
if [ $(date +%u) -eq 1 ]; then
    python scripts/performance_analysis.py >> logs/perf_$(date +%Y%m%d).log
fi

# Security audit (monthly, on 1st)
if [ $(date +%d) -eq 01 ]; then
    python scripts/security_audit.py >> logs/security_$(date +%Y%m%d).log
fi

echo "✅ Daily tasks complete: $(date)"
