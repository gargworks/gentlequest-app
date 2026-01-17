#!/bin/sh
# Setup Scheduled Autopilot for GentleQuest
# Generates and loads launchd agents dynamically.

PROJECT_DIR=$(pwd)
PYTHON_EXEC=$(which python3)
USER_ID=$(id -u)

echo "🚀 Setting up GentleQuest Autopilot..."
echo "📍 Project: $PROJECT_DIR"
echo "🐍 Python: $PYTHON_EXEC"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# 1. Generate Dashboard Plist
CAT_PLIST_DASHBOARD="$HOME/Library/LaunchAgents/com.gentlequest.marketing.dashboard.plist"
echo "📄 Generating Dashboard Agent -> $CAT_PLIST_DASHBOARD"

cat <<EOF > "$CAT_PLIST_DASHBOARD"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gentlequest.marketing.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_EXEC</string>
        <string>$PROJECT_DIR/tools/marketing-dashboard/server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/dashboard.error.log</string>
</dict>
</plist>
EOF

# 2. Generate Comet Scheduler Plist
CAT_PLIST_COMET="$HOME/Library/LaunchAgents/com.gentlequest.marketing.comet.plist"
echo "📄 Generating Comet Agent -> $CAT_PLIST_COMET"

cat <<EOF > "$CAT_PLIST_COMET"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gentlequest.marketing.comet</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_EXEC</string>
        <string>$PROJECT_DIR/scripts/comet_runner.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/comet_scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/comet_scheduler.error.log</string>
</dict>
</plist>
EOF

# 3. Load Agents
echo "🔄 Reloading Agents..."
launchctl unload "$CAT_PLIST_DASHBOARD" 2>/dev/null
launchctl unload "$CAT_PLIST_COMET" 2>/dev/null

launchctl load "$CAT_PLIST_DASHBOARD"
launchctl load "$CAT_PLIST_COMET"

echo "✅ Autopilot Installed."
echo "   - Dashboard: http://localhost:9999"
echo "   - Scheduler: 9:00 AM Daily"
echo "   - Logs: $PROJECT_DIR/logs/"
