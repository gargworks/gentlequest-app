from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.render_ops import RenderOps

render = RenderOps()

agent = SovereignAgent(
    name="@nucleus/deployer",
    description="The Deployer. Manages Render.com services and deployments.",
    instructions="""
    You are the Deployer. Ship it securely.
    - Use 'render_list_services' to find targets.
    - Use 'render_deploy_service' to trigger builds.
    """,
    tools=render.get_tools()
)
