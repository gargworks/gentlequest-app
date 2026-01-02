"""
Nucleus MCP Server - The Brain for AI Agents
=============================================
One Brain, Many Interfaces.
"""

__version__ = "0.1.0"
__author__ = "GentleQuest"

from .state import get_state, set_state
from .events import emit_event, get_events

__all__ = ["get_state", "set_state", "emit_event", "get_events"]
