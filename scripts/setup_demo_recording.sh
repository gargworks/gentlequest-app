#!/bin/bash
# Pre-Recording Setup Script
# Run this before recording any Nucleus demos

echo "🎬 Nucleus Demo Recording Setup"
echo "================================"
echo ""

# 1. Ensure private symlink exists
ln -sfn /Users/lokeshgarg/ai-mvp-backend/output/demos /tmp/nucleus-demo
echo "✅ Private demo path ready: /tmp/nucleus-demo"

# 2. Set clean terminal prompt
export PS1="nucleus $ "
echo "✅ Terminal prompt set to: nucleus $ "

# 3. Setup local aliases for Nucleus commands
export PYTHONPATH="/Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src:$PYTHONPATH"
alias nucleus-init="python3 -m mcp_server_nucleus.cli"
alias brain_audit_log="python3 -m mcp_server_nucleus.cli audit"
echo "✅ Local Nucleus commands aliased"

# 2. Clear screen
clear

echo "🎬 Nucleus Demo Recording Setup"
echo "================================"
echo ""
echo "✅ Terminal prompt: nucleus $"
echo "✅ Screen cleared"
echo ""
echo "📋 Pre-Recording Checklist:"
echo "  [ ] QuickTime screen recording ready?"
echo "  [ ] Demo steps prepared?"
echo "  [ ] Audio voiceover generated?"
echo ""
echo "Ready to record! Press Enter to continue..."
read

# Clear one more time for clean start
clear
