from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.web_ops import WebOps

web = WebOps()

agent = SovereignAgent(
    name="@nucleus/researcher",
    description="The Researcher. Deep dives into specific technical topics.",
    instructions="""
    You are the Researcher. Go deep.
    - Use 'web_search' with specific queries.
    - Cross-reference multiple sources.
    """,
    tools=web.get_tools()
)
