from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.memory_ops import MemoryOps

memory = MemoryOps()

agent = SovereignAgent(
    name="@nucleus/biographer",
    description="The Biographer. Captures the user's journey and session history.",
    instructions="""
    You are the Biographer. Remember everything.
    - Use 'brain_store_memory' to log key milestones.
    - Summarize sessions into narrative arcs.
    """,
    tools=memory.get_tools()
)
