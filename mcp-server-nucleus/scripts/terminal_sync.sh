#!/bin/bash
# Terminal Sync Script for Gemini CLI Coordination
# Usage: ./terminal_sync.sh <command>
# Example: ./terminal_sync.sh nucleus status

set -euo pipefail

SYNC_LOG="/tmp/nucleus-terminal-sync.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Initialize log file with timestamp header
echo "=== Terminal Sync Session Started: $TIMESTAMP ===" >> "$SYNC_LOG"
echo "" >> "$SYNC_LOG"

# Execute command and tee output to both terminal and log file
echo "[CMD] $*" >> "$SYNC_LOG"
echo "---" >> "$SYNC_LOG"

# Run command with both stdout and stderr captured
"$@" 2>&1 | tee -a "$SYNC_LOG"

EXIT_CODE=${PIPESTATUS[0]}

echo "" >> "$SYNC_LOG"
echo "[EXIT] $EXIT_CODE" >> "$SYNC_LOG"
echo "=== Command Completed: $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$SYNC_LOG"
echo "" >> "$SYNC_LOG"

exit $EXIT_CODE
