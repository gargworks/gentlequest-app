# 🌌 MEGA MASTER CONTEXT: NUCLEUS OPERATING PROTOCOL (NOP) v0.6.0
> **Primary Directive:** This document is the absolute "Source of Truth" for Cloud Opus (Model V-Next). It synthesizes all strategic, architectural, and operational context from the Phase 2 Research Cycle (Jan 24, 2026). 

---

## 🏁 1. SYSTEM INTEGRITY & HANDOFF STATE
- **Project Root:** `/Users/lokeshgarg/ai-mvp-backend/`
- **Current Version:** v0.5.0 (Pre-DSoR)
- **Target Version:** v0.6.0 (Decision System of Record)
- **Status:** **Research Complete.** The core `mcp-server-nucleus` source has been verified as pristine since Jan 22, 2026. No research prototypes were merged into the main runtime yet.

---

## 🔭 2. STRATEGIC VISION: THE "MECHA-ORGANISM"
The Nucleus ecosystem follows Foundation Capital's "Trillion Dollar Elephant" thesis (Enterprise AI Longevity). We are building a system that combines **Elastic Scale** with **Verified Alignment**.

### The Trinity of Agentic Leverage
1. **Elastic Scale (Choreography):** Dynamic swarms that self-assemble.
2. **Verified Alignment (Orchestration):** Using `DecisionMade` events to create an immutable "Why" trace.
3. **Digital Intuition (Memory):** `ContextManager` hashing for world-state verification.

---

## 🏗️ 3. ARCHITECTURE: DECISION SYSTEMS OF RECORD (DSoR)
Cloud Opus must transition the runtime from simple "Tool Execution" to "Decision Provenance."

### A. Core Source Files (Entry Points)
- **Agent Logic:** [`agent.py`](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/agent.py)
- **Main Loop:** [`agent.py:L69-272`](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/agent.py#L69-272) (Reasoning turn implementation)
- **Orchestrator:** [`orchestrator.py`](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/orchestrator.py)

### B. New DSoR Schema (Partially Implemented)
Classes are already defined in [`agent.py:L13-33`](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/agent.py#L13-33):
- `DecisionMade`: Captures `reasoning`, `context_hash`, and `confidence`.
- `ActionRequested`: Links the `action_id` to the `decision_id` (The "What" linked to "Why").

### C. The Context Graph Pattern
Instead of simple vector search, v0.6.0 introduces a **Knowledge Mesh**.
- **Context Manager:** Proposed stateless service to hash merged Reference Docs + Recent Events.
- **Trace API:** Proposed GraphQL/REST endpoint to audit mission causality.

---

## 🛡️ 4. SECURITY: V9 VULNERABILITY AUDIT
Four critical risks must be remediated in v0.6.0. Full report: [V9_VULNERABILITY_REPORT.md](file:///Users/lokeshgarg/ai-mvp-backend/V9_VULNERABILITY_REPORT.md).

| Vulnerability | Impact | Fix Strategy |
| :--- | :--- | :--- |
| **The Sidecar Exploit** | Session Hijacking | Per-request auth tokens for IPC socket. |
| **The Pricing Rebellion** | Billing Bypass | Metering based on `DecisionMade` events. |
| **The Marketplace Poisoning** | WASM Sandbox Escape | Logic-bomb detection / WASI hardening. |
| **The Trust Leak** | ZK Promise Erosion | Mirror all outbound ZK-Cloud hashes to local ledger. |

---

## ⚙️ 5. OPERATIONAL CODEX & FAILURE RECOVERY
The system currently implements several "Ghost" and "Orphan" persistence patterns to prevent context loss during failures.

### A. Failure Recovery Logic ([agent.py](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/agent.py))
- **Ghost Completion Fix ([L161-206](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/agent.py#L161-206)):** Ensures mission summaries are persisted even if the runtime terminates abruptly.
- **Orphan Persistence ([L232-262](file:///Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/src/mcp_server_nucleus/runtime/agent.py#L232-262)):** Saves agent reasoning to `.brain/swarms/orphan_outputs/` if a tool call fails after critique.

### B. Session Results (Jan 24 Cycle)
- **Primary Research Specs:** [/brain/swarms/orphan_outputs/critic_failure_Architect_1769223759.md](file:///Users/lokeshgarg/ai-mvp-backend/.brain/swarms/orphan_outputs/critic_failure_Architect_1769223759.md)
- **Research Walkthrough:** [/brain/be2077e7-1cf1-4df9-a7c2-16764e9974d6/walkthrough.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/be2077e7-1cf1-4df9-a7c2-16764e9974d6/walkthrough.md)
- **Consolidated Interaction Log:** `.brain/archive/raw_interactions_2026-01-24.jsonl`

---

## 🚀 6. MISSION DIRECTIVES FOR CLOUD OPUS
1. **Inject Audit Logic:** Modify `EphemeralAgent._run_llm` to emit `DecisionMade` events *before* every `_execute_tool` call.
2. **Context Manager Bootstrap:** Create `mcp_server_nucleus/runtime/context_manager.py` to handle context snapshotting and hashing.
3. **Audit Readiness:** Ensure the DSoR trace is available via a new tool `brain_get_decision_history`.

---
*Synthesized by Antigravity (Agentic AI).*
