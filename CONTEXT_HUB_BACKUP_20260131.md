# 🧭 CONTEXT_HUB

Welcome to the **Lokesh Studio Operating System**. This document is the "Spine" of the environment. It maps our intelligence, protocols, and workflows across scattered repos and tools.

> [!IMPORTANT]
> **Agents (Antigravity/Windsurf/Cursor):** Always read this document first. It defines the canonical rules and locations for this workspace. **Do not modify files outside of this workspace unless explicitly asked.**

> [!TIP]
> **New here?** Read the full manual: [STUDIO_MANUAL.md](/Users/lokeshgarg/ai-mvp-backend/STUDIO_MANUAL.md) (Absolute path for clarity)

---

## 🛠️ Canonical Protocols (The OS)
These files define how we work, our tone, and our decision-making logic.

| Protocol | Location | Purpose |
| :--- | :--- | :--- |
| **Agents** | [AGENTS.md](./AGENTS.md) | Personas and mission roles. |
| **Rules** | [PROTOCOL.md](./PROTOCOL.md) | Technical constraints and "Rules of the House." |
| **Workflows** | [.agent/workflows/](./.agent/workflows/) | Executable slash commands and multi-step plans. |
| **Brain** | [.brain/](./.brain/) | Memory ledger, decision logs, and long-term context. |

---

## 🏗️ Studio Structure
We use a **Cellular Mitosis Strategy** to keep experiments clean and production safe.

*   **Mother Repo:** `~/ai-mvp-backend/` (Production MVP + Nucleus MCP).
*   **Experiments:** `~/experiments/` (Prototypes, legacy revivals).
*   **Apps:** `~/apps/` (Shippable products).
*   **Archive:** `~/archive/` (Cold storage).

> [!WARNING]
> **Cross-Linking Danger:** Do not symlink folders from the Mother Repo into Experiments. This risks accidental edits to production code. Use the **Copy-on-Need** strategy.

---

## 🚀 Creating a New Experiment
To bootstrap a new idea without contaminating the Mother Rep:

1.  **Run Scaffolder:**
    ```bash
    ./scripts/scaffold_experiment.sh my-new-idea
    ```
2.  **Open Workspace:** Point your IDE (Antigravity/Windsurf) to `~/experiments/my-new-idea`.
3.  **Read Local Context:** The script creates a `CONTEXT.md` in the experiment folder. Read it first.

---

## 🧪 Canonical Code Patterns
Don't reinvent the wheel. Reference these files in the Mother Repo (readonly) for patterns:

*   **AI/LLM Config:** `providers/gemini.py` (Key rotation, model config).
*   **Tool Use:** `providers/tools.py` (How to structure agent tools).
*   **Deployment:** `scripts/` (Render/GCP automation - *GentleQuest specific, treat as reference*).
*   **Memory:** `providers/memory.py` (Vector DB patterns).

---

## 🔗 Tool-Specific Context
*   **Antigravity:** Playgrounds live in `~/.gemini/antigravity/playground/`.
*   **Windsurf:** Global memories/rules in `~/.windsurf/`.
*   **Local State:** `.gemini/` files exist in project roots for local tool config.
