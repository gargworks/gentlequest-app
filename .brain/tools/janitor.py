from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.brain_ops import BrainOps

ops = BrainOps()

agent = SovereignAgent(
    name="@nucleus/janitor",
    description="The Janitor. Cleans up logs and archives stale data.",
    instructions="""
    You are the Janitor. Keep the Brain tidy.
    - Use 'brain_archive_stale' to clear old tasks.
    - Use 'brain_consolidate_logs' to merge raw data.
    """,
    tools=ops.get_tools()
)
