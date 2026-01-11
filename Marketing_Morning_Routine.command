#!/bin/bash
# Marketing Morning Routine
# Double-click this to start the Growth Machine.

cd "$(dirname "$0")"

echo "🛸 Starting GentleQuest Marketing Autopilot..."

# 1. Check if the Ingest Server (Port 9999) is running
if ! lsof -i :9999 > /dev/null; then
    echo "🚀 Starting Ingest Server..."
    
    # Set PYTHONPATH to include project root and nucleus src
    export PYTHONPATH="$PYTHONPATH:$(pwd):$(pwd)/mcp-server-nucleus/src"
    
    nohup python3 tools/marketing-dashboard/server.py > tools/marketing-dashboard/server.log 2>&1 &
    sleep 2
else
    echo "✅ Ingest Server already live."
fi

# 2. Open the Dashboard
echo "🧭 Opening Dashboard..."
open "http://localhost:9999"

echo "------------------------------------------------"
echo "Mission Control is LIVE."
echo "Follow the 'Morning Routine' panel on the dashboard."
echo "------------------------------------------------"
sleep 3
exit
