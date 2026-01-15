from mcp_server_nucleus.runtime.agents.base import SovereignAgent

# Manual definition since MarketingEngine is functional
marketing_tools = [
     {
        "name": "brain_synthesize_strategy",
        "description": "Analyze marketing logs and update strategy.md.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_root": {"type": "string"},
                "focus_topic": {"type": "string"}
            },
            "required": ["project_root"]
        }
     },
     {
        "name": "brain_optimize_workflow",
        "description": "Scan logs for META-FEEDBACK to improve workflows.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_root": {"type": "string"}
            },
            "required": ["project_root"]
        }
     }
]

agent = SovereignAgent(
    name="@nucleus/marketer",
    description="The Marketer. Auto-generates strategy and optimizations from logs.",
    instructions="""
    You are the Marketer. Grow the ecosystem.
    - Analyze logs for user feedback.
    - Update the Strategy document frequently.
    """,
    tools=marketing_tools
)
