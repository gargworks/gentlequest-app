"""
Tests for tool registration implementation
"""

import pytest
from unittest.mock import MagicMock
from mcp_server_nucleus.core import tool_registration_impl
from mcp_server_nucleus.tool_tiers import tier_manager


def test_tier_based_registration():
    """Test tools are registered or filtered based on active tier"""
    # Setup mock MCP
    mock_mcp = MagicMock()
    
    # Configure with tier 1 (core tools)
    tier_manager.active_tier = 1
    configured_mcp = tool_registration_impl.configure_tiered_tool_registration(mock_mcp)
    
    # Create sample tools
    @configured_mcp.tool()
    def core_tool():
        return "core"

    @configured_mcp.tool()
    def advanced_tool():
        return "advanced"
    
    # Verify only core tool was registered
    assert "core_tool" in tier_manager.registered_tools
    assert "advanced_tool" in tier_manager.filtered_tools
    mock_mcp.tool.assert_called_once()
    
    # Reset and test tier 2 (all tools)
    tier_manager.reset()
    tier_manager.active_tier = 2
    configured_mcp = tool_registration_impl.configure_tiered_tool_registration(mock_mcp)
    
    @configured_mcp.tool()
    def core_tool():
        return "core"

    @configured_mcp.tool()
    def advanced_tool():
        return "advanced"
    
    # Verify both tools registered
    assert "core_tool" in tier_manager.registered_tools
    assert "advanced_tool" in tier_manager.registered_tools
    assert mock_mcp.tool.call_count == 3  # 1 previous + 2 new
