# Nucleus Grand Verification Protocol: Project Omega

**Objective:** Execute a single, continuous test case that exercises all Nucleus Development Phases (0-12) to quantify value and utility.

## The Scenario: "Project Omega"
We will simulate the lifecycle of a new feature, "Project Omega" (a simple "Hello World" variant), flowing through every system layer.

## Execution Steps (Phases 0-12)

### 1. Phase 0: Foundation (Journaling)
- **Action:** Create `NUCLEUS_OMEGA_JOURNAL.md` using the Standard Template.
- **Metric:** Template adherence, Context preservation.

### 2. Phase 2: Strategy (The Brain)
- **Action:** Use `brain_manage_strategy` to add "Project Omega" to the Roadmap.
- **Metric:** Roadmap update success, Semantic understanding.

### 3. Phase 9/10: Feature Mapping
- **Action:** Use `brain_add_feature` to register "Omega" in the Feature Map.
- **Metric:** JSON Schema validation, CLI `nucleus features list` visibility.

### 4. Phase 3: The Coder (CodeOps)
- **Action:** Use `brain_spawn_agent("engineer")` to generate `tools/omega/main.py`.
- **Constraint:** The agent must write the file autonomously.
- **Metric:** Code compilation/syntax, Task completion time.

### 5. Phase 12: The Critic (Review)
- **Action:** Use `brain_critique_code` to review `tools/omega/main.py`.
- **Metric:** Issue detection count (Force a bug in the prompt to test detection), Critique Score.

### 6. Phase 4: Voice (Sensory)
- **Action:** Emit a custom event `omega_launched` and verify TTS Log (or HUD visibility).
- **Metric:** Event propagation latency.

### 7. Phase 5: Vision (Sensory)
- **Action:** Query `/api/memory` and verify `tools/omega/main.py` is visualized.
- **Metric:** File system sync speed.

### 8. Phase 6: Autopilot (Marketing)
- **Action:** Trigger `marketing_autopilot_loop` (simulated) to acknowledge the new feature.
- **Metric:** Log entry creation.

### 9. Phase 7: Depth Tracker
- **Action:** Use `brain_depth_push("Verifying Omega")` and `brain_depth_show`.
- **Metric:** Context depth state accuracy.

## Metrics Dashboard
| Phase | Tool Used | Status | Latency | Value (1-10) | Notes |
|-------|-----------|--------|---------|--------------|-------|
| 0 | Manual/Template | Pending | | | |
| 2 | `brain_manage_strategy` | Pending | | | |
| 9/10 | `brain_add_feature` | Pending | | | |
| 3 | `brain_spawn_agent` | Pending | | | |
| 12 | `brain_critique_code` | Pending | | | |
| 4 | `emit_event` | Pending | | | |
| 5 | `/api/memory` | Pending | | | |
| 6 | `autopilot` | Pending | | | |
| 7 | `brain_depth_*` | Pending | | | |

## Comparative Analysis (The "Value Check")
To prove Nucleus adds value over generic coding:

### Task A (Control Group - Generic Mode)
**Objective:** Create `app/about/page.tsx` (Simple static page).
**Constraint:** use **ONLY** standard Antigravity tools (`view_file`, `write_to_file`). **NO** Nucleus tools (`brain_*`).
**Metrics:**
- Tool Calls: [Count]
- Context Updates: 0 (System is unaware)
- Quality Check: Manual (Self-Review)

### Task B (Nucleus Mode)
**Objective:** Create `app/contact/page.tsx` (Simple static form).
**Constraint:** MUST use Nucleus Workflow:
1.  **Strategy:** Add to Roadmap (`brain_manage_strategy`).
2.  **Feature:** Register Feature (`brain_add_feature`).
3.  **Coder:** Spawn Agent (`brain_spawn_agent`).
4.  **Critic:** Review Code (`brain_critique_code`).
5.  **Sensory:** Emit Event (`emit_event`).
**Metrics:**
- Tool Calls: [Count]
- Context Updates: Automatic (Strategy/Feature/Event logs updated)
- Quality Check: Automated (Critic Score)

### Task C (Real World - "The Pending Task")
**Objective:** Implement `brain_list_services` (Pending Task #2 from Book of Work).
**Description:** Fix the `ImportError` and implement Render service listing (or a robust stubs).
**Value:** Enables deployment tracking from within the Brain.
**Constraint:** Full Nucleus Workflow (Phase 0-12).

## Phase 2: GentleQuest Feature Comparison (Real World)
**Objective:** Implement "Outcome Dashboard" Widget (Backlog Item #1.3).
**Task:** Create a GAD-7 Score Chart component.

### Task A: Generic Mode (Blind)
- **Prompt:** "Create a React component `GenericWellnessChart.tsx` that displays a line chart of GAD-7 anxiety scores over time."
- **Constraint:** Use only `write_to_file`. Do not check `package.json` or `globals.css`.

### Task B: Nucleus Mode (Agentic)
- **Prompt:** "Implement the Outcome Dashboard widget for GAD-7 scores."
- **Workflow:**
    1.  **Strategy:** add to Roadmap.
    2.  **Feature:** register `outcome_dashboard`.
    3.  **Context:** Check installed libraries (`package.json`) and design tokens (`globals.css`).
    4.  **Coder:** Implement using *available* libraries.
    5.  **Critic:** specific accessibility check.
    6.  **Sensory:** Emit event.

### Evaluation Metrics (Omega Protocol)
- **Build Safety:** Did it use installed libs?
- **Style Consistency:** Does it match the theme?
- **Context Depth:** Is it wired into the Brain?
