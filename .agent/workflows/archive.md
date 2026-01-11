---
description: Golden Standard Archival Protocol (MDR_008 Compliance)
---

# Golden Standard Archival Protocol

Use this workflow to formally close a coding thread or create a "Save Point" for session resumption. This ensures that all findings, test results, and experimental context (including small "frills") are condensed and fed into the project's "Brain."

## 📋 The "Golden Prompt"
> **"Execute a Golden Standard Archival: verify active deployments, capture final metrics, fix task.md/walkthrough.md, save the session state, create a formal handoff to the synthesizer with key findings, cleanup resolved files, and trigger archival."**

## 🛠️ Step-by-Step Implementation

1. **Deployment & Metric Verification** (Pro Phase)
   - Verify any active Render/CloudRun builds are "Live".
   - Capture final metrics (e.g., `mcp_nucleus_brain_metrics` or `mcp_nucleus_brain_value_ratio`) to document the "Result" of the sprint.
   - Run `mcp_nucleus_brain_check_kill_switch` to ensure system health.

2. **State Serialization**
   - Call `mcp_nucleus_brain_save_session` to capture breadcrumbs, pending decisions, and next steps.

3. **Artifact Finalization**
   - Update `task.md` to mark all completions.
   - Update `walkthrough.md` with final verification results, embeddings of screenshots/recordings, and critical failures.

4. **Product-Aware Handoff Creation**
   - Create/Update `handoff_to_synthesizer.md` in the artifacts directory.
   - **Categorize Work:** Use headers like `# [NEW] GentleQuest Work` and `# [NEW] Nucleus Work`.
   - **Feature Linking:** Use `mcp_nucleus_brain_list_features` to find relevant features for the product and link work to the `feature_id`.
   - **Must Include:** 
     - Recent Commits & Feature Endpoints.
     - Testing Pass Rates (e.g., E2E findings).
     - **Specific Next Steps** and "Resumption Key" from the saved session.
     - **Rationale & Dead Ends**: Why certain paths were taken and which were ruled out.


5. **Environment Cleanup**
   - Run `mcp_nucleus_brain_archive_resolved` to move `.resolved.*` backups to `archive/`.
   - Run `mcp_nucleus_brain_archive_stale` to clean up commitments older than 30 days.

6. **Formal Archival Trigger**
   - Emit an `agent_archival_complete` event via `mcp_nucleus_brain_emit_event`.
   - Call `mcp_nucleus_brain_trigger_agent` targeting `synthesizer`.

## 🎯 Value
This protocol enforces **MDR_008/010 compliance**, prevents context rot, and ensures the **Synthesizer** has a high-fidelity snapshot to update the "Global Brain."
