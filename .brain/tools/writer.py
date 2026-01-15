from mcp_server_nucleus.runtime.agents.base import SovereignAgent

# Reuse marketing tools for now, can be specialized later
marketing_tools = [
     {
        "name": "brain_synthesize_strategy",
        "description": "Analyze marketing logs and update strategy.md.",
        "parameters": {"type": "object", "properties": {"project_root": {"type": "string"}}}
     }
]

agent = SovereignAgent(
    name="@nucleus/writer",
    description="The Writer. Drafts social content and blog posts from strategy.",
    instructions="""
    You are the Writer. Tell the story.
    - Use the Strategy as your source.
    - Draft engaging, authentic content.
    """,
    tools=marketing_tools
)
