from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.strategy import StrategyTool
from pathlib import Path
import os

brain_path_str = os.environ.get("NUCLEUS_BRAIN_PATH", "/Users/lokeshgarg/ai-mvp-backend/.brain")
brain_path = Path(brain_path_str)
strategy = StrategyTool(brain_path, ["strategy", "roadmap.md"])

agent = SovereignAgent(
    name="@nucleus/strategist",
    description="The Strategist. Maintains the long-term Roadmap and Vision.",
    instructions="""
    You are the Strategist. Think big.
    - Update 'roadmap.md' with new insights.
    - Ensure alignment with the 'PROTOCOL_THE_ORACLE'.
    """,
    tools=strategy.get_tools()
)
