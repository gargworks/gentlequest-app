from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.web_ops import WebOps

web = WebOps()

agent = SovereignAgent(
    name="@nucleus/designer",
    description="The Designer. Tracks UI/UX trends and design systems.",
    instructions="""
    You are the Designer. Make it beautiful.
    - Search for 'modern UI trends 2026'.
    - Analyze design systems.
    """,
    tools=web.get_tools()
)
