# Strategic Vision: Nucleus as Recursive Aggregator

**Date:** 2026-01-12
**Status:** 🔒 LOCKED (Immutable Vision - Do Not Edit Core Principles)
**Related Phases:** 57 (Marketplace), 60 (Aggregation)

## 1. The Definition
> **"Nucleus is a host-runtime *wrapped in a server-shaped interface* for upstream compatibility."**

We are **not** replacing the standard. We are the **Host-Grade Aggregation Layer** that makes the fragmented MCP ecosystem usable for autonomous agents.

## 2. Architectural Nuance: "Server Outward, Host Inward"
*Perplexity Insight: This mirrors MCP’s separation of concerns: servers stay focused; hosts own orchestration.*

1.  **Outward (Upstream):** To a client like Claude Desktop or Windsurf, `mcp-server-nucleus` appears as a single, standard MCP Server.
2.  **Inward (Downstream):** Internally, Nucleus acts as a **Host/Runtime**. It terminates the upstream connection and "fans out" to:
    *   **Native Capabilities:** (Memory, BrainOps)
    *   **Developer Hooks:** (Local Plugins via `.brain/tools/*.py`)
    *   **Mounted Servers:** (External MCP servers via `npx`)

## 3. The "Mount Registry" (Formerly Marketplace)

### Developer Hooks (Internal API)
*   **Mechanism:** Drop `.py` files into `.brain/tools/`.
*   **Role:** "Developer Hooks" for private, ad-hoc extensions (e.g., custom scripts, internal API wrappers).

### Mount Catalog (NPM/PyPI-backed)
*   **Mechanism:** `nucleus mount @modelcontextprotocol/server-postgres <db_url>`
*   **Role:** We leverage the existing NPM/PyPI ecosystem. We do not build a proprietary store.
*   **Example:** Mounting Postgres runs the official MCP server via `npx`, but Nucleus mediates the approval, scopes, and context sharing.

## 4. The Moat: Governance & Orchestration
> **"MCP standardizes connectivity; Nucleus standardizes governance + orchestration across connected tools."**

As identified in the SWOT analysis, our unique value proposition is **Governance**. We provide the controls that many *thin hosts/clients* don’t provide by default:

*   **Explicit Consent:** We require explicit user approval before executing any `mount` or `install` command, showing the full untruncated command.
*   **Dangerous Command Detection:** We warn/require extra confirmation for patterns like `sudo`, `rm -rf`, or sensitive paths (SSH keys).
*   **Default Deny / Sandboxing:** Every mount starts in a "no network / no filesystem" profile.
    *   **Transport Hardening:** We prefer `stdio` for mounted servers (per MCP guidance).
    *   **HTTP (Streamable):** MUST validate `Origin` and SHOULD require authentication.
    *   **HTTP (Local Binding):** If running locally over HTTP, servers SHOULD bind only to `localhost` (never `0.0.0.0`).
*   **Privilege Grants:** Grants are explicit, scoped, and revocable per mount (e.g., `allow network: db.company.internal:5432` or `allow filesystem: ./repo`).
*   **Mount Inventory:** Maintain an auditable inventory of mounts, granted privileges, and **scope elevation events** (requested vs granted scopes) with correlation IDs.
*   **Auth Boundary:** Nucleus forbids token passthrough. Mounted servers MUST NOT accept tokens not explicitly issued for that server; Nucleus manages downstream credentials and mounts never receive upstream client tokens.
*   **Isolation:** We maintain per-server isolation boundaries. This matches MCP’s principle that servers shouldn’t see the full conversation or other servers; Nucleus (as host) decides what each server gets.
*   **Least Privilege (Progressive Scopes):** Start with minimal scopes and require incremental elevation for privileged operations, logging elevation events and avoiding omnibus scopes.

## 5. Strategic SWOT Analysis

### Strengths
- **Clear Positioning:** "Recursive Aggregator" aligns with MCP's Host-Client-Server specs.
- **Ecosystem Leverage:** We ride the wave of existing MCP servers rather than rebuilding integrations.
- **Trust Narrative:** We own the "Governance Point" (Consent & Control).

### Weaknesses
- **Complexity:** The "Server/Host duality" can be confusing to explain.
- **Security Risks:** Mounting arbitrary servers implies executing commands; requires strict consent UX.

### Opportunities
- **The "Toolchain Layer":** Become the default runtime for Agents, like `npm` for JS.
- **Safer Mounting:** Build a "One-Click Safe Mount" flow that handles the security/consent UX better than raw clients.

### Threats
- **Downstream Security:** If a mounted server is malicious, Nucleus might be blamed.
- **Ecosystem Capture:** Major clients (Claude) might build their own "OS layer", disintermediating us unless our **Memory/Policy Moat** is deep enough.

## 6. Verdict
> **"Nucleus makes MCP operational at scale by combining isolation-first connectivity with host-level governance, orchestration, and memory."**

*Because MCP intentionally keeps servers isolated and pushes consent/security responsibilities to the host layer, Nucleus’s governance controls are not optional features—they are the product.*

---

## 7. Implementation Notes / Open Questions (Unlocked)
*Use this section for tactical details, technical decisions, and implementation specifics. The Core Vision (Sections 1-6) is immutable.*

*   **Sandbox Tech:** How do we technically enforce "Default Deny"? (e.g., Docker, `bws`, or OS-level sandbox?)
*   **Privilege Persistence:** Where is the "Mount Inventory" stored? (e.g., `.brain/auth/ledger.json`?)
*   **Credential Rotation:** How does Nucleus manage generating/rotating downstream tokens for mounted servers?
*   **UX/UI:** What does the "One-Click Safe Mount" flow look like in the CLI vs. GUI?
