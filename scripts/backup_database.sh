#!/bin/bash
# Database Backup Script
# Run daily via cron: 0 2 * * * /path/to/backup_database.sh

BACKUP_DIR="/Users/lokeshgarg/ai-mvp-backend/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/gentlequest_$DATE.sql"

mkdir -p $BACKUP_DIR

# Backup database
pg_dump mental_health > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "✅ Backup complete: $BACKUP_FILE.gz"
