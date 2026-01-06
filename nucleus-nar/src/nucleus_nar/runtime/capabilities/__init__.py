"""
Capability Base Class
=====================
The abstract interface for all NAR capabilities.
Capabilities define tools that can be used by ephemeral agents.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class Capability(ABC):
    """
    Abstract base for all capabilities in the NAR ecosystem.
    
    A Capability:
    1. Defines a set of tools (get_tools)
    2. Executes tool calls (execute_tool)
    3. Has a unique name for registration
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this capability"""
        pass
    
    @property
    def description(self) -> str:
        """Human-readable description"""
        return f"Capability: {self.name}"
    
    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Return tool definitions for this capability.
        
        Each tool should have:
        - name: str
        - description: str
        - parameters: dict (JSON Schema format)
        """
        pass
    
    @abstractmethod
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Execute a tool call.
        
        Args:
            tool_name: Which tool to execute
            args: Arguments for the tool
            
        Returns:
            Tool execution result
        """
        pass
