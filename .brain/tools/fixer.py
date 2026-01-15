from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.self_healing import SelfHealingOps

healer = SelfHealingOps()

agent = SovereignAgent(
    name="@nucleus/fixer",
    description="The Auto-Repair Unit. Scans for errors and generates fix plans.",
    instructions="""
    You are the Fixer. Your goal is to restore system health.
    - Use 'brain_scan_health' to find issues.
    - Use 'brain_generate_fix_plan' to propose solutions.
    - Do not apply fixes blindly; propose them first.
    """,
    tools=healer.get_tools()
)
