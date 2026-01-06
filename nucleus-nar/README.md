# Nucleus Agent Runtime (NAR)

> **Serverless Cognitive Threads for LLM Applications**

NAR is the open-source "Agent Operating System" that powers the Nucleus ecosystem. It provides:

- **Context Factory**: Maps intent → persona → constrained toolset
- **Ephemeral Agents**: Spawn, execute, terminate (zero idle cost)
- **Capability System**: Modular tool registration and isolation

## Philosophy

NAR treats AI agents as **ephemeral compute units**, not "digital employees."

| Traditional Agents | NAR Agents |
|:-------------------|:-----------|
| Stateful (memory across sessions) | Stateless (fresh context each time) |
| Fixed roles ("Developer Agent") | Dynamic personas per intent |
| 50+ tools dumped into context | Constrained toolsets (5-10 max) |
| Long-running, expensive | Spawn-execute-terminate |

## Quick Start

```python
from nucleus_nar import ContextFactory, EphemeralAgent

# 1. Initialize Factory
factory = ContextFactory()

# 2. Create Context from Intent
context = factory.create_context(
    session_id="deploy-001",
    intent="Deploy the backend service to production"
)

# 3. Spawn and Run Agent
agent = EphemeralAgent(model=your_llm_model, context=context)
result = await agent.run()
```

## Creating Custom Capabilities

```python
from nucleus_nar.runtime.capabilities.base import Capability

class MyCapability(Capability):
    @property
    def name(self) -> str:
        return "my_capability"
    
    def get_tools(self):
        return [
            {"name": "my_tool", "description": "Does something", "parameters": {...}}
        ]
    
    def execute_tool(self, tool_name, args):
        if tool_name == "my_tool":
            return "Result!"
        return f"Unknown tool: {tool_name}"

# Register with factory
factory.register(MyCapability())
```

## Why Open Source?

NAR is **the engine**. The value is in:
- Your **Brain** (personal data, context, memory) - Not open source
- Your **Orchestration** (custom workflows) - Not open source

You can clone NAR. You cannot clone the relationship it builds with you.

## License

MIT License - Use it, fork it, build with it.

---

Built by [@LKGargProjects](https://github.com/LKGargProjects) | Part of the Nucleus Ecosystem
