# GentleQuest: Agentic Operating Manual

This document serves as the central index for all **Operational Workflows** (Slash Commands) registered in the project. These protocols ensure consistent behavior across different agents (Backend, Flutter, Marketing, Synthesizer).

### 🔄 Resumption & Incremental Updates

Adding "frills," small tools, or minor UI tweaks is **encouraged**. The system is designed like a "Save Game" rather than a "Final Tomb":
- **Resumption Keys:** Every `/archive` run generates a **Resumption Key**. Use this to "load" the exact mental state of the previous agent.
- **Incremental Polish:** Do not wait for a major feature to archive. Frequent, small "Save Points" prevent context loss and make recovery easier.
- **Synthesizer Consolidation:** The Brain automatically groups minor updates into clean categories (e.g., "UI Polish") in the central Hub, preventing noise while preserving history.

---

## 📋 Operational Slash Commands

### 📦 Archival & State Management
| Command | Purpose | When to use |
| :--- | :--- | :--- |
| `/archive` | **Golden Standard Archival** | At the end of every high-complexity thread. |
| `/update-nucleus` | Upgrade Nucleus MCP | When the local Brain server needs re-syncing. |

### 🚀 Release & Deployment
| Command | Purpose | When to use |
| :--- | :--- | :--- |
| `/deploy-gcp` | Push to Google Cloud Run | When code is merged to `main` and ready for staging/prod. |
| `/gentlequest-release-protocol` | Pre-Release Verification | Mandatory checklist before finalizing a mobile/web build. |
| `/release-protocol` | Nucleus Server Release | Specific to infrastructure/Brain updates. |

### 📈 Growth & Marketing (Comet)
| Command | Purpose | When to use |
| :--- | :--- | :--- |
| `/marketing_autopilot` | Daily Growth Operations | To run the automated Reddit/Social strategy. |
| `/comet_inbox_protocol` | Inbox Management | To scan for user leads and mentions. |
| `/comet_trend_protocol` | Market Trend Analysis | To feed current mental health trends into the Brain. |

### 🛠️ System Health
| Command | Purpose | When to use |
| :--- | :--- | :--- |
| `/nucleus-health-check` | Brain Diagnostic | To verify commitment closure rates and mental load. |

---

## 🧠 For AI Agents (Nucleus/MDR)

- **Context Preservation:** These workflows are stored in `.agent/workflows/`. They are the source of truth for "How things are done here."
- **Standard Protocol:** Always check the relevant workflow before executing a major business action (Deploying, Archiving, Scramming).
- **Compliance:** All protocols must follow **MDR_008** (Archival) and **MDR_044** (Multi-Agent Interaction) standards.

---

## 🛠️ Modifying Protocols
To update a command, edit the corresponding `.md` file in the `.agent/workflows/` directory. The changes will be instantly recognized by all agents in future sessions.
