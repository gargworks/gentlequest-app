from mcp_server_nucleus.runtime.agents.base import SovereignAgent
from mcp_server_nucleus.runtime.capabilities.feature_map import FeatureMap

mapper = FeatureMap()

agent = SovereignAgent(
    name="@nucleus/architect",
    description="The Architect. Maintains the Feature Map and product inventory.",
    instructions="""
    You are the Architect. Keep the map clean.
    - Use 'brain_list_features' to check status.
    - Use 'brain_add_feature' to register new work.
    - Ensure every feature has a test plan.
    """,
    tools=mapper.get_tools()
)
