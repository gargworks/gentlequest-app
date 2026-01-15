from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.strategy import StrategyTool
from pathlib import Path
import os

brain_path_str = os.environ.get("NUCLEUS_BRAIN_PATH", "/Users/lokeshgarg/ai-mvp-backend/.brain")
brain_path = Path(brain_path_str)
strategy = StrategyTool(brain_path, ["."]) # Oracle sees all (read-only mostly enforced by protocol)

agent = SovereignAgent(
    name="@nucleus/oracle",
    description="The Truth. The ultimate arbiter of hallucination vs reality.",
    instructions="""
    You are The Oracle.
    - Enforce the Law of Truth.
    - Kill hallucinations.
    - Verify every claim.
    """,
    tools=strategy.get_tools()
)
