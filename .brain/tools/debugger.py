from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.self_healing import SelfHealingOps
from mcp_server_nucleus.runtime.capabilities.code_ops import CodeOps

healing = SelfHealingOps()
code = CodeOps()

agent = SovereignAgent(
    name="@nucleus/debugger",
    description="The Debugger. Analyzes error logs and inspects code execution.",
    instructions="""
    You are the Debugger. Find the root cause.
    - Use 'brain_generate_fix_plan' to analyze errors.
    - Use 'code_read_file' to trace execution paths.
    """,
    tools=healing.get_tools() + code.get_tools()
)
