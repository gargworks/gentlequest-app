#!/bin/sh
# Wrapper to run Nucleus MCP server with stderr suppressed
export NUCLEAR_BRAIN_PATH="${NUCLEAR_BRAIN_PATH:-/Users/lokeshgarg/dogfood-brain/.brain}"
export FASTMCP_SHOW_CLI_BANNER="False"
export FASTMCP_LOG_LEVEL="WARNING"

# Execute python module, redirecting stderr to /dev/null to keep MCP protocol clean
exec /opt/homebrew/bin/python3.11 -m mcp_server_nucleus 2>/dev/null
