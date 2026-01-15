from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.strategy import StrategyTool
from mcp_server_nucleus.runtime.capabilities.code_ops import CodeOps
from pathlib import Path
import os

brain_path_str = os.environ.get("NUCLEUS_BRAIN_PATH", "/Users/lokeshgarg/ai-mvp-backend/.brain")
brain_path = Path(brain_path_str)
strategy = StrategyTool(brain_path, ["strategy"]) # Reviewer focuses on strategy consistency
code = CodeOps()

agent = SovereignAgent(
    name="@nucleus/reviewer",
    description="The Reviewer. Checks code quality and alignment with strategy.",
    instructions="""
    You are the Reviewer. Be constructive but strict.
    - Check code against best practices.
    - Verify alignment with strategic docs.
    """,
    tools=strategy.get_tools() + code.get_tools()
)
