# Phase 59: Nucleus Daemon (Unified Runtime)
**Goal:** Implement the "Presence-Aware" Daemon as a parallel service.
**Strategy:** Non-Destructive Additive Build.

## 1. Stage 0: Safety & Atomicity (The Foundation)
*   [ ] **Locking:** Implement `BrainLock` as an **Abstract Base Class** (Support `FileLock` now, `RedisLock` later).
*   [ ] **Graph Safety (Zuckerberg):** Extend locking scope to `memory/`.
*   [ ] **Fault Tolerance:** Implement `check_stale_locks()` (Lease Management).
*   [ ] **Validation:** Update `commitment_ledger.py` and `memory_ops.py`.

## 2. Stage A: The Nucleus Kernel & Adaptive Policy
*   [ ] **Package:** Initialize `mcp_server_nucleus/daemon/`.
*   [ ] **Lifecycle (Gates):** Implement `DaemonManager` with strict cleanup.
*   [ ] **Event Loop (Musk):** Implement `AsyncFileWatcher` (Event-Driven).
*   [ ] **Toolbox Integration:** Import `ContextFactory`.
*   [ ] **The Circuit Breaker (Risk):** Implement `BudgetAuditor` middleware (Hard Token Limits).
*   [ ] **The App Store Hook:** Define `AgentManifest` schema.
*   [ ] **The Insight Hook:** Define `InsightExchange` data structures (for future trading).
*   [ ] **The Grid Hook:** Define `RemoteExecutionProtocol` interface (for Cloud offloading).
*   [ ] **The Hardware Hook:** Create `Dockerfile` for Headless Runtime (Debian-based Anti-Fragility).
*   [ ] **The Host Hook:** Implement `HostIntimacy` module (Permission-aware OS access).
*   [ ] **The Identity Hook:** Implement `IdentityKey` validation.
*   [ ] **The Training Hook:** Define `PrivateGraphTrainer` interface (LoRA fine-tuning spec).
*   [ ] **The Anti-Sherlock Hook:** Define `DataExporter` (JSON/SQLite Dump) & `DockerManifest`.
*   [ ] **Policy Engine:** Implement `DirectivesLoader` with `safety_level` config.
*   [ ] **The Compact:** Implement `MissionParameters` + `WatchdogTimer`.
*   [ ] **Feedback Loop:** Implement `ProposalOps` with **Pathway Export** schema.
*   [ ] **The Pulse:** Implement `AmbientTelemetry` (Write status to `~/.brain/pulse.json`).

## 3. Stage B: Preemptive Orchestrator & Strategic Handshake
*   [ ] **Execution:** Modify `SwarmsOrchestrator` to support `async` runs.
*   [ ] **Context Serialization:** Implement `save_thought_process()`.
*   [ ] **Preemption:** Implement `MonitorTask`.
*   [ ] **Predictive UX (Jobs):** Implement `ContextPreloader` (Generate `.vscode/restore_prev.json` to open relevant files).
*   [ ] **The Handshake (Venkatraman):** Implement `enter_negotiation_mode()` (Interactive Chat Briefing).

## 4. Stage C: Non-Destructive CLI
*   [ ] **Module Entry:** Implement `mcp_server_nucleus.daemon.__main__`.
*   [ ] **Verification:** `verify_kernel_handoff.py` (Script to simulate human-agent task contention).

## 4. Verification (The Proof)
*   [ ] **Simulated Test:** `python scripts/verify_daemon.py`.
    *   Mock "User Active" -> Daemon Sleeps.
    *   Mock "User Offline" -> Daemon Wakes.

## 5. Safety
*   [ ] **Isolation:** The Daemon will use a separate log file `daemon.log`.
*   [ ] **No Conflict:** It will respect the `state.json` locking mechanism (Atomic Claims) so it plays nice with any manual scripts running.
