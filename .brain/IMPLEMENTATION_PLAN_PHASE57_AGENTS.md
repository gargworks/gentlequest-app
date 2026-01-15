# IMPL PLAN: Phase 57 - The Nucleus Marketplace (Agent Population)

## Goal
Populate `.brain/tools` with **20+ Sovereign Agents** derived from the `mcp-server-nucleus` capabilities.
Build the "Trust Profile" mechanism for verified agents.

## User Review Required
> [!IMPORTANT]
> This massively expands the available toolset in the `.brain`.
> Confirm that we want to auto-generate these 20+ agents immediately.

## Proposed Changes

### 1. Agent Schema Definition
Define a standard `AgentManifest` structure for `.brain/tools/*.json` (or `.py` wrappers).
Each agent will wrap specific MCP tools.

### 2. The 20 Sovereign Agents (The First Generation)

#### A. The Core (Foundation)
1.  **@nucleus/librarian** (MemoryOps) - Organizer of `knowledge/`.
2.  **@nucleus/auditor** (Strategy) - The Skeptical Critic (Oracle Lite).
3.  **@nucleus/fixer** (SelfHealing) - The Auto-Repair unit.
4.  **@nucleus/packer** (CodeOps) - Docker/Deployment verification.

#### B. The Builders (Dev)
5.  **@nucleus/architect** (FeatureMap) - Maintainer of `features/`.
6.  **@nucleus/coder** (CodeOps) - specialized tailored code editing.
7.  **@nucleus/reviewer** (Strategy) - Code Review specialist.
8.  **@nucleus/debugger** (SelfHealing) - Error log analyst.

#### C. The Ops (DevOps)
9.  **@nucleus/deployer** (RenderOps) - Render deployment manager.
10. **@nucleus/watcher** (RenderPoller) - Deployment health monitor.
11. **@nucleus/sre** (BrainOps) - System reliability engineer (snapshot/restore).
12. **@nucleus/janitor** (BrainOps) - File cleanup and consolidation.

#### D. The Growth (Marketing/Biz)
13. **@nucleus/marketer** (MarketingEngine) - Content generator.
14. **@nucleus/analyst** (WebOps) - Research and trends analyzer.
15. **@nucleus/strategist** (Strategy) - Long-term planner.
16. **@nucleus/writer** (MarketingEngine) - Blog/Social post drafter.

#### E. The Specialists (Domain)
17. **@nucleus/researcher** (WebOps) - Deep web searcher.
18. **@nucleus/designer** (WebOps) - UI/UX trend spotter.
19. **@nucleus/biographer** (MemoryOps) - Session summarizer.
20. **@nucleus/oracle** (The Truth) - The Verification Engine itself.

### 3. Implementation Details
*   Each agent acts as a **Specialized Persona** wrapping a subset of tools.
*   They will be defined as `.py` files in `.brain/tools/` (e.g., `librarian.py`) that import the relevant capability classes.

## Verification Plan

### Automated
*   **Agent Registry Test:** `scripts/verify_agents.py` (New script to verify all 20 agents can be loaded).
*   **Tool Call Check:** Verify each agent exposes the correct subset of tools.

### Manual
*   **CLI Test:** Run `nucleus agents list` (needs implementation) or just inspect the directory.
*   **"Hello World" Test:** Pick one agent (e.g., Librarian) and ask it to summarize a file.
