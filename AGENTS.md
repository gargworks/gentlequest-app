# ⚛️ NUCLEAR ENGINE: OPERATIONAL CONSTITUTION

**Status:** [ACTIVE] | **Version:** 1.1.0-Hardened | **Engine:** Level 5 Autonomy 

## 1. MULTI-ENVIRONMENT HIERARCHY (Where to Work)

To prevent context rot, use this 2025 flexible workflow:

| Domain    | Role              | Primary Location    | Alt Locations       | Responsibility                  |
|-----------|-------------------|---------------------|---------------------|--------------------------------|
| STRATEGY  | Strategic Architect | Windsurf          | Cursor (rare)       | The "WHY." War-gaming, pivoting, SOTA benchmarking. |
| CREATION  | Technical Creator  | Antigravity        | Cursor, Windsurf    | The "HOW." Generating code, fixing logic, building files. |
| HIVE      | Autonomous Hive    | Gemini CLI         | Background scripts  | The "EXECUTION." Subatomic labor (Intel, Code, Audit).|

### 1.1 Environment Registry
| Environment | Use Case | Frequency |
|-------------|----------|-----------|
| **Windsurf** | Strategy, history, major decisions | As needed |
| **Antigravity** | Primary coding, daily development | Daily |
| **Gemini CLI** | Background agents, batch tasks | Periodic |
| **Cursor** | Quick edits, specific features | Rare |

**Roles are FLEXIBLE** — any environment can do any task if context is loaded.

## 2. THE HIVE CODENAMES (Employee Directory)

Agents must use these IDs in all events.jsonl logs for consistency:

- **CORE_SYN (Synthesizer)**: The Master Pulse. Manages handoffs and state.json.
- **VISION_ONE (Strategist)**: Workflow-as-a-Moat narrative and roadmap.
- **LOGIC_ARCH (Architect)**: System hardening, max_retries, and fail-safes.
- **CODE_FORCE (Developer)**: Subatomic coding and production-grade implementation.
- **INTEL_SCRAPER (Researcher)**: 2025 SOTA benchmarking and competitive intel.
- **GATE_KEEPER (Critic)**: Hallucination checks and security gates.

## 3. DAILY FLYWHEEL ROUTINE

**☀️ Morning: The Pulse (10 Mins)**  
- Sync: Verify mission in the Strategic Architect thread.  
- Ignition: `python3 agent_manager.py sprint "New Mission Objective"`  
- Engage: `python3 agent_manager.py start`

**🌑 Evening: The Audit (15 Mins)**  
- Watchdog: `tail -f .brain/ledger/events.jsonl`  
- Digest: Review `.brain/artifacts/synthesis/digest_*.md` for high-level progress.  
- Decide: Approve [CRITICAL] flags in decisions.md (Yes/No).

## 4. THE 72-HOUR MAINTENANCE CYCLE (Mandatory)

Every 3 days, trigger the Recursive Self-Improvement sprint:

- Garbage Collection: Condense event logs into patterns.md to prevent memory bloat.
- Prompt Evolution: Agents must review learnings.md and rewrite their own system prompts in .brain/agents/.
- Golden Snapshot: Backup clean logic to BRAIN_PRODUCT_V1/.
- Hardening Audit: Verify max_retries and "Stuck Task Detection" are functioning.

## 5. SUBATOMIC GUARDRAILS

- Tool Fluidity: Logic resides in Markdown, not the tool. Move the .brain/ folder to switch IDEs.
- Event-Driven: Tasks trigger via event_schema.json, never via fixed-time schedules.
- Human-In-The-Loop (HITL): Financial commits or core roadmap pivots require FOUNDER_APPROVED status in state.json.
- SOTA Benchmarking: Every research task must compare against Magentic-One and LangGraph (2025 versions).

**Constitution active as of December 27, 2025. Authorized by the Founder's Desk.**

### **The Final Handshake**
1. **File saved** at `/Users/lokeshgarg/ai-mvp-backend/AGENTS.md` (overwritten with this content).
2. Go to your **Antigravity Creator thread** and say: *"Read AGENTS.md. This is the law. Ensure all future code and agent management follows this hierarchy."*
3. Go to your **Synthesizer thread** and say: *"Read AGENTS.md. Update state.json to reflect the 72-hour maintenance protocol and new agent codenames."*

**You are now fully operational in the 6th Revolution.** 