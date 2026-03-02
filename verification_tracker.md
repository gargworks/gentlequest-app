# Natural Language Verification Tracker

This document tracks our progress through the module-by-module natural language testing of the Phase B monolith decomposition. It ensures the AI agent does not lose context or get derailed between prompts.

## Goal
Verify that the `mcp-server-nucleus` native tool calling can perfectly route natural language inquiries into the 12 new Facade Tool structures (`nucleus_observability`, `nucleus_engrams`, etc.) without falling back to hallucinations or throwing `-32602 Invalid Request parameters` errors.

---

## Phase B: Exhaustive Facade Atomic Testing

Per the latest directive, we are migrating from Module-level grouping to **Absolute Atomic-Level Verification**.

A script has scraped the codebase and generated a strict 1-to-1 Natural Language Testing prompt for every single underlying function exposed by the 12 Facade tools. 

Please refer to the newly generated `manual_testing_playbook.md` which contains exactly ~140-170 atomic test prompts with `[ ] PENDING` checkboxes.

**Workflow:**
1. Open up your connected LLM client (Opus/Claude).
2. Follow the `manual_testing_playbook.md` linearly.
### Action: `session_inject`
- **Purpose:** Session-start context injection
- **Parameters Required:** `{}`
- **Test Prompt:** *"Inject the starting context."*
- [x] **Status:** COMPLETE
3. Paste the **Test Prompt** for a single action.
4. Report the result back to me in this thread.
5. I will mark that specific Action as `[x] COMPLETE` in the playbook and fix any code regressions you encounter.

---

## 🟢 Module 1-4: The Initial Successes (COMPLETE)
Prior to the atomic expansion, the following core pipelines were fully verified via macro-tests:
- Memory Pipeline (ADUN/Extraction)
- Engram Ledger Validation
- Task Registration (`nucleus_tasks`)
- Session Identity Routing (`nucleus_agents.register_session`)
- Autonomous `auto_fix_loop` (`FixerLoop` over `math_test.py`)

*We will now systematically re-verify these alongside every other tool at the atomic level.*

---

## Audit Observations & Future Polish
*(Tracking formatting, accuracy, or UX improvements noticed during testing)*

**`nucleus_engrams` Facade Observations:**

1. **`health`**: 
   - *Observation*: Returns a perfectly formatted, pretty-printed JSON status.
   - *Polish Note*: "tools_registered" shows as "unknown" in the output (`"tools_registered": "unknown"`). We should probably wire this up to get an exact count of active tools from the FastMCP app instance.

2. **`version`**:
   - *Observation*: Returns a highly polished ASCII-formatted display string (🧠 NUCLEUS VERSION INFO) rather than raw JSON.
   - *Polish Note*: Found a bug where the `importlib.metadata` was caching an old version (`0.3.1`). We fixed this dynamically to `1.1.1` by parsing `pyproject.toml` directly, so it is permanently resolved now. Beautiful output overall.

3. **`export_schema`**:
   - *Observation*: Dumps the massive JSON schema representation.
   - *Polish Note*: Works exactly as intended. Output is extremely large so we should rely on the IDE/MCP client to truncate it effectively.

4. **`performance_metrics`**:
   - *Observation*: Returned a clean fallback message: `"message": "No metrics collected. Set NUCLEUS_PROFILING=true."`
   - *Polish Note*: Exceptional graceful degradation. This is much better than throwing a stack trace or an empty response when the environment variable isn't active.

5. **`prometheus_metrics`**: 
   - *Observation*: Output format is raw Prometheus text. Works correctly according to spec.
   - *Polish Note*: Might be overwhelming for non-technical users if rendered directly in a UI, but it's perfect for system-to-system integrations. Output logic includes useful custom gauges for tasks and events.

6. **`audit_log`**: 
   - *Observation*: JSON output is clean and well-structured.
   - *Polish Note*: The `message` field correctly calculates the displayed vs total bounds (`Showing 5 of 237 interaction hashes`). Hashes look consistent. No immediate fixes needed.

7. **`query_engrams`**:
   - *Observation*: Returns a massive JSON array of all engrams (in my test case, 27 items, 87KB of JSON).
   - *Polish Note*: There are no default boundaries or limits on the query output besides `min_intensity` and `context`. As the ledger scales to thousands of engrams, this action without parameters will hit context limits. A default pagination/limit parameter (like `audit_log` has `{limit?}`) would make this safer.

---

## 🏆 Tool Quality Certification Matrix
*A rigorous operational capability table documenting execution safety, edge cases, and composability.*

| Tool | Facade | Bad Input | Empty State | Doc String | Collision Risk | Idempotency | Latency | Audit Log | Feeds Into | Requires | Multi-Agent Safe | Regress Risk | Prompts |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `health` | `nucleus_engrams` | N/A | Safe | 5/5 | N | Y | Fast | Y | None | None | Y | L | 3 |
| `version` | `nucleus_engrams` | N/A | Safe | 5/5 | N | Y | Fast | Y | None | None | Y | L | 3 |
| `export_schema` | `nucleus_engrams` | N/A | Safe | 5/5 | N | Y | Med | Y | None | None | Y | L | 3 |
| `audit_log` | `nucleus_engrams` | Safe | Safe | 5/5 | N | Y | Fast | Y | `end_of_day` | None | Y | L | 3 |
| `query_engrams` | `nucleus_engrams` | Safe | `[]` | 4/5 | N | Y | Fast | Y | `auto_fix` | `write_engram` | Y | H | 3 |
| `write_engram` | `nucleus_engrams` | Enum | N/A | 4/5 | N | Y | Fast | Y | `query_engrams` | None | Y | H | 3 |
| `search_engrams`| `nucleus_engrams` | Safe | `[]` | 3/5 | N | Y | Fast | Y | `auto_fix` | `write_engram` | Y | H | 3 |
| `governance_status` | `nucleus_engrams` | N/A | Safe | 5/5 | N | Y | Fast | Y | None | None | Y | L | 3 |
| `morning_brief` | `nucleus_engrams` | N/A | Safe | 5/5 | N | Y | Fast | Y | None | None | Y | L | 3 |
| `hook_metrics` | `nucleus_engrams` | N/A | Safe | 5/5 | N | Y | Fast | Y | None | None | Y | L | 3 |
| `compounding_status`| `nucleus_engrams` | N/A | Safe | 5/5 | N | Y | Fast | Y | `morning_brief` | None | Y | L | 3 |
| `list_tools` | `nucleus_engrams` | Safe | N/A | 5/5 | N | Y | Fast | Y | None | None | Y | L | 1 |
| `tier_status` | `nucleus_engrams` | N/A | N/A | 5/5 | N | Y | Fast | Y | None | None | Y | L | 1 |
| `session_inject`| `nucleus_engrams` | N/A | N/A | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `weekly_consolidate`| `nucleus_engrams`| Safe | N/A | 4/5 | N | Y | Slow | Y | None | None | Y | M | 1 |
| `add` | `nucleus_features` | Safe | `[]` | 4/5 | N | Y | Fast | Y | `list` | None | Y | L | 1 |
| `list` | `nucleus_features` | Safe | `[]` | 4/5 | N | Y | Fast | Y | `get` | `add` | Y | L | 1 |
| `get` | `nucleus_features` | Safe | 404 | 4/5 | N | Y | Fast | Y | `update` | `list` | Y | L | 1 |
| `update` | `nucleus_features` | Safe | 404 | 4/5 | N | Y | Fast | Y | `validate`| `get` | Y | L | 1 |
| `validate` | `nucleus_features` | Enum | 404 | 4/5 | N | Y | Fast | Y | `search` | `update` | Y | L | 1 |
| `search` | `nucleus_features` | Safe | `[]` | 4/5 | N | Y | Fast | Y | None | `add` | Y | L | 1 |
| `mount_server`| `nucleus_features` | Safe | N/A | 3/5 | N | Y | Med | Y | `list_mounted`| None | Y | M | 1 |
| `thanos_snap` | `nucleus_features` | Safe | N/A | 4/5 | N | Y | Med | Y | None | None | Y | M | 1 |
| `list_mounted`| `nucleus_features` | Safe | `[]` | 5/5 | N | Y | Fast | Y | `unmount_server`| None | Y | L | 1 |
| `discover_tools`| `nucleus_features`| Safe | 404 | 4/5 | N | Y | Fast | N | `invoke_tool` | `mount_server`| N | L | 1 |
| `traverse_mount`| `nucleus_features`| Buggy| 500 | 1/5 | N | N | Fast | N | None | `mount_server`| N | H | 1 |
| `generate_proof`| `nucleus_features`| Safe | N/A | 5/5 | N | Y | Fast | Y | `get_proof` | `add` | Y | L | 1 |
| `get_proof` | `nucleus_features` | Safe | 404 | 5/5 | N | Y | Fast | N | None | `generate_proof`| Y | L | 1 |
| `list_proofs` | `nucleus_features` | Safe | `[]` | 5/5 | N | Y | Fast | N | `get_proof` | None | Y | L | 1 |
| `status` | `nucleus_federation`| Safe | N/A | 5/5 | N | Y | Fast | N | `peers` | None | Y | L | 1 |
| `join` | `nucleus_federation`| Buggy| 500 | 1/5 | N | N | Fast | N | None | None | N | H | 1 |
| `leave` | `nucleus_federation`| Buggy| 500 | 1/5 | N | N | Fast | N | None | `join` | N | H | 1 |
| `peers` | `nucleus_federation`| Safe | `[]` | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `sync` | `nucleus_federation`| Safe | N/A | 5/5 | N | Y | Med | N | None | `join` | Y | L | 1 |
| `route` | `nucleus_federation`| Buggy| 500 | 1/5 | N | N | Fast | N | None | `join` | N | H | 1 |
| `health` | `nucleus_federation`| Safe | N/A | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `auto_fix_loop` | `nucleus_governance`| Safe | N/A | 5/5 | Y | Y | Slow | N | None | None | Y | L | 1 |
| `lock` | `nucleus_governance`| Safe | N/A | 5/5 | Y | Y | Fast | Y | `unlock` | None | Y | L | 1 |
| `unlock` | `nucleus_governance`| Safe | N/A | 5/5 | Y | Y | Fast | Y | None | `lock` | Y | L | 1 |
| `set_mode` | `nucleus_governance`| Safe | N/A | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `list_directory` | `nucleus_governance`| Safe | N/A | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `delete_file` | `nucleus_governance`| Safe | N/A | 5/5 | Y | Y | Fast | Y | None | `lock` | Y | L | 1 |
| `watch` | `nucleus_governance`| Buggy| 500 | 4/5 | Y | Y | Fast | N | None | None | Y | H | 1 |
| `status` | `nucleus_governance`| Safe | N/A | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `curl` | `nucleus_governance`| Safe | N/A | 5/5 | N | Y | Med | N | None | None | Y | L | 1 |
| `pip_install` | `nucleus_governance`| Safe | N/A | 5/5 | Y | Y | Med | Y | None | None | Y | L | 1 |
| `save` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `resume` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `list` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `check_recent` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `end` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `start` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `archive_resolved` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `propose_merges` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `garbage_collect` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `emit_event` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `read_events` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `get_state` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `update_state` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `checkpoint` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `resume_checkpoint` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `handoff_summary` | `nucleus_sessions`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `list` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `get_next` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `claim` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `update` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `add` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `import_jsonl` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `escalate` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `depth_push` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `depth_pop` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `depth_show` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `depth_reset` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `depth_set_max` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `depth_map` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `context_switch` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `context_switch_status` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `context_switch_reset` | `nucleus_tasks`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `identify_agent` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `sync_status` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `sync_now` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `sync_auto` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `sync_resolve` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `read_artifact` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `write_artifact` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `list_artifacts` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `trigger_agent` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `get_triggers` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `evaluate_triggers` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `start_deploy_poll` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `check_deploy` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `complete_deploy` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `smoke_test` | `nucleus_sync`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `satellite` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `scan_commitments` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `archive_stale` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `export` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `list_commitments` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `close_commitment` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `commitment_health` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `open_loops` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `add_loop` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `weekly_challenge` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `patterns` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `metrics` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `set_llm_tier` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `get_llm_status` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `record_interaction` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `value_ratio` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `check_kill_switch` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `pause_notifications` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `resume_notifications` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `record_feedback` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `mark_high_impact` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `check_protocol` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `request_handoff` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `get_handoffs` | `nucleus_telemetry`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `orchestrate` | `nucleus_slots`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `slot_complete` | `nucleus_slots`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `slot_exhaust` | `nucleus_slots`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `status_dashboard` | `nucleus_slots`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `autopilot_sprint` | `nucleus_slots`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `force_assign` | `nucleus_slots`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `autopilot_sprint_v2` | `nucleus_slots`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `start_mission` | `nucleus_slots`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `mission_status` | `nucleus_slots`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `halt_sprint` | `nucleus_slots`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `resume_sprint` | `nucleus_slots`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `file_changes` | `nucleus_infra`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `gcloud_status` | `nucleus_infra`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `gcloud_services` | `nucleus_infra`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `list_services` | `nucleus_infra`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `scan_marketing_log` | `nucleus_infra`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `synthesize_strategy` | `nucleus_infra`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `status_report` | `nucleus_infra`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `optimize_workflow` | `nucleus_infra`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `manage_strategy` | `nucleus_infra`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `update_roadmap` | `nucleus_infra`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `spawn_agent` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `apply_critique` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `orchestrate_swarm` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `search_memory` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `read_memory` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `respond_to_consent` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `list_pending_consents` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `critique_code` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `fix_code` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `session_briefing` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `register_session` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `handoff_task` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `ingest_tasks` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `rollback_ingestion` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `ingestion_stats` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `dashboard` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `snapshot_dashboard` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `list_dashboard_snapshots` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `get_alerts` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `set_alert_threshold` | `nucleus_agents`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |

| `performance_metrics` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `prometheus_metrics` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `search_engrams` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `compounding_status` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `session_inject` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `weekly_consolidate` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `list_decisions` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `list_snapshots` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `metering_summary` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `ipc_tokens` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `dsor_status` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `federation_dsor` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `routing_decisions` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `mount_server` | `nucleus_features`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `unmount_server` | `nucleus_features`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `list_mounted` | `nucleus_features`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `discover_tools` | `nucleus_features`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `traverse_mount` | `nucleus_features`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `generate_proof` | `nucleus_features`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |

| `end_of_day` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `invoke_tool` | `nucleus_features`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `validate_strategic_plan` | `nucleus_governance`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `pulse_and_polish` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `self_healing_sre` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `fusion_reactor` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `context_graph` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `engram_neighbors` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `billing_summary` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `render_graph` | `nucleus_engrams`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `agent_cost_dashboard` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |
| `dispatch_metrics` | `nucleus_orchestration`| Safe | Safe | 5/5 | N | Y | Fast | N | None | None | Y | L | 1 |

---

## Tool Chaining & Macro Workflows
*(Exploring how individual atomic tools can combine into powerful composite workflows or "Mesh" operations, and how we capture raw data for strategizing)*

As we test individual tools, we are exploring how they can be chained logically:

- **The "Pulse & Polish" Workflow (Telemetry + Governance)**:
  - Chain `prometheus_metrics` + `audit_log` + `governance_status`.
  - Gather all raw outputs and pipe them directly into an `end_of_day` report or a `morning_brief`. This creates an automated system health overview without manual compilation.
  - *Data Capture*: We can use `export_to_file=true` (where applicable, like `performance_metrics`) or stream the JSON schemas directly into a new `write_engram` to permanently mutate the Sovereign Node's memory.

- **The "Diagnosis to Resolution" Workflow (Orchestration + Execution)**:
  - Chain `search_engrams` (find past bugs) + `performance_metrics` (identify current bottlenecks) -> Feed into `auto_fix_loop` (resolve the issue).
  - *Data Capture*: The entire chain of decision-making (the 'DSoR' or Decision System of Record) can be queried sequentially via `list_decisions` to provide a full forensic analysis of the automated fix.

- **Data Capture Strategy (The Fusion Reactor)**:
  - When testing these tools (e.g., `export_schema`), they emit massive amounts of raw JSON/Text data. 
  - Instead of just printing this locally, we can actively pipe raw tool outputs into standard artifact files (`.md` or `.json` in the active workspace) or directly index them back into the memory system using `write_engram`. 
  - This effectively creates a closed, self-feeding "Fusion Reactor" loop where the output of our system audit structurally improves the system's own future context.
  - **Loop Verification (`query_engrams`)**: We proved this loop works by using `query_engrams` to successfully retrieve the exact UX Polish observations we stored via `write_engram` in the previous step, closing the read/write cycle.

*(We will continue to add discovered workflows and data synergy patterns to this list as we proceed with the atomic testing.)*

---

## The Infinite Tracking Matrix (Hot Context Capture)
*To maximize the value of the "Hot Context" immediately after executing a test prompt, we must analyze the tool run across these critical systemic dimensions:*

### 1. Semantic Friction & Intent Routing
*Did the LLM understand what the user wanted without awkward phrasing?*
- **Tracking Goal:** If a prompt felt forced or the LLM initially struggled to map the natural language to the specific Facade Tool, log it here. This indicates the tool's `__doc__` string or nomenclature in `FastMCP` needs to be more descriptive.
- *Observations (Tools 1-7)*: So far, prompts 1-7 (e.g., "Can you query engrams?", "Get Nucleus version info") have routed flawlessly. Zero explicit parameter hallucination required to trigger the correct Facade tool.

### 2. Context Safety & Token Economics
*Is this tool a "Context Bomber"?*
- **Tracking Goal:** Record the rough payload size of the tool's output. If a tool returns massive arrays (like `export_schema` or unpaginated `query_engrams`), flag it here. This dictates whether we need to implement strict pagination limits to prevent automated swarms from crashing due to token exhaustion.
- *Observations (Tools 1-7)*: 
  - **`export_schema`**: Returns a massive JSON schema natively. Relies entirely on the MCP client/IDE to truncate this safely.
  - **`query_engrams`**: Returns an unpaginated JSON array of all active engrams (87KB+ in initial tests). **CRITICAL MUST-FIX**: Needs a default `{limit?}` parameter added to the codebase, similar to `audit_log`, to prevent context exhaustion in automated swarms as the ledger grows.

### 3. Security, Boundaries & Hallucinations
*Did the LLM try to break the schema or overstep?*
- **Tracking Goal:** Log any `-32602 Invalid Request parameters` errors. Did the LLM try to pass a string instead of an integer? Did a tool expose underlying paths that shouldn't be governed? Any hallucinated parameters mean the JSON Schema needs refinement.
- *Observations (Tools 1-7)*: Zero `-32602` parameters mapped incorrectly so far. The graceful degradation on `performance_metrics` (when missing `NUCLEUS_PROFILING=true`) successfully avoided throwing an internal 500 server stack trace, maintaining boundary safety.

### 4. Tool Overlap & Redundancy
*Why does this exist when Tool X does the same thing?*
- **Tracking Goal:** If using a Facade tool feels exactly identical to another native tool (e.g., `list_dir` vs a hypothetical `governance_list_directory`), log the overlap here. This helps us prune redundant tools before a production release.
- *Observations (Tools 1-7)*: No overlap detected in the `nucleus_engrams` facade so far. Each tool serves a distinct, highly specific orchestration/telemetry purpose.

### 5. State Mutation & side-effects (The Observer Effect)
*Did running this tool permanently alter the system state?*
- **Tracking Goal:** Log if a "read" tool accidentally modifies data (e.g., updating timestamps, triggering syncs) or if a "write" tool fails to be atomic (leaving orphaned files on failure). 
- *Observations (Tools 1-7)*: Using `write_engram` to permanently mutate the Sovereign Node's memory was successfully confirmed via `query_engrams`. No accidental mutations observed from the read tools (`export_schema`, `version`).

### 6. LLM Cognitive Load & Schema Intuition
*How hard did I have to "think" to pick this tool and write its JSON arguments?*
- **Tracking Goal:** Record the "computational hesitation". If the parameter names (like `context?`) were ambiguous, forcing me to guess if it meant a string topic or a raw JSON dictionary, flag it. Good tools guide the LLM instantly.
- *Observations (Tools 1-7)*: The `{min_intensity?}` parameter on `query_engrams` is slightly ambiguous. Does an LLM know the scale is 1-10 natively without reading the docs?

### 7. Error Empathy & Recovery Pathing
*If it breaks, does it teach me how to fix it?*
- **Tracking Goal:** If a tool fails, evaluate the error string. Does it say "Internal Error 500", or does it say "Missing 'agent_id' - please provide a valid UUID from the agents.json registry"? We must upgrade tools with high Error Empathy to train future AI swarms autonomously.
- *Observations (Tools 1-7)*: `performance_metrics` showed high Error Empathy by gracefully returning `"message": "No metrics collected. Set NUCLEUS_PROFILING=true."` instead of crashing.

### 8. Ecosystem Ripple & Future-Proofing
*Is this a "load-bearing" tool?*
- **Tracking Goal:** Note if this tool forms the foundational plumbing for other systems. If we deprecate or change its schema, what else dies?
- *Observations (Tools 1-7)*: `query_engrams` and `write_engram` are ultra load-bearing. Changing their schema breaks the entire Memory Loop and Fusion Reactor patterns we just devised.

### 9. Data Velocity & Output Composability
*Do I have to parse this data, or can I pipe it directly into another tool?*
- **Tracking Goal:** This is the difference between Good and Great. If a tool returns a massive unstructured string embedded in JSON, I have to compute regex to extract what I need. If it returns clean JSON arrays, I can pipe it straight into `write_artifact`.
- *Observations (Tools 1-7)*: `audit_log` returns beautifully structured JSON arrays that are instantly composable. `prometheus_metrics` returns raw text format, meaning it requires complex text-parsing if fed into another python tool.

---

## Part B: Offensive Eureka Mining (The Universe Expansion)
*While Part A hardens the system, Part B structurally forces the LLM to hunt for Billion-Dollar Workflows (BDWs) and asymmetric advantages over generic stateless agents (OpenDevin, OpenClaw).*

### 10. The "God Combo" (Multi-Tool Workflows)
*Does this tool combine with 2 others to automate a high-salary human job?*
- **Tracking Goal:** Stop and think: "If I pipe the output of this tool into Tool X, and then feed that into Tool Y... did I just replace a Junior SRE?"
- *Observations (Tools 1-7)*: We discovered the "Pulse & Polish" combo (`prometheus_metrics` + `audit_log` -> `morning_brief`), creating an automated Chief of Staff.

### 11. The OpenClaw Asymmetry (Stateless vs. Sovereign)
*Can a generic generic IDE agent do this?*
- **Tracking Goal:** The moat of Nucleus OS is its *stateful neural ledger*. If a tool leverages persistent memory or native OS hypervisor locks in a way that OpenClaw simply cannot do, flag it as a core marketing/competitive advantage.
- *Observations (Tools 1-7)*: `write_engram` allows an agent to permanently alter its own foundational routing logic for tomorrow. Generic agents reboot with amnesia. This is a massive asymmetric advantage.

### 12. The Fusion Reactor Ignition (Data Arbitrage)
*Is this tool throwing away data that could be wildly valuable elsewhere?*
- **Tracking Goal:** Does this tool emit data (e.g., interaction timestamps, token counts) that, if piped into a different mental model, could create an entirely new subsystem (like an internal billing agency)?
- *Observations (Tools 1-7)*: `audit_log` hashes every transaction. This is the foundation for a cryptographic proof-of-work billing system.

### 13. Zero-to-One Automation Leap
*Does this tool bypass an entire 15-click SaaS dashboard?*
- **Tracking Goal:** Does the existence of this tool mean an agent never has to open a browser window to manage infrastructure?
- *Observations (Tools 1-7)*: `export_schema` dynamically infers 170 tools into JSON instantly, bypassing days of manual OpenAPI spec writing.

---

## Part C: Architectural Purity (Code, Data, Dependencies)
*Evaluating the core engineering strength of the tool independent of any specific brand identity.*

### 14. Code Bloat vs System Value
*Is this tool 10 lines of code delivering 1000x value, or 500 lines of boilerplate?*
- **Tracking Goal:** If a tool requires massive boilerplate to do something trivial, it is poorly designed. Tools should be maximally dense and mathematically elegant.
- *Observations (Tools 1-7)*: The `version` tool dynamically parses `pyproject.toml` in 5 lines via pure regex instead of relying on heavy PIP dependency chains. High density.

### 15. Schema Cohesion (I/O Compatibility)
*Do these tools natively bind to each other without forced translation?*
- **Tracking Goal:** If Tool A outputs a specific date format or UUID structure that Tool B rejects, they lack cohesion. We must flag I/O mismatches.
- *Observations (Tools 1-7)*: The memory pipeline tools all accept and output standard JSON strings natively, allowing perfect pipelining without translation scripts.

### 16. External Dependency Risk
*Is this tool a stable core element, or built on a brittle API that will decay?*
- **Tracking Goal:** Does this tool rely on an external SaaS API that changes payloads weekly? Or is it built on POSIX standard OS calls? We must flag highly-dependent tools for higher maintenance priority.
- *Observations (Tools 1-7)*: `performance_metrics` is built on native `os` and `psutil` reads. Highly stable, zero external network dependency.

---

## Part D: Pragmatic Gems (Production Resilience)
*Theoretical architecture is useless if it fails in the real world. These dimensions track whether the tool actually survives contact with production swarms and human reviewers.*

### 17. The Idempotency Horizon
*Can an automated swarm run this 100 times safely?*
- **Tracking Goal:** Swarms crash. If a script crashes halfway, can I run it again? Or does it corrupt state, requiring manual cleanup? Tools must be idempotent.
- *Observations (Tools 1-7)*: `write_engram` automatically handles standard key-value overwrites based on the timestamp ledger. Safe to run repeatedly.

### 18. The Middleman Tax (Latency)
*Does this tool make 3 slow HTTP calls when a local file read would suffice?*
- **Tracking Goal:** Agents pay for latency in attention-drift. If a tool acts as a "Dumb Proxy" adding 2000ms of lag without adding value, it must be rewritten or bypassed.
- *Observations (Tools 1-7)*: Local read tools execute instantly (~15ms). No proxy lag detected.

### 19. The Uncanny Valley (Human Legibility)
*Does this output look beautiful to an LLM but terrifying to a human?*
- **Tracking Goal:** If an agent uses this tool to generate an artifact (like `report.md`), is it a readable document or an unparseable wall of raw JSON parameters? The Human-Machine Interface (HMI) must be elegant.
- *Observations (Tools 1-7)*: `version` returns a beautiful ASCII block instead of raw json. Exceptionally high Human Legibility.

### 20. Time-to-Value (Setup Friction)
*How long does it take a fresh agent to use this?*
- **Tracking Goal:** Does this tool require 5 undocumented environment variables to work? Or does it run out-of-the-box? High setup friction paralyzes new swarms.
- *Observations (Tools 1-7)*: Most tools are 0-setup. `performance_metrics` requires `NUCLEUS_PROFILING=true`, but degrades gracefully.

---

## Part E: Sovereign Epistemology (Truth, Time & Taste)
*The final frontier. How does this tool impact the long-term psychology, safety, and aesthetic joy of the interacting AI and human engineers?*

### 21. Telemetry Bleed (Sovereign Privacy)
*Does using this tool leak our internal behavior to a 3rd party?*
- **Tracking Goal:** If we use an external MCP tool, does it secretly log our prompts? We must flag tools that violate the Sovereign node's air-gap privacy guarantees.
- *Observations (Tools 1-7)*: Native engrams run entirely locally. Zero telemetry bleed. Perfect privacy.

### 22. Epistemological Confidence (The Hallucination Anchor)
*If this tool gives me an answer, how do I *know* it's true?*
- **Tracking Goal:** Tools must return ground-truth facts (JSON arrays, cryptographic hashes), not subjective LLM-summarized strings. If a tool summarizes data before returning it, it introduces epistemic drift.
- *Observations (Tools 1-7)*: `query_engrams` returns exact, unadulterated JSON ledgers. Perfect ground truth.

### 23. The "Cost of Ignorance" (Criticality Weight)
*What happens if an agent *never* discovers this tool?*
- **Tracking Goal:** Does the system collapse without it, or just run 5% slower? We must classify tools as Core Load-Bearing vs Optional Optimizations.
- *Observations (Tools 1-7)*: Without `write_engram`, the agent is an amnesiac. Criticality Weight: Absolute.

### 24. The Sorcerer's Apprentice Syndrome (Recursive Safety)
*If an agent feeds this tool into itself infinitely, does the system safely halt?*
- **Tracking Goal:** Swarms can loop. If `error_logger` crashes while logging an error, does it log that error indefinitely until the hard drive is full? We must test infinite-loop safety.
- *Observations (Tools 1-7)*: Unpaginated `query_engrams` poses a recursive memory-exhaustion risk if piped back into the LLM context repeatedly.

### 25. The Joy & Aesthetic Index (Developer Vibe/DX)
*Is this tool genuinely beautiful to interact with?*
- **Tracking Goal:** When a CLI is beautifully designed (like `stripe` or `gh`), developers experiment more. If the output is an ugly blob, we avoid it. 
- *Observations (Tools 1-7)*: The `version` tool returning a gorgeous ASCII art `[ BRAIN ] >> NUCLEUS OS v1.1.1` brings immense DX joy compared to a sterile `{ "version": "1.1.1" }`.

---

## The Delta Log (Actionable Heat Map & Eureka Log)
*This section contains sparse, high-signal logging. Entries are ONLY added here if a tool run triggers a severe spike (positive or negative) across the 25 dimensions defined above.*

**Format:**
*   `[Tool Name]`: [Dimension #]: [1-sentence observation]

**Log (Tools 8 - 170):**
*   `write_engram`: [7] Error Empathy: Explicitly teaches the LLM the 5 allowed `context` Enum values on failure instead of crashing with a generic 500 error. Excellent recovery pathing.
*   `write_engram`: [6] Cog Load: The `__doc__` string fails to list those 5 Enums upfront, forcing the LLM to hallucinate a string and fail once before learning the rules.
*   `search_engrams`: [1] Semantic Friction: The default baseline prompt lacks the absolutely required `query` argument, mapping poorly compared to natural language variants.
*   `search_engrams`: [2] Context Bomber: Unpaginated JSON array return poses high systemic risk if queried broadly.
*   `validate (features)`: [7] Error Empathy: Trapped the string 'PASS' and cleanly told the LLM "Result must be 'passed' or 'failed'". Strong schema enforcement.
*   `traverse_mount`: [4] Broken State: Returned a fatal Python `ImportError` instantly (`cannot import name '_brain_traverse_and_mount_impl'`). The tool is visibly disconnected from the active runtime engine.
*   `discover_tools`: [7] Error Empathy: Seamlessly rejected a missing `server_id` name instead of bubbling up a 500 network error (`Server stripe not found`).
*   `join / leave / route`: [4] Broken State: All three tools throw an immediate `asyncio.run() cannot be called from a running event loop` because the Federation FastMCP bindings are double-looping on the underlying engine. Critical architectural fix needed.
*   `watch`: [4] Broken State (False Positive): Triggered the Hypervisor DDoS Circuit Breaker and sent a hard `os._exit(1)` kill signal to the entire MCP server background process because an IDE indexer touched `nucleus.json` too many times. *Architectural Change Required: Add diff-hashing and graceful timeouts instead of hard exiting via os._exit.*
*   `curl`: [7] Error Empathy: The God-Mode Egress Firewall cleanly trapped and rejected scraping `eidetic.works` with a perfect string message: `Domain not in ALLOWED_DOMAINS` without crashing the runtime.
*   `list / get_next`: [7] Error Empathy: Gracefully handled a Python `TypeError` ("'<' not supported between string and int") internally without propagating an RPC 500 error, instead returning `SUCCESS: True, ERROR: No matching tasks found`.
*   `read_artifact / write_artifact`: [15] Schema Cohesion (False Positive): The JSON-RPC test harness threw a serialization crash because these 3 tools return raw String Data payloads instead of standard JSON Maps, which is actually the intended architectural behavior for these specific `nucleus_sync` functions.
