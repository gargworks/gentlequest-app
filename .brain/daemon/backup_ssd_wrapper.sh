#!/bin/bash
# Wrapper for launchd — runs SSD backup only if the drive is mounted.
# Called by dev.nucleusos.backup-ssd launchd agent.
#
# NOTE: launchd's /bin/bash needs Full Disk Access in
#   System Settings > Privacy & Security > Full Disk Access
# to write to external volumes. Without it, rsync fails with
# "Operation not permitted". The script detects this and logs
# remediation instructions instead of silently failing.

SSD_PATH="/Volumes/Samsung SSD 990 PRO 2TB Media"
BACKUP_ROOT="$SSD_PATH/nucleus-backup"
LOG="/Users/lokeshgarg/ai-mvp-backend/.brain/logs/backup_ssd.log"

echo "--- $(date) ---" >> "$LOG"

if [ ! -d "$SSD_PATH" ]; then
    echo "SSD not mounted — skipping" >> "$LOG"
    exit 0
fi

# Preflight: test write access before running the full backup
TEST_FILE="$BACKUP_ROOT/.write_test_$$"
mkdir -p "$BACKUP_ROOT" 2>/dev/null
if ! touch "$TEST_FILE" 2>/dev/null; then
    echo "BACKUP SKIPPED — cannot write to $BACKUP_ROOT" >> "$LOG"
    echo "FIX: System Settings > Privacy & Security > Full Disk Access > add /bin/bash" >> "$LOG"
    exit 1
fi
rm -f "$TEST_FILE"

/Users/lokeshgarg/ai-mvp-backend/.brain/backup_ssd.sh >> "$LOG" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "BACKUP FAILED (exit $EXIT_CODE)" >> "$LOG"
else
    echo "Backup complete" >> "$LOG"
fi

exit $EXIT_CODE
