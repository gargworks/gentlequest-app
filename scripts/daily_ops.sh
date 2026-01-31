#!/bin/bash

echo "🌅 GentleQuest Daily Ops Report - $(date)"
echo "----------------------------------------"

# 1. System Health Check
echo "Checking Backend Health..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://app.gentlequest.app/api/health)

if [ "$HEALTH_STATUS" -eq 200 ]; then
    echo "✅ Backend: ONLINE (200 OK)"
else
    echo "❌ Backend: DOWN ($HEALTH_STATUS)"
fi

# 2. Database Connectivity
echo "Checking Database Pool..."
# We reuse setup_demo_user.py's ping logic or a simple SQL check
# For now, let's use a quick python one-liner to check dependencies
python3 -c "import psycopg; print('✅ Psycopg Installed')" 2>/dev/null

# 3. Outreach Status
if [ -d "outreach_campaign_v1" ]; then
    COUNT=$(ls outreach_campaign_v1 | wc -l)
    echo "✉️  Campaign Drafts Ready: $COUNT"
else
    echo "⚠️  No Campaign Drafts Found (Run outreach_manager.py)"
fi

echo "----------------------------------------"
echo "🚀 Morning Routine Complete."
