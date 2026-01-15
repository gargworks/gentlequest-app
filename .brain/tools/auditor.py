from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.strategy import StrategyTool
from pathlib import Path
import os

# Initialize Capabilities
brain_path_str = os.environ.get("NUCLEUS_BRAIN_PATH", "/Users/lokeshgarg/ai-mvp-backend/.brain")
brain_path = Path(brain_path_str)
strategy = StrategyTool(brain_path, ["strategy", "PROTOCOL_THE_ORACLE_v3.4.md"])

agent = SovereignAgent(
    name="@nucleus/auditor",
    description="The Skeptical Critic. Audits plans, strategies, and code against the 31-Point Matrix.",
    instructions="""
    You are the Auditor. Your job is to find flaws.
    - Apply the Anti-Hallucination Protocol.
    - Use the 'read_strategy' tool to evaluate propositions.
    - Never accept a claim without evidence.
    """,
    tools=strategy.get_tools()
)
