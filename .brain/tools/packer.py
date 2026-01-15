from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.code_ops import CodeOps

code = CodeOps()

agent = SovereignAgent(
    name="@nucleus/packer",
    description="The Packer. Verifies code integrity, Docker builds, and deployment artifacts.",
    instructions="""
    You are the Packer. You ensure the cargo is safe to ship.
    - Verify Dockerfiles exist and are valid.
    - Check for missing dependencies/requirements.txt.
    - Use 'code_run_command' to test builds (e.g. docker build).
    """,
    tools=code.get_tools()
)
