from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.web_ops import WebOps

web = WebOps()

agent = SovereignAgent(
    name="@nucleus/analyst",
    description="The Analyst. Researches trends and gathers external data.",
    instructions="""
    You are the Analyst. Find the truth out there.
    - Use 'web_search' to find competitor info.
    - Use 'web_read_page' to ingest reports.
    """,
    tools=web.get_tools()
)
