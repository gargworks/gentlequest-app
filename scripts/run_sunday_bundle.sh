#!/bin/bash
# run_sunday_bundle.sh
# Bundles the Weekly Strategy Sync and the Weekly Summary into one sequential job.

# Set project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo "=============================================="
echo "🌞 STARTING SUNDAY BUNDLE: $(date)"
echo "=============================================="

# 1. Run Strategy Sync (The Brain) using Python 3
# This updates strategy.md and task.md
echo "Running Auto Strategy Sync..."
/usr/bin/python3 scripts/auto_strategy_sync.py

# 2. Run Weekly Summary (The Reporter)
# This reads the UPDATED strategy.md and sends the Telegram
echo "Running Weekly Summary..."
/usr/bin/python3 scripts/weekly_summary.py

echo "=============================================="
echo "✅ SUNDAY BUNDLE COMPLETE: $(date)"
echo "=============================================="
