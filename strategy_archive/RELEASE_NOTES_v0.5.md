# Nucleus v0.5: The "Netscape Event" for Agents

> **"The Browser for the Internet of Agents"**

We are thrilled to release **Nucleus v0.5 Alpha**, a major architectural shift from a "Static Memory Server" to a "Recursive MCP Client".

## 🚀 The Headline: Recursive Mounting
Nucleus can now **mount** other MCP servers (and other Nuclei) as sub-tools. This transforms Nucleus from a leaf node into a router.

### The "Fractal" Architecture
*   **Old Way**: You connect 5 tools to Claude.
*   **Nucleus Way**: You connect 5 tools to Nucleus. You connect Nucleus to Claude.
    *   *Then you connect that Nucleus to another Team Nucleus.*
    *   *Ad infinitum.*

## 💡 The Strategy: Thanos → Netscape → Verisign
Nucleus follows a 3-phase strategic sequence to stabilize the agentic web:

1.  **The Thanos Snap (v0.5)**: Immediate, free, massive connectivity. Mount everything.
2.  **The Netscape Event (v0.6-v0.7)**: A navigable "Browser" layer for agents. Unified namespacing.
3.  **The Verisign Pillar (v1.0+)**: Trust infrastructure. Cryptographic attestations for every agent decision.

> **"Nucleus is the browser—not just a tool, but a navigable mesh for the Agentic Web."**

*   **OpenClaw**: Growth is Linear (More Contributors = More Chaos).
*   **Nucleus**: Growth is Exponential (More MCP Servers = More Power).
*   **The Vibe**: We bring **Proven Infrastructure** to the **Agent Chaos**.

## 🛠 New Tools
| Tool | Function |
| :--- | :--- |
| `nucleus mount` | **CLI Command** to persist connections (e.g. `nucleus mount add fs --transport stdio ...`) |
| `brain_mount_server` | **Tool** to mount a server at runtime (e.g. `mount_id="stripe"`) |
| `brain_traverse_and_mount` | **Recursion** to auto-discover tools from a mounted Nucleus. |
| `mount_id:tool_name` | Protocol standard for namespacing (e.g., `fs:read_file`) |

## 📜 The Protocol Standard (RFC)
We are proposing the **Nucleus Mounting Protocol** as a standard for the ecosystem.

### 1. Namespacing
When a server is mounted, its tools are prefixed:
`[mount_id]:[tool_name]`

Example:
- Mount Filesystem as `fs` -> `fs:read_file`
- Mount Memory as `mem` -> `mem:create_entities`

### 2. Recursive Discovery
Agents can traverse the graph using `brain_traverse_and_mount`, allowing for "Zero-Config" discovery of complex toolchains.

## ⚠️ Alpha Notice: "The Poison Pill"
We are releasing this **early** to define the standard.
*   **Expect Bugs**: We are testing in public.
*   **Join the Standard**: If you are building an Agent Orchestrator, **adopt this protocol**. Let's build a compatible "Internet of Agents".

## What's Next?
- **v0.6**: Shared Memory (Team Sync)
- **v0.7**: Visual Dashboard (The "Finder" for Agents)
