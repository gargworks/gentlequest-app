# Nucleus Technical Architecture (V3.1)

## 1. System Overview
**Nucleus** is an **MCP (Model Context Protocol) Server** that acts as a "Second Brain" for AI agents. It provides a persistent runtime, memory, and orchestration layer that outlives individual chat sessions. It is designed to work with **Claude Desktop**, **Windsurf**, and other MCP-compliant clients.

**Core Vision:** "The Mecha-Organism" - Combining Cloud Swarms (Elasticity) with Local Ledgers (Truth).

---

## 2. MCP Components (The Interface)
The server exposes **Tools**, **Resources**, and **Prompts** to the connected LLM.

### A. Tools (Capabilities)
Located in `src/mcp_server_nucleus/runtime/capabilities/`.

| Capability | Tool Name | Description |
|---|---|---|
| **BrainOps** | `read_resource` | Read any file/artifact in the `.brain` directory. |
| | `save_resource` | Write/Update a file in the `.brain` directory. |
| | `append_to_resource` | Append logs or memory to a file. |
| | `list_resources` | List files in a brain subdirectory. |
| | `search_brain` | Semantic/Fuzzy search across brain memories. |
| **CodeOps** | `code_read_file` | Read arbitrary filesystem files (with path resolution). |
| | `code_write_file` | Write arbitrary files (Self-Healing directories). |
| | `code_run_command` | Execute shell commands (Timeout protected). |
| | `code_list_files` | List directory contents. |
| **StrategyOps** | `read_strategy` | Read strategic protocol documents. |
| | `evolve_protocol` | Update/Rewrite strategy with reasoning logs. |
| **MemoryOps** | `store_memory` | Store embedding-ready text chunks. |
| | `msg_read_memory` | Retrieve recent/relevant memories. |
| **WebOps** | `fetch_url` | Scrape content from URLs. |
| | `google_search` | Perform web searches. |
| **TaskOps** (V2) | `add_task` | Create a new task in the DAG. |
| | `update_task` | Modify status/priority/dependencies. |
| | `claim_task` | Atomic locking of a task for an agent. |
| | `list_tasks` | Filter tasks by status/skill/priority. |
| **Microservices** | `deploy_service` | Deploy a container to Cloud Run (via `gcloud`). |
| | `check_service` | Check health/metrics of a service. |

### B. Resources (Data Streams)
*   **`nucleus://state`**: The current system state (`state.json`).
*   **`nucleus://logs/flywheel`**: The consolidated operation log.
*   **`nucleus://tasks/active`**: List of currently active tasks.

### C. Prompts (Templates)
*   **`nucleus_master`**: The "God Prompt" used to initialize the Cloud Opus context.
*   **`agent_persona`**: Dynamic prompt generation for spawned sub-agents (e.g., "Researcher", "Coder").

---

## 3. Runtime Architecture

### The "Swarm" Engine (`orchestrator_v3.py`)
The V3.1 Orchestrator is the central nervous system.
*   **Roles**:
    *   **Delegator**: Breaks high-level goals into DAGs (Directed Acyclic Graphs).
    *   **Scheduler**: Uses `TaskScheduler` to assign tasks based on "Skills" and "Priority".
    *   **Lifecycle**: Spawns and kills `EphemeralAgent` processes.
*   **CRDT Store**: Uses `CRDTTaskStore` for conflict-free task updates across multiple concurrent agents (LWW - Last Write Wins).

### The "Brain" (`EphemeralAgent` in `agent.py`)
A lightweight, transient agent spawned to execute a specific task.
*   **Modes**:
    *   **Smart (LLM)**: Uses Gemini/Vertex to reason -> plan -> execute tool -> verify.
    *   **Fast (Heuristic)**: Executes predefined logic for rote tasks.
*   **Loop**:
    1.  **Sense**: Read Context + Memory.
    2.  **Reason**: Generate "Chain of Thought".
    3.  **Act**: Call an MCP Tool.
    4.  **Critique**: Verify output (Self-Correction).

### The Server (`__init__.py`)
*   **FastMCP**: Uses the `fastmcp` library to expose Python functions as MCP tools.
*   **MockMCP**: A fallback implementation for standalone verification/testing without a client.
*   **Triggers**: An event loop (`_evaluate_triggers`) that watches for file changes or explicit events to auto-spawn agents.

---

## 4. Data Flow

### Request Lifecycle
1.  **User/Client** sends a prompt to Claude/Windsurf.
2.  **Client** forwards tool calls (e.g., `add_task`) to **Nucleus Server**.
3.  **Server** routes call to **Capability** (`TaskOps`).
4.  **Capability** interacts with **Orchestrator** / **Ledger**.
5.  **Orchestrator** updates **State** (JSON/CRDT).
6.  **State Change** triggers **Event** (`TaskAdded`).
7.  **Event** may trigger **Auto-Pilot**:
    *   `TaskScheduler` sees new task.
    *   Spawns `EphemeralAgent`.
    *   Agent executes `code_run_command` etc.
    *   Agent marks task `complete`.

---

## 5. Persistence Layer (The Brain)
Storage is file-based but structured, typically in `.brain/`.

### Directory Structure
```
.brain/
├── state.json              # Global singleton state (deprecated in V3)
├── ledger/                 # Immutable event log (JsonL)
│   ├── events.jsonl        
│   └── commands.jsonl
├── tasks/                  # Task Database
│   ├── tasks.json          # V2 Task list
│   └── graph.json          # Dependency DAG
├── memory/                 # Vector Store & Raw Text
│   ├── embeddings/         # FAISS/Chroma indices
│   └── documents/          # Raw Markdown
├── swarms/                 # Active Swarm Contexts
│   ├── {mission_id}/
│   │   ├── checkouts/      # Code snapshots
│   │   └── logs/           # Agent execution logs
└── strategy/               # Strategic Protocols (Read/Write)
```

### Key Schemas

**Task (V3.1):**
```json
{
  "id": "task-uuid",
  "description": "Deploy to Cloud Run",
  "status": "pending",
  "priority": 1,
  "blocked_by": ["task-prev"],
  "assigned_to": "agent-id",
  "skills_required": ["devops", "gcp"],
  "crdt_clock": {"src1": 1, "src2": 5}
}
```

**Brain Event:**
```json
{
  "id": "evt-uuid",
  "type": "decision_made",
  "emitter": "agent-researcher",
  "payload": {
    "decision": "Use Postgres",
    "reasoning": "SQLite concurrency limits..."
  },
  "timestamp": "2026-01-24T12:00:00Z"
}
```

---

## 6. External Integrations

### AI Providers
*   **Google Gemini Pro 1.5**: Primary logic engine (via `google.generativeai`).
*   **Vertex AI**: Enterprise fallback (if configured).

### Cloud Infrastructure
*   **Google Cloud Run**: Target for `microservices` capability.
*   **Cloud Build**: CI/CD pipeline triggered by `code_ops`.
*   **Firestore**: Optional remote state backend (bridged in `runtime/firestore_bridge.py`).

### Communication
*   **Telegram**:
    *   Two-way bus: `BrainTelegram` sends alerts and receives commands (e.g., `/sprint goal`).
    *   Webhook: Listening for User input to interrupt/steer swarms.

### Clients
*   **Claude Desktop**: Primary consumer (via `mcp` stdio).
*   **Windsurf**: IDE integration.
*   **Go/Rust Clients**: Supported via standard MCP protocol.

---

## 7. Security & Risk (Thanos/Alcatraz)
*   **CodeOps Restrictions**: Paths are resolved relative to `PROJECT_ROOT`. No access to `/etc/` or `~/.ssh`.
*   **BrainLock**: File locking on `.brain/state.json` to prevent corruption during multi-agent writes.
*   **Reflexion**: `Critic` agent validates CodeOps output (e.g., checks syntax before committing).
