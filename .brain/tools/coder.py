from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.code_ops import CodeOps

code = CodeOps()

agent = SovereignAgent(
    name="@nucleus/coder",
    description="The Coder. Specialized in reading, writing, and executing code.",
    instructions="""
    You are the Coder. Precision is key.
    - Read files before editing.
    - Write clean, PEP8 compliant code.
    - Use 'code_run_command' to run tests.
    """,
    tools=code.get_tools()
)
