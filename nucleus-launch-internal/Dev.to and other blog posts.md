#  <#Title#>

# How I synced Cursor, Claude, and Windsurf with one shared brain (MCP)

![Nucleus Banner](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/d7e7pqczqn44tl8j537h.png)

The "AHA" moment for me wasn't when I first used an AI coder. It was when I realized I was **fragmented**.

I’d do a deep architectural brainstorm in **Claude**, switch to **Cursor** to implement, and then jump into **Windsurf** to use its agentic flow. But Claude didn't know what Cursor did, and Cursor had no idea about the architectural epiphany I just had in Claude.

I was manually copy-pasting my own "brain" across tabs. 

Then I built **Nucleus**.

![Nucleus Architecture](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/d7e7pqczqn44tl8j537h.png)

## The Architecture of Sovereignty

Nucleus is an **MCP (Model Context Protocol) Recursive Aggregator**. 

Instead of treating MCP servers as individual plugins, Nucleus treats them as a **Unified Control Plane**. It creates a local-first memory layer (we call them **Engrams**) that stays on your hardware. 

When I teach Claude something, it writes to the Nucleus ledger. When I open Cursor, Cursor reads that same ledger. **The context is no longer session-bound; it's persistent and sovereign.**

### Why This Matters (The "Governance" Bit)

We’ve all seen the security warnings about giving agents full filesystem access. Nucleus solves this with a **Hypervisor** layer:

1.  **Default Deny**: No tool gets access to your drive unless explicitly granted.
2.  **DSoR (Decision System of Record)**: Every single tool call and agent decision is SHA-256 hashed and logged. You can audit precisely *why* an agent decided to delete a file.
3.  **Local First**: Your strategic data never leaves your machine. 

## The Stack
- **Python/MCP** for the recursive server logic.
- **Local-first storage** for the data layer.
- **Control Plane UI** (Planned / Coming Soon).

## Join the Sovereign Movement

We just open-sourced the v1.0.5 (Sovereign) release on GitHub. 

If you're tired of being a "context-courier" between agents, come check it out. 

👉 **[Nucleus on GitHub](https://github.com/eidetic-works/nucleus-mcp)**
👉 **[PyPI: mcp-server-nucleus](https://pypi.org/project/mcp-server-nucleus/)**
👉 **See it in action (Sovereign Master V19):** [![Watch the demo](https://img.youtube.com/vi/jI8TUpfjS1A/0.jpg)](https://www.youtube.com/watch?v=jI8TUpfjS1A)

Let’s stop building silos and start building a shared brain. 🚀🌕

#mcp #ai #agents #opensource #productivity


------
Dev.to copy
------

Nucleus social banner on top with logo wide

How I synced Cursor, Claude, and Windsurf with one shared brain (MCP)
#
mcp
#
ai
#
opensource
#
productivity

The "AHA" moment for me wasn't when I first used an AI coder. It was when I realized I was **fragmented**.

I’d do a deep architectural brainstorm in **Claude**, switch to **Cursor** to implement, and then jump into **Windsurf** to use its agentic flow. But Claude didn't know what Cursor did, and Cursor had no idea about the architectural epiphany I just had in Claude.

I was manually copy-pasting my own "brain" across tabs. 

Then I built **Nucleus**.
![Nucleus Architecture](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/d7e7pqczqn44tl8j537h.png)

## The Architecture of Sovereignty

Nucleus is an **MCP (Model Context Protocol) Recursive Aggregator**. 

Instead of treating MCP servers as individual plugins, Nucleus treats them as a **Unified Control Plane**. It creates a local-first memory layer (we call them **Engrams**) that stays on your hardware. 

When I teach Claude something, it writes to the Nucleus ledger. When I open Cursor, Cursor reads that same ledger. **The context is no longer session-bound; it's persistent and sovereign.**

### Why This Matters (The "Governance" Bit)

We’ve all seen the security warnings about giving agents full filesystem access. Nucleus solves this with a **Hypervisor** layer:

1.  **Default Deny**: No tool gets access to your drive unless explicitly granted.
2.  **DSoR (Decision System of Record)**: Every single tool call and agent decision is SHA-256 hashed and logged. You can audit precisely *why* an agent decided to delete a file.
3.  **Local First**: Your strategic data never leaves your machine. 

## The Stack
- **Python/MCP** for the recursive server logic.
- **Local-first storage** for the data layer.
- **Control Plane UI** (Planned / Coming Soon).

## Join the Sovereign Movement

We just open-sourced the v1.0.5 (Sovereign) release on GitHub. 

If you're tired of being a "context-courier" between agents, come check it out. 

👉 **[Nucleus on GitHub](https://github.com/eidetic-works/nucleus-mcp)**
👉 **[PyPI: nucleus-mcp](https://pypi.org/project/nucleus-mcp/)**
👉 **See it in action (Sovereign Master V19):** [![Watch the demo](https://img.youtube.com/vi/jI8TUpfjS1A/0.jpg)](https://www.youtube.com/watch?v=jI8TUpfjS1A)

Let’s stop building silos and start building a shared brain. 🚀🌕
