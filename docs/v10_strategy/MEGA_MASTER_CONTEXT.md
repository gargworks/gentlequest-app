# 🌌 MEGA MASTER CONTEXT: NUCLEUS OPERATING PROTOCOL

> **Primary Directive:** This document is the "Source of Truth" for Cloud Opus (Model V-Next). It synthesizes the entire strategic, architectural, and operational state of the Nucleus project as of Phase 2 (Jan 24, 2026).

---

## 1. 🔭 Strategic Vision: The "Mecha-Organism"
**Thesis:** Foundation Capital's "Trillion Dollar Elephant" (Enterprise AI Longevity).
**Core Concept:** We are building a "Mecha-Organism"—a system that combines the **Elastic Scale** of cloud swarms with the **Verified Alignment** of local ledgers and the **Digital Intuition** of a shared World Model.

### The Trinity of Agentic Leverage (NOP v3.0)
1.  **Elastic Scale (Choreography):** Event-driven swarms that spawn/dissolve purely based on demand.
2.  **Verified Alignment (Orchestration):** Use of `DecisionMade` events to create an immutable "Why" trace for every action.
3.  **Digital Intuition (Memory):** A `ContextManager` that hashes the world-state to verify decision validity.

---

## 2. 🏗️ Architecture: Decision Systems of Record (DSoR)
**Status:** Research Complete (v0.5.0) -> Implementation Ready (v0.6.0).

### A. The "Why" Link Problem
Current agents log *what* they did (`ToolCall`), but not *why* (`Reasoning`). This makes enterprise audit impossible.
**Solution:** The DSoR Pattern.

### B. New Event Schema
Cloud Opus must implement these event types in `mcp_server_nucleus/runtime/agent.py`:

```python
class DecisionMade(Event):
    decision_id: str
    parent_context_hash: str  # Hash of the Context Graph snapshot
    reasoning_trace: str      # The Chain-of-Thought
    confidence_score: float
    alternatives_considered: List[str]

class ActionRequested(Event):
    action_id: str
    linked_decision_id: str   # The Foreign Key to the "Why"
    tool_name: str
    tool_args: Dict
```

### C. Context Graph Service (`ContextManager`)
A stateless service that:
1.  **Assembles:** Merges Reference Docs + Recent Events + Vector Memory.
2.  **Hashes:** Generates a SHA-256 signature of the inputs.
3.  **Serves:** Allows Agents to "hop" from a Decision back to the exact files that informed it.

---

## 3. 🛡️ Security & Vulnerability Landscape (V9 Report)
**Critical Risks Identified (MUST FIX in v0.6.0):**

1.  **The Sidecar Exploit (CVE-2026-001):**
    *   *Risk:* Malicious VS Code extensions hijacking the unauthenticated IPC socket.
    *   *Fix:* Implement per-request authorization tokens for the `nucleusd` daemon.

2.  **The Pricing Rebellion:**
    *   *Risk:* "Hydra Agents" multiplexing tasks to evade the per-agent billing meter.
    *   *Fix:* Metering based on `DecisionMade` events (Cognitive Ops), not just "Active Agent" count.

3.  **The "Trust Leak":**
    *   *Risk:* No user-visible log of encryption operations before data leaves to the ZK Cloud.
    *   *Fix:* Mirror all outbound payload hashes to the local `events.jsonl` ledger.

---

## 4. ⚙️ Operational Codex

### A. Swarm Orchestration
*   **Launcher:** `scripts/launch_research_swarm.py`
*   **Mechanism:** Uses `SwarmsOrchestrator` to spawn `EphemeralAgent` instances.
*   **Recovery:** If an agent fails to call a tool, the `EphemeralAgent._run_turn` loop has a "Ghost Completion Fix" that saves findings to `.brain/swarms/orphan_outputs/`.

### B. Session Persistence
*   **Command:** `nucleus sessions save` (or manual script `verify_researcher_agent.py`).
*   **Artifacts:**
    *   Daily Logs: `.brain/archive/raw_interactions_YYYY-MM-DD.jsonl`
    *   Vector Memory: Stored via `memory_ops.brain_store_memory`.

---

## 5. 🧬 Core Interface Definitions
(Reference for Cloud Opus to understand the Runtime without indiscriminate reading)

### `EphemeralAgent` (The Brain)
```python
class EphemeralAgent:
    def __init__(self, context: AgentContext, model: DualEngineLLM):
        self.context = context  # Contains tools, memories, objectives
        self.model = model      # The Brain (Gemini/Vertex)

    async def run(self) -> str:
        # 1. Loads Prompt Template (nucleus-smart-v2)
        # 2. Enters Reasoning Loop (Max 15 turns)
        # 3. Emits 'DecisionMade' (Proposed v0.6.0)
        # 4. Executes Tool
        # 5. Auto-recovers from JSON errors
```

### `Capability` (The Body)
```python
class Capability(ABC):
    @abstractmethod
    def get_tools(self) -> List[Dict]:
        """Exposes raw MCP tool definitions for the LLM."""
        pass
        
    @abstractmethod
    def execute_tool(self, tool_name: str, args: Dict) -> Any:
        """Route execution to local logic or external API."""
        pass
```

---

## 6. 🗺️ File Ecosystem (The Spine)
*   `CONTEXT_HUB.md`: The OS Manual (Project Root).
*   `.brain/`: The Cortex (Memory, Ledger, Artifacts).
*   `mcp-server-nucleus/`: The Runtime (Python Source).
*   `scripts/`: The Automation Layer.

---
*Generated: Jan 24, 2026 | Priority: CRITICAL*
