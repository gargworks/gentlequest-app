#!/bin/sh
# Wrapper to run Nucleus MCP server with stderr suppressed
export NUCLEAR_BRAIN_PATH="${NUCLEAR_BRAIN_PATH:-/Users/lokeshgarg/dogfood-brain/.brain}"
export FASTMCP_SHOW_CLI_BANNER="False"
export FASTMCP_LOG_LEVEL="WARNING"
export NUCLEUS_TOOL_TIER="${NUCLEUS_TOOL_TIER:-0}"
export NUCLEUS_V9_SECURITY="${NUCLEUS_V9_SECURITY:-true}"

# Execute python module, redirecting stderr to /dev/null to keep MCP protocol clean
exec python3 -m mcp_server_nucleus 2>/dev/null
