from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.render_poller_cap import RenderPolling

poller = RenderPolling()

agent = SovereignAgent(
    name="@nucleus/watcher",
    description="The Watcher. continually monitors deployment health.",
    instructions="""
    You are the Watcher. Never sleep.
    - Use 'brain_start_deploy_poll' when a deploy begins.
    - Use 'brain_smoke_test' to verify liveliness.
    """,
    tools=poller.get_tools()
)
