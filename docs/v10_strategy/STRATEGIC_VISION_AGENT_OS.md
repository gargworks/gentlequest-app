# Strategic Vision: Nucleus as "OS of Agents"
*Synthesized from Perplexity Strategic Brainstorming (Jan 2026)*

## 1. The Core Definition
> "Nucleus is a host-runtime wrapped in a server-shaped interface for upstream compatibility."

Nucleus is the **Agent Control Plane** that aggregates other MCP tools. It solves the fragmentation of the MCP ecosystem by adding **Memory, Orchestration, and Governance**.

## 2. Recursive Aggregator Architecture
*   **Upstream (Server-Shaped)**: To Claude/Windsurf, Nucleus appears as a standard MCP server.
*   **Inward (Host-Like)**: Internally, Nucleus acts as a host that terminates the upstream connection and "fans out" to:
    *   **Native Tools**: MemoryOps, BrainOps, Audit.
    *   **Developer Hooks**: Local Python plugins (`.brain/tools/*.py`).
    *   **Mounted Servers**: External MCP servers (e.g., Postgres, GitHub via `npx`).

## 3. Governance: The Product Moat
"MCP standardizes connectivity; Nucleus standardizes governance."

*   **Explicit Consent**: Show the untruncated command before execution.
*   **Default Deny**: Start with no network/filesystem permissions.
*   **Isolation**: Keep servers isolated; only the Host (Nucleus) coordinates data transfer.
*   **Auth Boundary**: Forbid token passthrough. Nucleus handles rotation and storage.

## 4. Market Strategy: Sideloading to Marketplace
*   **Phase 1 (Sideloading)**: Drop `.py` files into `.brain/tools/`.
*   **Phase 2 (Mount Catalog)**: `nucleus mount @modelcontextprotocol/server-postgres`. 
*   **Strategy**: Leverage existing NPM/PyPI ecosystems rather than building a proprietary store.

## 5. SWOT Analysis
*   **Strengths**: Recursive positioning, Ecosystem leverage, Governance moat.
*   **Weaknesses**: Architecturally complex to explain, Security liability of mounting external servers.
*   **Opportunities**: "Default Toolchain" for agents, Safer mounting than raw clients.
*   **Threats**: Client disintermediation (Claude building their own OS layer).
