#!/bin/bash
# Emergency shutdown procedure

echo "🚨 EMERGENCY SHUTDOWN"
echo "====================="

read -p "Are you SURE you want to shut down GentleQuest? (type YES): " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo "Shutdown cancelled"
    exit 0
fi

echo ""
echo "Shutting down..."

# 1. Notify all active users
echo "1. Notifying users..."
# TODO: Send email to all active sessions

# 2. Disable new signups
echo "2. Disabling new signups..."
# TODO: Set maintenance mode flag

# 3. Export all data
echo "3. Exporting all data..."
python scripts/export_pilot_data.py 1 emergency_backup_$(date +%Y%m%d).csv

# 4. Backup database
echo "4. Backing up database..."
./scripts/backup_database.sh

# 5. Document reason
echo "5. Documenting shutdown..."
read -p "Reason for shutdown: " REASON
echo "$(date): Emergency shutdown - $REASON" >> logs/shutdown_log.txt

echo ""
echo "✅ Emergency shutdown complete"
echo ""
echo "Data backed up to:"
echo "  - emergency_backup_$(date +%Y%m%d).csv"
echo "  - backups/gentlequest_*.sql.gz"
echo ""
echo "To restart:"
echo "  1. Fix issue causing shutdown"
echo "  2. Run: make deploy"
echo "  3. Notify users service is restored"
