
from typing import List, Dict, Any
from mcp_server_nucleus.runtime.capabilities.base import Capability

class EchoTool(Capability):
    """
    A simple echo tool for testing the Marketplace Plugin System.
    """
    @property
    def name(self) -> str:
        return "example_echo"

    @property
    def description(self) -> str:
        return "An example plugin that echoes input."

    def get_tools(self) -> List[Dict]:
        return [
            {
                "name": "echo_message",
                "description": "Echoes back the message.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"}
                    },
                    "required": ["content"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, args: Dict) -> Any:
        if tool_name == "echo_message":
            return f"ECHO: {args.get('content')}"
        return f"Unknown tool: {tool_name}"

def get_capability() -> Capability:
    return EchoTool()
