#!/bin/bash
# GentleQuest Deployment Wrapper
# Triggers the NAR DevOps Agent to handle deployment.

# Ensure we are in the project root
cd "$(dirname "$0")"

echo "🤖 Nucleus DevOps Agent"
echo "======================="

# Check for API Key
if [ -z "$RENDER_API_KEY" ]; then
    echo "⚠️  RENDER_API_KEY is not set. Deployment will fail."
    echo "   Please export RENDER_API_KEY=..."
    echo ""
fi

echo "🚀 Spawning DevOps Agent..."
python3 scripts/deploy_agent.py

echo ""
echo "✅ Operational task handed off to Agent Runtime."
