#!/bin/bash
# Nightly Agent + Weekly Summary Cron Setup
# Installs both daily (8 AM) and weekly (Sunday 9 AM) jobs

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/.brain/ledger"

echo "📅 Setting up Agent cron jobs..."
echo "   Project: $PROJECT_DIR"
echo ""

# Check for API key
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY not found in environment."
    echo "   Make sure to set it before the cron runs."
    echo ""
fi

# Define cron entries
NIGHTLY_CRON="0 8 * * * cd $PROJECT_DIR && GEMINI_API_KEY=\$GEMINI_API_KEY TELEGRAM_BOT_TOKEN=\$TELEGRAM_BOT_TOKEN /usr/bin/python3 $SCRIPT_DIR/nightly_agent.py >> $LOG_DIR/cron.log 2>&1"
WEEKLY_CRON="0 9 * * 0 cd $PROJECT_DIR && GEMINI_API_KEY=\$GEMINI_API_KEY TELEGRAM_BOT_TOKEN=\$TELEGRAM_BOT_TOKEN /usr/bin/python3 $SCRIPT_DIR/weekly_summary.py >> $LOG_DIR/cron.log 2>&1"

echo "📋 Proposed cron entries:"
echo ""
echo "1. NIGHTLY (8 AM every day):"
echo "   $NIGHTLY_CRON"
echo ""
echo "2. WEEKLY (9 AM every Sunday):"
echo "   $WEEKLY_CRON"
echo ""

read -p "Install both cron jobs? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Remove old entries and add new ones
    (crontab -l 2>/dev/null | grep -v "nightly_agent.py" | grep -v "weekly_summary.py"; echo "$NIGHTLY_CRON"; echo "$WEEKLY_CRON") | crontab -
    
    echo ""
    echo "✅ Cron jobs installed!"
    echo ""
    echo "   📆 Nightly: 8 AM every day"
    echo "   📊 Weekly: 9 AM every Sunday"
    echo ""
    echo "   View with: crontab -l"
    echo "   Logs at: $LOG_DIR/cron.log"
else
    echo ""
    echo "❌ Cron jobs not installed."
    echo "   To install manually, run: crontab -e"
fi

echo ""
echo "🧪 Test commands:"
echo "   python3 $SCRIPT_DIR/nightly_agent.py    # Daily"
echo "   python3 $SCRIPT_DIR/weekly_summary.py   # Weekly"
