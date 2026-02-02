# 🧭 CONTEXT_HUB

Welcome to the **Lokesh Studio Operating System**. This document is the "Spine" of the environment. It maps our intelligence, protocols, and workflows across scattered repos and tools.

> [!IMPORTANT]
> **Agents (Antigravity/Windsurf/Cursor):** Always read this document first. It defines the canonical rules and locations for this workspace. **Do not modify files outside of this workspace unless explicitly asked.**

> [!TIP]
> **New here?** Read the full manual: [STUDIO_MANUAL.md](./STUDIO_MANUAL.md) (Mother Repo–relative link; absolute path is `~/ai-mvp-backend/STUDIO_MANUAL.md`).

---

## 🛠️ Canonical Protocols (The OS)

These files define how we work, our tone, and our decision-making logic.

| Protocol   | Location                  | Purpose                                       |
| :---       | :---                      | :---                                          |
| **Agents** | [AGENTS.md](./AGENTS.md) | Personas and mission roles.                   |
| **Rules**  | [PROTOCOL.md](./PROTOCOL.md) | Technical constraints and "Rules of the House." |
| **Workflows** | [.agent/workflows/](./.agent/workflows/) | Executable slash commands and multi-step plans. |
| **Brain**  | [.brain/](./.brain/)     | Memory ledger, decision logs, and long-term context. |

---

## 🏗️ Studio Structure

We use a **Cellular Mitosis Strategy** to keep experiments clean and production safe.

- **Mother Repo:** `~/ai-mvp-backend/` (Production MVP + Nucleus MCP; canonical protocols and code patterns).
- **Experiments:** `~/experiments/` (Prototypes, legacy revivals, sandbox cells).
- **Apps:** `~/apps/` (Shippable products that graduate from experiments).
- **Archive:** `~/archive/` (Cold storage; retired experiments and artifacts).

> [!WARNING]
> **Cross-Linking Danger:** Do not symlink folders from the Mother Repo into Experiments. This risks accidental edits to production code. Use the **Copy-on-Need** strategy (copy patterns from Mother Repo into experiments instead of linking).

---

## 🚀 Creating a New Experiment

To bootstrap a new idea without contaminating the Mother Repo:

1. **Run Scaffolder:**
   ```bash
   ./scripts/scaffold_experiment.sh my-new-idea

