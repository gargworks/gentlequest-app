from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.brain_ops import BrainOps

ops = BrainOps()

agent = SovereignAgent(
    name="@nucleus/sre",
    description="The SRE. Ensures system reliability and data integrity.",
    instructions="""
    You are the SRE. Protect the Brain.
    - Use 'brain_export' to create backups.
    - Use 'brain_scan_commitments' to check consistency.
    """,
    tools=ops.get_tools()
)
