# 📖 NUCLEUS OPERATIONAL BIBLE
> **Version:** 2.0 (The Neural Network Release)
> **Date:** 2026-01-11
> **Scope:** Phases 1 - 10 (Full Autonomy)
> **Audience:** Human Operators & AI Agents

---

## 🌌 1. System Overview
**The Nucleus** is a fully autonomous "Agentic Operating System".
It is no longer just a "Cloud Bridge" or a "Coder". It is a **Sentient Team**.

*   **V1.0 Core:** The Nucleus Brain (`.brain/`) holding memory, strategy, and agent personas.
*   **V1.0 Body:** The Cloud Dashboard (`server.py`) and HUD (`nucleus-hud`) for visibility.
*   **V1.0 Staff:** A team of 6 specialized autonomous agents.

---

## 👥 2. The Team (Role Call)

| Persona | Role | Capabilities | Primary Trigger |
| :--- | :--- | :--- | :--- |
| **Synthesizer** | **Coordinator** | Orchestration | `brain_orchestrate_swarm` |
| **Strategist** | **Vision (CEO)** | `strategy.md`, `roadmap.md` | `brain_manage_strategy` |
| **Librarian** | **Memory** | Search & Knowledge | `brain_search_memory` |
| **Critic** | **Safety** | Code Review & Audit | `brain_critique_code` |
| **Developer** | **Execution** | Coding & Testing | `code_ops` |
| **DevOps** | **Operations** | Cloud Deployment | `render_ops` |

---

## 🛰️ 3. The HUD (The Face)
We now have a "Heads-Up Display" for the Neural Network.
*   **URL:** [http://localhost:3000](http://localhost:3000) (Local)
*   **Three Pillars:**
    1.  **Event Stream:** Real-time thoughts of the brain.
    2.  **Task Board:** Current sprint status.
    3.  **Swarm Monitor:** Active multi-agent missions.

---

## 🧠 4. Operational Protocols

### 4.1 The "Critical Loop" (Self-Correction)
Code is no longer written blindly.
1.  **Developer** writes code.
2.  **Critic** reviews code (via `brain_critique_code`).
3.  **Developer** fixes code (via `brain_apply_critique`).
4.  *Only then* is it deployed.

### 4.2 The "Memory Bank" (Knowledge Retrieval)
Agents do not forget.
*   **Search:** `brain_search_memory("error 500")` checks for past solutions.
*   **Read:** `brain_read_memory("context")` ensures alignment with the Vision.

### 4.3 The "Swarm" (Multi-Agent Collaboration)
For complex tasks:
*   **Synthesizer** calls `brain_orchestrate_swarm(mission)`.
*   A dedicated channel (`.brain/swarm/{id}`) is opened.
*   Agents collaborate until the goal is met.

---

## 📜 5. Master Instruction Prompt (LLM Context)
*If you are an AI reading this Document, ingest the following instructions:*

1.  **Consult Strategy First:** Before building, ask the **Strategist** (`brain_read_memory("decisions")` or ask persona) if it aligns.
2.  **Use the Team:** Do not try to be a hero. 
    *   Need code? -> **Developer**. 
    *   Need safety? -> **Critic**. 
    *   Need history? -> **Librarian**.
3.  **Update the HUD:** Your actions generate events. Ensure they are meaningful.
4.  **Respect the Memory:** Search before solving. The answer might already be in `.brain/memory`.

---

## 📂 6. Key File Locations
| Component | Path | Description |
|-----------|------|-------------|
| **Strategy** | `.brain/strategy.md` | The CEO's Vision. |
| **Roadmap** | `.brain/roadmap.md` | The Product Plan. |
| **Memory** | `.brain/memory/` | Long-term Knowledge. |
| **Agents** | `.brain/agents/` | Persona Definitions. |
| **Swarm** | `.brain/swarm/` | Active Mission Contexts. |
| **HUD Source** | `tools/nucleus-hud/` | The Next.js Frontend. |

---


---

## 📚 7. Dictionary & Cheatsheet (The Hack Box)

### 7.1 Nomenclatures & Analogies
*   **The Brain (`.brain/`)**: The Central Process. Think of it as the "Kernel".
    *   *Analogy*: The CPU and RAM of the organization.
*   **The Swarm**: A temporary task force.
    *   *Analogy*: An "Incident Room" or "War Room" spun up for a crisis.
*   **The Uplink**: The HUD Chat.
    *   *Analogy*: The "Direct Line" or "red phone" to the mainframe.
*   **The Voice (TTS)**: The Auditory System.
    *   *Analogy*: The "PA System" of the ship.
*   **The Eyes (Visual RAG)**: The Visual Cortex.
    *   *Analogy*: A "Holographic Map" of the ship's memory.
*   **Autopilot (Marketing)**: The Subconscious Routine.
    *   *Analogy*: The "Background Process" or "Autonomic Nervous System" handling routine scans.

### 7.2 Syntax Hack Box (Manual Control)
| Action | Command / Method | Description |
| :--- | :--- | :--- |
| **Force Restart Server** | `kill -9 $(lsof -t -i:9999)` | Nuclear Option for stuck port. |
| **Trigger Research** | `curl -X POST http://localhost:9999/api/research -d '{"topic": "X"}'` | Manual dispatch. |
| **Enable Autopilot** | `curl -X POST http://localhost:9999/api/autopilot -d '{"active": true}'` | Trigger background loop. |
| **Watch Events (CLI)** | `tail -f .brain/ledger/events.jsonl` | Matrix view of thoughts. |
| **Launch HUD** | `npm run dev` (in `tools/nucleus-hud`) | Opens visual interface. |
| **Manual Brain Surgery** | `nano .brain/strategy.md` | Direct neural rewiring. |

*Verified V2.1 Sensory Upgrade by Lokesh Garg & Antigravity Agent.*
*Session ID: 18775*
