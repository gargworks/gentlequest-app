# Ultimate 170 Atomic Tests Playbook (Natural Language Edition)

This playbook lists an absolute atomic, genuinely conversational natural language prompt to test every single one of the 170 underlying functions mapped behind the 12 Facade MCP tools. The LLM must infer the correct action and parameters from the phrasing.

**Workflow:**
1. Open up your connected LLM client (Opus/Claude).
2. Follow the `manual_testing_playbook.md` linearly.
3. Paste the **Test Prompt** for a single action. *(Note: Tri-prompt routing fuzzing is deferred to a future autonomous testing suite)*.
4. Report the result back to me in this thread.
5. I will mark that Action as `[x] COMPLETE` in the playbook.
6. **MANDATORY POST-FLIGHT CHECK**: Before asking for the next prompt, I will silently run the **25-Dimension Matrix Checklist** on the tool output:
   * **[Part A - Defensive]**: (1) Friction? (2) Context Bomber? (3) Hallucinated? (4) Overlap? (5) Mutation? (6) Cog Load? (7) Error Empathy? (8) Ripple? (9) Composability?
   * **[Part B - Offensive]**: (10) God Combo? (11) OpenClaw Asymmetry? (12) Data Arbitrage? (13) Zero-to-One Automation?
   * **[Part C - Architecture]**: (14) Code Bloat? (15) Schema Cohesion? (16) Dependency Risk?
   * **[Part D - Pragmatics]**: (17) Idempotency? (18) Latency/Tax? (19) HMI Legibility? (20) Setup Friction?
   * **[Part E - Epistemology]**: (21) Telemetry Bleed? (22) Ground Truth? (23) Criticality? (24) Recursive Safety? (25) DX Vibe?
7. **DELTA LOGGING**: If and ONLY if there is a significant spike/idea in any of those 25 dimensions, I will append a structured entry to the "Delta Log" in `verification_tracker.md`.
8. **CERTIFICATION MATRIX**: I will append a new row to the `🏆 Tool Quality Certification Matrix` in `verification_tracker.md` filling out the 12 operational columns (Bad Input, Idempotency, etc.) for the tool I just tested. Crucially, I will ensure the **Prompts** column logs exactly how many variants were tested (Currently defaults to 1).

## Facade: `nucleus_engrams`

### Action: `health`
- **Purpose:** Get system health status
- **Parameters Required:** `{}`
- **Test Prompt:** *"Hey Nucleus, what is your current system health?"*
- [x] **Status:** COMPLETE

### Action: `version`
- **Purpose:** Get Nucleus version info
- **Parameters Required:** `{}`
- **Test Prompt:** *"What is the system version?"*
- [x] **Status:** COMPLETE

### Action: `export_schema`
- **Purpose:** Export MCP toolset as JSON Schema
- **Parameters Required:** `{}`
- **Test Prompt:** *"Can you export the MCP toolset as a JSON Schema?"*
- [x] **Status:** COMPLETE

### Action: `performance_metrics`
- **Purpose:** Get perf metrics
- **Parameters Required:** `{export_to_file?}`
- **Test Prompt:** *"Could you pull up the perf metrics?"*
- [x] **Status:** COMPLETE

### Action: `prometheus_metrics`
- **Purpose:** Get Prometheus metrics
- **Parameters Required:** `{format?}`
- **Test Prompt:** *"Please give me the Prometheus metrics."*
- [x] **Status:** COMPLETE

### Action: `audit_log`
- **Purpose:** View cryptographic interaction log
- **Parameters Required:** `{limit?}`
- **Test Prompt:** *"I need the cryptographic interaction log."*
- [x] **Status:** COMPLETE

### Action: `write_engram`
- **Purpose:** Write engram to memory
- **Parameters Required:** `{key, value, context?, intensity?}`
- **Test Prompt:** *"Note to self: The auth port is 9090."*
- [x] **Status:** COMPLETE

### Action: `query_engrams`
- **Purpose:** Query engrams
- **Parameters Required:** `{context?, min_intensity?}`
- **Test Prompt:** *"Can you query engrams?"*
- [x] **Status:** COMPLETE

### Action: `search_engrams`
- **Purpose:** Search engrams
- **Parameters Required:** `{query, case_sensitive?}`
- **Test Prompt:** *"Could you search engrams for me?"*
- [x] **Status:** COMPLETE

### Action: `governance_status`
- **Purpose:** Get governance status
- **Parameters Required:** `{}`
- **Test Prompt:** *"Show me the governance status."*
- [x] **Status:** COMPLETE

### Action: `morning_brief`
- **Purpose:** Daily Nucleus Morning Brief
- **Parameters Required:** `{}`
- **Test Prompt:** *"I need the daily Nucleus Morning Brief."*
- [x] **Status:** COMPLETE

### Action: `hook_metrics`
- **Purpose:** Monitor auto-write engram hooks
- **Parameters Required:** `{}`
- **Test Prompt:** *"I'd like you to monitor auto-write engram hooks."*
- [x] **Status:** COMPLETE

### Action: `compounding_status`
- **Purpose:** Compounding Loop status
- **Parameters Required:** `{}`
- **Test Prompt:** *"Can you show me the compounding Loop status?"*
- [x] **Status:** COMPLETE

### Action: `end_of_day`
- **Purpose:** Capture EOD learnings
- **Parameters Required:** `{summary, key_decisions?, blockers?}`
- **Test Prompt:** *"Can you capture EOD learnings?"*
- [ ] **Status:** PENDING

### Action: `session_inject`
- **Purpose:** Session-start context injection
- **Parameters Required:** `{}`
- **Test Prompt:** *"Inject the starting context."*
- [x] **Status:** COMPLETE

### Action: `weekly_consolidate`
- **Purpose:** Weekly consolidation
- **Parameters Required:** `{dry_run?}`
- **Test Prompt:** *"Show me the weekly consolidation."*
- [x] **Status:** COMPLETE

### Action: `list_decisions`
- **Purpose:** List DecisionMade events
- **Parameters Required:** `{limit?}`
- **Test Prompt:** *"Show me the DecisionMade events."*
- [ ] **Status:** PENDING

### Action: `list_snapshots`
- **Purpose:** List context snapshots
- **Parameters Required:** `{limit?}`
- **Test Prompt:** *"Show me the context snapshots."*
- [ ] **Status:** PENDING

### Action: `metering_summary`
- **Purpose:** Token metering summary
- **Parameters Required:** `{since_hours?}`
- **Test Prompt:** *"I need the token metering summary."*
- [ ] **Status:** PENDING

### Action: `ipc_tokens`
- **Purpose:** List IPC auth tokens
- **Parameters Required:** `{active_only?}`
- **Test Prompt:** *"I need the IPC auth tokens."*
- [ ] **Status:** PENDING

### Action: `dsor_status`
- **Purpose:** Comprehensive DSoR status
- **Parameters Required:** `{}`
- **Test Prompt:** *"Where can I find the comprehensive DSoR status?"*
- [ ] **Status:** PENDING

### Action: `federation_dsor`
- **Purpose:** Federation DSoR status
- **Parameters Required:** `{}`
- **Test Prompt:** *"I need the federation DSoR status."*
- [ ] **Status:** PENDING

### Action: `routing_decisions`
- **Purpose:** Query routing decision history
- **Parameters Required:** `{limit?}`
- **Test Prompt:** *"Go ahead and query routing decision history."*
- [ ] **Status:** PENDING

### Action: `list_tools`
- **Purpose:** List tools at current tier
- **Parameters Required:** `{category?}`
- **Test Prompt:** *"Please give me the tools at current tier."*
- [ ] **Status:** PENDING

### Action: `tier_status`
- **Purpose:** Get tier configuration status
- **Parameters Required:** `{}`
- **Test Prompt:** *"What is the tier configuration status?"*
- [x] **Status:** COMPLETE

## Facade: `nucleus_features`

### Action: `add`
- **Purpose:** Add a feature
- **Parameters Required:** `{product, name, description, source, version, how_to_test, expected_result, status?, tags?}`
- **Test Prompt:** *"Could you add a feature for me?"*
- [x] **Status:** COMPLETE

### Action: `list`
- **Purpose:** List features
- **Parameters Required:** `{product?, status?, tag?}`
- **Test Prompt:** *"Show me the features."*
- [x] **Status:** COMPLETE

### Action: `get`
- **Purpose:** Get feature by ID
- **Parameters Required:** `{feature_id}`
- **Test Prompt:** *"Show me the feature by ID."*
- [x] **Status:** COMPLETE

### Action: `update`
- **Purpose:** Update feature fields
- **Parameters Required:** `{feature_id, status?, description?, version?}`
- **Test Prompt:** *"I'd like you to update feature fields."*
- [x] **Status:** COMPLETE

### Action: `validate`
- **Purpose:** Mark feature validated
- **Parameters Required:** `{feature_id, result}`
- **Test Prompt:** *"Could you mark feature validated for me?"*
- [x] **Status:** COMPLETE

### Action: `search`
- **Purpose:** Search features
- **Parameters Required:** `{query}`
- **Test Prompt:** *"I'd like you to search features."*
- [x] **Status:** COMPLETE

### Action: `mount_server`
- **Purpose:** Mount external MCP server
- **Parameters Required:** `{name, command, args?}`
- **Test Prompt:** *"Could you mount external MCP server for me?"*
- [x] **Status:** COMPLETE

### Action: `thanos_snap`
- **Purpose:** Trigger Instance Fractal Aggregation
- **Parameters Required:** `{}`
- **Test Prompt:** *"I'd like you to trigger Instance Fractal Aggregation."*
- [x] **Status:** COMPLETE

### Action: `unmount_server`
- **Purpose:** Unmount MCP server
- **Parameters Required:** `{server_id}`
- **Test Prompt:** *"Can you unmount MCP server?"*
- [x] **Status:** COMPLETE

### Action: `list_mounted`
- **Purpose:** List mounted MCP servers
- **Parameters Required:** `{}`
- **Test Prompt:** *"Show me the mounted MCP servers."*
- [x] **Status:** COMPLETE

### Action: `discover_tools`
- **Purpose:** Discover tools from mounted servers
- **Parameters Required:** `{server_id?}`
- **Test Prompt:** *"I need to discover tools from mounted servers. Can you handle that?"*
- [x] **Status:** COMPLETE

### Action: `invoke_tool`
- **Purpose:** Invoke tool on mounted server
- **Parameters Required:** `{server_id, tool_name, arguments?}`
- **Test Prompt:** *"Go ahead and invoke tool on mounted server."*
- [x] **Status:** COMPLETE

### Action: `traverse_mount`
- **Purpose:** Recursively mount downstream servers
- **Parameters Required:** `{root_mount_id}`
- **Test Prompt:** *"Where can I find the recursively mount downstream servers?"*
- [x] **Status:** COMPLETE

### Action: `generate_proof`
- **Purpose:** Generate proof document
- **Parameters Required:** `{feature_id, thinking?, deployed_url?, files_changed?, risk_level?, rollback_time?}`
- **Test Prompt:** *"Could you generate proof document for me?"*
- [x] **Status:** COMPLETE

### Action: `get_proof`
- **Purpose:** Get proof for a feature
- **Parameters Required:** `{feature_id}`
- **Test Prompt:** *"Could you pull up the proof for a feature?"*
- [x] **Status:** COMPLETE

### Action: `list_proofs`
- **Purpose:** List all proof documents
- **Parameters Required:** `{}`
- **Test Prompt:** *"Please give me the all proof documents."*
- [x] **Status:** COMPLETE

## Facade: `nucleus_federation`

### Action: `status`
- **Purpose:** Get comprehensive federation status
- **Parameters Required:** `{}`
- **Test Prompt:** *"Could you pull up the comprehensive federation status?"*
- [x] **Status:** COMPLETE

### Action: `join`
- **Purpose:** Join a federation via seed peer
- **Parameters Required:** `{seed_peer}`
- **Test Prompt:** *"Can you show me the join a federation via seed peer?"*
- [x] **Status:** COMPLETE

### Action: `leave`
- **Purpose:** Leave the federation gracefully
- **Parameters Required:** `{}`
- **Test Prompt:** *"Where can I find the leave the federation gracefully?"*
- [x] **Status:** COMPLETE

### Action: `peers`
- **Purpose:** List all federation peers with details
- **Parameters Required:** `{}`
- **Test Prompt:** *"Show me the all federation peers with details."*
- [x] **Status:** COMPLETE

### Action: `sync`
- **Purpose:** Force immediate synchronization with all peers
- **Parameters Required:** `{}`
- **Test Prompt:** *"Could you force immediate synchronization with all peers for me?"*
- [x] **Status:** COMPLETE

### Action: `route`
- **Purpose:** Route a task to the optimal brain
- **Parameters Required:** `{task_id, profile?}`
- **Test Prompt:** *"Could you pull up the route a task to the optimal brain?"*
- [x] **Status:** COMPLETE

### Action: `health`
- **Purpose:** Get federation health dashboard
- **Parameters Required:** `{}`
- **Test Prompt:** *"Hey Nucleus, what is your current system health?"*
- [x] **Status:** COMPLETE

## Facade: `nucleus_governance`

### Action: `auto_fix_loop`
- **Purpose:** Auto-fix loop: Verify->Diagnose->Fix->Verify (3 retries)
- **Parameters Required:** `{file_path, verification_command}`
- **Test Prompt:** *"Can you diagnose and auto-fix the failing `math_test.py`?"*
- [x] **Status:** COMPLETE

### Action: `lock`
- **Purpose:** [HYPERVISOR] Lock a file/dir immutable (chflags uchg)
- **Parameters Required:** `{path}`
- **Test Prompt:** *"Can you show me the [HYPERVISOR] Lock a file/dir immutable (chflags uchg)?"*
- [x] **Status:** COMPLETE

### Action: `unlock`
- **Purpose:** [HYPERVISOR] Unlock a file/dir
- **Parameters Required:** `{path}`
- **Test Prompt:** *"Show me the [HYPERVISOR] Unlock a file/dir."*
- [x] **Status:** COMPLETE

### Action: `set_mode`
- **Purpose:** [HYPERVISOR] Switch IDE context: "red" or "blue"
- **Parameters Required:** `{mode}`
- **Test Prompt:** *"I need the [HYPERVISOR] Switch IDE context: "red" or "blue"."*
- [x] **Status:** COMPLETE

### Action: `list_directory`
- **Purpose:** [GOVERNANCE] List files in a directory
- **Parameters Required:** `{path}`
- **Test Prompt:** *"Where can I find the [GOVERNANCE] List files in a directory?"*
- [x] **Status:** COMPLETE

### Action: `delete_file`
- **Purpose:** [GOVERNANCE] Delete a file (governed by Hypervisor)
- **Parameters Required:** `{path}`
- **Test Prompt:** *"Please give me the [GOVERNANCE] Delete a file (governed by Hypervisor)."*
- [x] **Status:** COMPLETE

### Action: `watch`
- **Purpose:** [HYPERVISOR] Monitor a file/folder for changes
- **Parameters Required:** `{path}`
- **Test Prompt:** *"Show me the [HYPERVISOR] Monitor a file/folder for changes."*
- [x] **Status:** COMPLETE

### Action: `status`
- **Purpose:** [HYPERVISOR] Report current security state of Agent OS
- **Parameters Required:** `{}`
- **Test Prompt:** *"Also check the hypervisor security status."*
- [x] **Status:** COMPLETE

### Action: `curl`
- **Purpose:** [EGRESS] Proxied HTTP fetch for air-gapped agents
- **Parameters Required:** `{url, method?}`
- **Test Prompt:** *"Could you pull up the [EGRESS] Proxied HTTP fetch for air-gapped agents?"*
- [x] **Status:** COMPLETE

### Action: `pip_install`
- **Purpose:** [EGRESS] Proxied pip install for air-gapped agents
- **Parameters Required:** `{package}`
- **Test Prompt:** *"Please give me the [EGRESS] Proxied pip install for air-gapped agents."*
- [x] **Status:** COMPLETE

## Facade: `nucleus_orchestration`

### Action: `satellite`
- **Purpose:** Unified satellite view
- **Parameters Required:** `{detail_level?}`
- **Test Prompt:** *"Can you show me the unified satellite view?"*
- [ ] **Status:** PENDING

### Action: `scan_commitments`
- **Purpose:** Scan artifacts for new commitments
- **Parameters Required:** `{}`
- **Test Prompt:** *"I'd like you to scan artifacts for new commitments."*
- [ ] **Status:** PENDING

### Action: `archive_stale`
- **Purpose:** Auto-archive commitments older than 30 days
- **Parameters Required:** `{}`
- **Test Prompt:** *"Can you show me the auto-archive commitments older than 30 days?"*
- [ ] **Status:** PENDING

### Action: `export`
- **Purpose:** Export brain to zip
- **Parameters Required:** `{}`
- **Test Prompt:** *"I'd like you to export brain to zip."*
- [ ] **Status:** PENDING

### Action: `list_commitments`
- **Purpose:** List open commitments
- **Parameters Required:** `{tier?}`
- **Test Prompt:** *"Can you show me the open commitments?"*
- [ ] **Status:** PENDING

### Action: `close_commitment`
- **Purpose:** Close a commitment
- **Parameters Required:** `{commitment_id, method}`
- **Test Prompt:** *"Can you close a commitment?"*
- [ ] **Status:** PENDING

### Action: `commitment_health`
- **Purpose:** Get commitment health summary
- **Parameters Required:** `{}`
- **Test Prompt:** *"Where can I find the commitment health summary?"*
- [ ] **Status:** PENDING

### Action: `open_loops`
- **Purpose:** View all open loops
- **Parameters Required:** `{type_filter?, tier_filter?}`
- **Test Prompt:** *"Where can I find the all open loops?"*
- [ ] **Status:** PENDING

### Action: `add_loop`
- **Purpose:** Add a new open loop
- **Parameters Required:** `{description, loop_type?, priority?}`
- **Test Prompt:** *"Could you add a new open loop for me?"*
- [ ] **Status:** PENDING

### Action: `weekly_challenge`
- **Purpose:** Manage weekly challenge
- **Parameters Required:** `{action?, challenge_id?}`
- **Test Prompt:** *"I'd like you to manage weekly challenge."*
- [ ] **Status:** PENDING

### Action: `patterns`
- **Purpose:** Manage learned patterns
- **Parameters Required:** `{action?}`
- **Test Prompt:** *"Please manage learned patterns."*
- [ ] **Status:** PENDING

### Action: `metrics`
- **Purpose:** Get coordination metrics
- **Parameters Required:** `{}`
- **Test Prompt:** *"I need the coordination metrics."*
- [ ] **Status:** PENDING

## Facade: `nucleus_telemetry`

### Action: `set_llm_tier`
- **Purpose:** Set default LLM tier
- **Parameters Required:** `{tier}`
- **Test Prompt:** *"Go ahead and set default LLM tier."*
- [ ] **Status:** PENDING

### Action: `get_llm_status`
- **Purpose:** Get LLM tier configuration
- **Parameters Required:** `{}`
- **Test Prompt:** *"Please give me the LLM tier configuration."*
- [ ] **Status:** PENDING

### Action: `record_interaction`
- **Purpose:** Record user interaction timestamp
- **Parameters Required:** `{}`
- **Test Prompt:** *"Could you record user interaction timestamp for me?"*
- [ ] **Status:** PENDING

### Action: `value_ratio`
- **Purpose:** Get Value Ratio metric
- **Parameters Required:** `{}`
- **Test Prompt:** *"Where can I find the Value Ratio metric?"*
- [ ] **Status:** PENDING

### Action: `check_kill_switch`
- **Purpose:** Check Kill Switch status
- **Parameters Required:** `{}`
- **Test Prompt:** *"Go ahead and check Kill Switch status."*
- [ ] **Status:** PENDING

### Action: `pause_notifications`
- **Purpose:** Pause PEFS notifications
- **Parameters Required:** `{}`
- **Test Prompt:** *"Go ahead and pause PEFS notifications."*
- [ ] **Status:** PENDING

### Action: `resume_notifications`
- **Purpose:** Resume PEFS notifications
- **Parameters Required:** `{}`
- **Test Prompt:** *"I'd like you to resume PEFS notifications."*
- [ ] **Status:** PENDING

### Action: `record_feedback`
- **Purpose:** Record notification feedback
- **Parameters Required:** `{notification_type, score}`
- **Test Prompt:** *"Could you record notification feedback for me?"*
- [ ] **Status:** PENDING

### Action: `mark_high_impact`
- **Purpose:** Mark loop closure as high-impact
- **Parameters Required:** `{}`
- **Test Prompt:** *"I'd like you to mark loop closure as high-impact."*
- [ ] **Status:** PENDING

### Action: `check_protocol`
- **Purpose:** Check protocol compliance
- **Parameters Required:** `{agent_id}`
- **Test Prompt:** *"Please check protocol compliance."*
- [ ] **Status:** PENDING

### Action: `request_handoff`
- **Purpose:** Request agent handoff
- **Parameters Required:** `{to_agent, context, request, priority?, artifacts?}`
- **Test Prompt:** *"I'd like you to request agent handoff."*
- [ ] **Status:** PENDING

### Action: `get_handoffs`
- **Purpose:** Get pending handoffs
- **Parameters Required:** `{agent_id?}`
- **Test Prompt:** *"Please give me the pending handoffs."*
- [ ] **Status:** PENDING

## Facade: `nucleus_slots`

### Action: `orchestrate`
- **Purpose:** THE GOD COMMAND
- **Parameters Required:** `{slot_id?, model?, alias?, mode?}`
- **Test Prompt:** *"Could you pull up the tHE GOD COMMAND?"*
- [ ] **Status:** PENDING

### Action: `slot_complete`
- **Purpose:** Mark task complete
- **Parameters Required:** `{slot_id, task_id, outcome?, notes?}`
- **Test Prompt:** *"I need to mark task complete. Can you handle that?"*
- [ ] **Status:** PENDING

### Action: `slot_exhaust`
- **Purpose:** Mark slot exhausted
- **Parameters Required:** `{slot_id, reset_hours?}`
- **Test Prompt:** *"Please mark slot exhausted."*
- [ ] **Status:** PENDING

### Action: `status_dashboard`
- **Purpose:** ASCII dashboard
- **Parameters Required:** `{detail_level?}`
- **Test Prompt:** *"Can you show me the aSCII dashboard?"*
- [ ] **Status:** PENDING

### Action: `autopilot_sprint`
- **Purpose:** Sprint command
- **Parameters Required:** `{slots?, mode?, halt_on_blocker?, halt_on_tier_mismatch?, max_tasks_per_slot?, budget_limit?, dry_run?}`
- **Test Prompt:** *"Show me the sprint command."*
- [ ] **Status:** PENDING

### Action: `force_assign`
- **Purpose:** Force assign task
- **Parameters Required:** `{slot_id, task_id, acknowledge_risk?}`
- **Test Prompt:** *"Can you force assign task?"*
- [ ] **Status:** PENDING

### Action: `autopilot_sprint_v2`
- **Purpose:** Enhanced sprint V3.1
- **Parameters Required:** `{slots?, mode?, halt_on_blocker?, halt_on_tier_mismatch?, max_tasks_per_slot?, budget_limit?, time_limit_hours?, dry_run?}`
- **Test Prompt:** *"Show me the enhanced sprint V3.1."*
- [ ] **Status:** PENDING

### Action: `start_mission`
- **Purpose:** Start mission
- **Parameters Required:** `{name, goal, task_ids, slot_ids?, budget_limit?, time_limit_hours?, success_criteria?}`
- **Test Prompt:** *"I need to start mission. Can you handle that?"*
- [ ] **Status:** PENDING

### Action: `mission_status`
- **Purpose:** Get mission status
- **Parameters Required:** `{mission_id?}`
- **Test Prompt:** *"Can you show me the mission status?"*
- [ ] **Status:** PENDING

### Action: `halt_sprint`
- **Purpose:** Halt sprint
- **Parameters Required:** `{reason?}`
- **Test Prompt:** *"Can you halt sprint?"*
- [ ] **Status:** PENDING

### Action: `resume_sprint`
- **Purpose:** Resume sprint
- **Parameters Required:** `{sprint_id?}`
- **Test Prompt:** *"I need to resume sprint. Can you handle that?"*
- [ ] **Status:** PENDING

## Facade: `nucleus_infra`

### Action: `file_changes`
- **Purpose:** Get pending file change events
- **Parameters Required:** `{}`
- **Test Prompt:** *"Could you pull up the pending file change events?"*
- [ ] **Status:** PENDING

### Action: `gcloud_status`
- **Purpose:** Check GCloud auth status
- **Parameters Required:** `{}`
- **Test Prompt:** *"Please check GCloud auth status."*
- [ ] **Status:** PENDING

### Action: `gcloud_services`
- **Purpose:** List Cloud Run services
- **Parameters Required:** `{project?, region?}`
- **Test Prompt:** *"Could you pull up the Cloud Run services?"*
- [ ] **Status:** PENDING

### Action: `list_services`
- **Purpose:** List Render.com services
- **Parameters Required:** `{}`
- **Test Prompt:** *"I need the Render.com services."*
- [ ] **Status:** PENDING

### Action: `scan_marketing_log`
- **Purpose:** Scan marketing log for failures
- **Parameters Required:** `{}`
- **Test Prompt:** *"Can you scan marketing log for failures?"*
- [ ] **Status:** PENDING

### Action: `synthesize_strategy`
- **Purpose:** Analyze marketing & update strategy
- **Parameters Required:** `{focus_topic?}`
- **Test Prompt:** *"Show me the analyze marketing & update strategy."*
- [ ] **Status:** PENDING

### Action: `status_report`
- **Purpose:** Generate State of the Union
- **Parameters Required:** `{focus?}`
- **Test Prompt:** *"Could you generate State of the Union for me?"*
- [ ] **Status:** PENDING

### Action: `optimize_workflow`
- **Purpose:** Self-optimize workflow cheatsheet
- **Parameters Required:** `{}`
- **Test Prompt:** *"Please give me the self-optimize workflow cheatsheet."*
- [ ] **Status:** PENDING

### Action: `manage_strategy`
- **Purpose:** Read/Update strategy doc
- **Parameters Required:** `{action, content?}`
- **Test Prompt:** *"Please give me the read/Update strategy doc."*
- [ ] **Status:** PENDING

### Action: `update_roadmap`
- **Purpose:** Read/Update roadmap
- **Parameters Required:** `{action, item?}`
- **Test Prompt:** *"I need the read/Update roadmap."*
- [ ] **Status:** PENDING

## Facade: `nucleus_agents`

### Action: `spawn_agent`
- **Purpose:** Spawn Ephemeral Agent
- **Parameters Required:** `{intent, execute_now?, persona?}`
- **Test Prompt:** *"Could you spawn Ephemeral Agent for me?"*
- [ ] **Status:** PENDING

### Action: `apply_critique`
- **Purpose:** Apply critique fixes
- **Parameters Required:** `{review_path}`
- **Test Prompt:** *"Could you apply critique fixes for me?"*
- [ ] **Status:** PENDING

### Action: `orchestrate_swarm`
- **Purpose:** Start multi-agent swarm
- **Parameters Required:** `{mission, agents?}`
- **Test Prompt:** *"I'd like you to start multi-agent swarm."*
- [ ] **Status:** PENDING

### Action: `search_memory`
- **Purpose:** Search long-term memory
- **Parameters Required:** `{query}`
- **Test Prompt:** *"Please search long-term memory."*
- [ ] **Status:** PENDING

### Action: `read_memory`
- **Purpose:** Read memory category
- **Parameters Required:** `{category}`
- **Test Prompt:** *"Can you read memory category?"*
- [ ] **Status:** PENDING

### Action: `respond_to_consent`
- **Purpose:** Respond to respawn consent
- **Parameters Required:** `{agent_id, choice?}`
- **Test Prompt:** *"Can you respond to respawn consent?"*
- [ ] **Status:** PENDING

### Action: `list_pending_consents`
- **Purpose:** List agents awaiting consent
- **Parameters Required:** `{}`
- **Test Prompt:** *"Please give me the agents awaiting consent."*
- [ ] **Status:** PENDING

### Action: `critique_code`
- **Purpose:** Run Critic review
- **Parameters Required:** `{file_path, context?}`
- **Test Prompt:** *"Go ahead and run Critic review."*
- [ ] **Status:** PENDING

### Action: `fix_code`
- **Purpose:** Auto-fix code
- **Parameters Required:** `{file_path, issues_context}`
- **Test Prompt:** *"Go ahead and auto-fix code."*
- [ ] **Status:** PENDING

### Action: `session_briefing`
- **Purpose:** Get session briefing
- **Parameters Required:** `{conversation_id?}`
- **Test Prompt:** *"Please give me the session briefing."*
- [ ] **Status:** PENDING

### Action: `register_session`
- **Purpose:** Register session focus
- **Parameters Required:** `{conversation_id, focus_area}`
- **Test Prompt:** *"Register 'Stripe Integration' as our active session focus."*
- [x] **Status:** COMPLETE

### Action: `handoff_task`
- **Purpose:** Hand off task
- **Parameters Required:** `{task_description, target_session_id?, priority?}`
- **Test Prompt:** *"Could you pull up the hand off task?"*
- [ ] **Status:** PENDING

### Action: `ingest_tasks`
- **Purpose:** Ingest tasks
- **Parameters Required:** `{source, source_type?, session_id?, auto_assign?, skip_dedup?, dry_run?}`
- **Test Prompt:** *"Please give me the ingest tasks."*
- [ ] **Status:** PENDING

### Action: `rollback_ingestion`
- **Purpose:** Rollback ingestion
- **Parameters Required:** `{batch_id, reason?}`
- **Test Prompt:** *"Can you show me the rollback ingestion?"*
- [ ] **Status:** PENDING

### Action: `ingestion_stats`
- **Purpose:** Get ingestion statistics
- **Parameters Required:** `{}`
- **Test Prompt:** *"Show me the ingestion statistics."*
- [ ] **Status:** PENDING

### Action: `dashboard`
- **Purpose:** Enhanced dashboard
- **Parameters Required:** `{detail_level?, format?, include_alerts?, include_trends?, category?}`
- **Test Prompt:** *"Show me the enhanced dashboard."*
- [ ] **Status:** PENDING

### Action: `snapshot_dashboard`
- **Purpose:** Create dashboard snapshot
- **Parameters Required:** `{name?}`
- **Test Prompt:** *"I need to create dashboard snapshot. Can you handle that?"*
- [ ] **Status:** PENDING

### Action: `list_dashboard_snapshots`
- **Purpose:** List snapshots
- **Parameters Required:** `{limit?}`
- **Test Prompt:** *"Can you show me the snapshots?"*
- [ ] **Status:** PENDING

### Action: `get_alerts`
- **Purpose:** Get active alerts
- **Parameters Required:** `{}`
- **Test Prompt:** *"Show me the active alerts."*
- [ ] **Status:** PENDING

### Action: `set_alert_threshold`
- **Purpose:** Set alert threshold
- **Parameters Required:** `{metric, level, value}`
- **Test Prompt:** *"Go ahead and set alert threshold."*
- [ ] **Status:** PENDING

## Facade: `nucleus_sessions`

### Action: `save`
- **Purpose:** Save session for later
- **Parameters Required:** `{context, active_task?, pending_decisions?, breadcrumbs?, next_steps?}`
- **Test Prompt:** *"Show me the save session for later."*
- [ ] **Status:** PENDING

### Action: `resume`
- **Purpose:** Resume a saved session
- **Parameters Required:** `{session_id?}`
- **Test Prompt:** *"Can you resume a saved session?"*
- [ ] **Status:** PENDING

### Action: `list`
- **Purpose:** List all saved sessions
- **Parameters Required:** `{}`
- **Test Prompt:** *"Where can I find the all saved sessions?"*
- [ ] **Status:** PENDING

### Action: `check_recent`
- **Purpose:** Check for recent session to resume
- **Parameters Required:** `{}`
- **Test Prompt:** *"Please check for recent session to resume."*
- [ ] **Status:** PENDING

### Action: `end`
- **Purpose:** End work session
- **Parameters Required:** `{summary?, learnings?, mood?}`
- **Test Prompt:** *"Can you end work session?"*
- [ ] **Status:** PENDING

### Action: `start`
- **Purpose:** Mandatory session start protocol
- **Parameters Required:** `{}`
- **Test Prompt:** *"Could you pull up the mandatory session start protocol?"*
- [ ] **Status:** PENDING

### Action: `archive_resolved`
- **Purpose:** Archive .resolved.* backup files
- **Parameters Required:** `{}`
- **Test Prompt:** *"Go ahead and archive .resolved.* backup files."*
- [ ] **Status:** PENDING

### Action: `propose_merges`
- **Purpose:** Detect redundant artifacts, generate merge proposals
- **Parameters Required:** `{}`
- **Test Prompt:** *"Where can I find the detect redundant artifacts, generate merge proposals?"*
- [ ] **Status:** PENDING

### Action: `garbage_collect`
- **Purpose:** Archive stale tasks
- **Parameters Required:** `{max_age_hours?, dry_run?}`
- **Test Prompt:** *"Go ahead and archive stale tasks."*
- [ ] **Status:** PENDING

### Action: `emit_event`
- **Purpose:** Emit event to brain ledger
- **Parameters Required:** `{event_type, emitter, data, description?}`
- **Test Prompt:** *"Can you show me the emit event to brain ledger?"*
- [ ] **Status:** PENDING

### Action: `read_events`
- **Purpose:** Read recent events
- **Parameters Required:** `{limit?}`
- **Test Prompt:** *"I'd like you to read recent events."*
- [ ] **Status:** PENDING

### Action: `get_state`
- **Purpose:** Get brain state
- **Parameters Required:** `{path?}`
- **Test Prompt:** *"Please give me the brain state."*
- [ ] **Status:** PENDING

### Action: `update_state`
- **Purpose:** Update brain state
- **Parameters Required:** `{updates}`
- **Test Prompt:** *"Go ahead and update brain state."*
- [ ] **Status:** PENDING

### Action: `checkpoint`
- **Purpose:** Save task checkpoint
- **Parameters Required:** `{task_id, step?, progress_percent?, context?, artifacts?, resumable?}`
- **Test Prompt:** *"Can you show me the save task checkpoint?"*
- [ ] **Status:** PENDING

### Action: `resume_checkpoint`
- **Purpose:** Resume from checkpoint
- **Parameters Required:** `{task_id}`
- **Test Prompt:** *"I need to resume from checkpoint. Can you handle that?"*
- [ ] **Status:** PENDING

### Action: `handoff_summary`
- **Purpose:** Generate handoff summary
- **Parameters Required:** `{task_id, summary, key_decisions?, handoff_notes?}`
- **Test Prompt:** *"I need to generate handoff summary. Can you handle that?"*
- [ ] **Status:** PENDING

## Facade: `nucleus_sync`

### Action: `identify_agent`
- **Purpose:** Register agent identity
- **Parameters Required:** `{agent_id, environment, role?}`
- **Test Prompt:** *"I need the register agent identity."*
- [x] **Status:** COMPLETE

### Action: `sync_status`
- **Purpose:** Check current multi-agent sync status
- **Parameters Required:** `{}`
- **Test Prompt:** *"Can you check current multi-agent sync status?"*
- [x] **Status:** COMPLETE

### Action: `sync_now`
- **Purpose:** Manually trigger sync
- **Parameters Required:** `{force?}`
- **Test Prompt:** *"Please give me the manually trigger sync."*
- [x] **Status:** COMPLETE

### Action: `sync_auto`
- **Purpose:** Enable/disable file watching
- **Parameters Required:** `{enable}`
- **Test Prompt:** *"Show me the enable/disable file watching."*
- [x] **Status:** COMPLETE

### Action: `sync_resolve`
- **Purpose:** Resolve a file conflict
- **Parameters Required:** `{file_path, strategy?}`
- **Test Prompt:** *"Can you show me the resolve a file conflict?"*
- [x] **Status:** COMPLETE

### Action: `read_artifact`
- **Purpose:** Read an artifact file
- **Parameters Required:** `{path}`
- **Test Prompt:** *"I'd like you to read an artifact file."*
- [x] **Status:** COMPLETE

### Action: `write_artifact`
- **Purpose:** Write to an artifact file
- **Parameters Required:** `{path, content}`
- **Test Prompt:** *"Show me the write to an artifact file."*
- [x] **Status:** COMPLETE

### Action: `list_artifacts`
- **Purpose:** List artifacts
- **Parameters Required:** `{folder?}`
- **Test Prompt:** *"Please give me the artifacts."*
- [x] **Status:** COMPLETE

### Action: `trigger_agent`
- **Purpose:** Trigger an agent via event
- **Parameters Required:** `{agent, task_description, context_files?}`
- **Test Prompt:** *"Can you trigger an agent via event?"*
- [x] **Status:** COMPLETE

### Action: `get_triggers`
- **Purpose:** Get all defined neural triggers
- **Parameters Required:** `{}`
- **Test Prompt:** *"Where can I find the all defined neural triggers?"*
- [x] **Status:** COMPLETE

### Action: `evaluate_triggers`
- **Purpose:** Evaluate triggers for an event
- **Parameters Required:** `{event_type, emitter}`
- **Test Prompt:** *"Where can I find the evaluate triggers for an event?"*
- [x] **Status:** COMPLETE

### Action: `start_deploy_poll`
- **Purpose:** Start monitoring a Render deploy
- **Parameters Required:** `{service_id, commit_sha?}`
- **Test Prompt:** *"I need to start monitoring a Render deploy. Can you handle that?"*
- [x] **Status:** COMPLETE

### Action: `check_deploy`
- **Purpose:** Check deploy poll status
- **Parameters Required:** `{service_id}`
- **Test Prompt:** *"Please check deploy poll status."*
- [x] **Status:** COMPLETE

### Action: `complete_deploy`
- **Purpose:** Mark deploy complete
- **Parameters Required:** `{service_id, success, deploy_url?, error?, run_smoke_test?}`
- **Test Prompt:** *"I'd like you to mark deploy complete."*
- [x] **Status:** COMPLETE

### Action: `smoke_test`
- **Purpose:** Run a smoke test
- **Parameters Required:** `{url, endpoint?}`
- **Test Prompt:** *"Go ahead and run a smoke test."*
- [x] **Status:** COMPLETE

## Facade: `nucleus_tasks`

### Action: `list`
- **Purpose:** List tasks
- **Parameters Required:** `{status?, priority?, skill?, claimed_by?}`
- **Test Prompt:** *"Could you pull up the tasks?"*
- [ ] **Status:** PENDING

### Action: `get_next`
- **Purpose:** Get highest-priority unblocked task
- **Parameters Required:** `{skills}`
- **Test Prompt:** *"Can you show me the highest-priority unblocked task?"*
- [ ] **Status:** PENDING

### Action: `claim`
- **Purpose:** Atomically claim a task
- **Parameters Required:** `{task_id, agent_id}`
- **Test Prompt:** *"Can you show me the atomically claim a task?"*
- [ ] **Status:** PENDING

### Action: `update`
- **Purpose:** Update task fields
- **Parameters Required:** `{task_id, updates}`
- **Test Prompt:** *"Go ahead and update task fields."*
- [ ] **Status:** PENDING

### Action: `add`
- **Purpose:** Create a new task
- **Parameters Required:** `{description, priority?, blocked_by?, required_skills?, source?, task_id?, skip_dep_check?}`
- **Test Prompt:** *"Can you add a high priority task for 'Stripe Integration'?"*
- [x] **Status:** COMPLETE

### Action: `import_jsonl`
- **Purpose:** Import tasks from JSONL
- **Parameters Required:** `{jsonl_path, clear_existing?, merge_gtm_metadata?}`
- **Test Prompt:** *"Can you import tasks from JSONL?"*
- [ ] **Status:** PENDING

### Action: `escalate`
- **Purpose:** Escalate task for human help
- **Parameters Required:** `{task_id, reason}`
- **Test Prompt:** *"Show me the escalate task for human help."*
- [ ] **Status:** PENDING

### Action: `depth_push`
- **Purpose:** Go deeper into subtopic
- **Parameters Required:** `{topic}`
- **Test Prompt:** *"Where can I find the go deeper into subtopic?"*
- [ ] **Status:** PENDING

### Action: `depth_pop`
- **Purpose:** Come back up one level
- **Parameters Required:** `{}`
- **Test Prompt:** *"Where can I find the come back up one level?"*
- [ ] **Status:** PENDING

### Action: `depth_show`
- **Purpose:** Show current depth state
- **Parameters Required:** `{}`
- **Test Prompt:** *"Could you pull up the show current depth state?"*
- [ ] **Status:** PENDING

### Action: `depth_reset`
- **Purpose:** Reset depth to root
- **Parameters Required:** `{}`
- **Test Prompt:** *"I need the reset depth to root."*
- [ ] **Status:** PENDING

### Action: `depth_set_max`
- **Purpose:** Set max safe depth
- **Parameters Required:** `{max_depth}`
- **Test Prompt:** *"Can you set max safe depth?"*
- [ ] **Status:** PENDING

### Action: `depth_map`
- **Purpose:** Generate exploration map
- **Parameters Required:** `{}`
- **Test Prompt:** *"Can you generate exploration map?"*
- [ ] **Status:** PENDING

### Action: `context_switch`
- **Purpose:** Record context switch / ADHD drift check
- **Parameters Required:** `{new_context}`
- **Test Prompt:** *"Could you record context switch / ADHD drift check for me?"*
- [ ] **Status:** PENDING

### Action: `context_switch_status`
- **Purpose:** Get context switch metrics
- **Parameters Required:** `{}`
- **Test Prompt:** *"Show me the context switch metrics."*
- [ ] **Status:** PENDING

### Action: `context_switch_reset`
- **Purpose:** Reset context switch counter
- **Parameters Required:** `{}`
- **Test Prompt:** *"Where can I find the reset context switch counter?"*
- [ ] **Status:** PENDING

---
**Total Atomic Tests:** 170

## Facade: `nucleus_sessions`

### Action: `list`
- [x] **Status:** COMPLETE

### Action: `check_recent`
- [x] **Status:** COMPLETE

### Action: `get_state`
- [x] **Status:** COMPLETE

### Action: `read_events`
- [x] **Status:** COMPLETE

### Action: `start`
- [x] **Status:** COMPLETE

### Action: `end`
- [x] **Status:** COMPLETE

### Action: `save`
- [x] **Status:** COMPLETE

### Action: `resume`
- [x] **Status:** COMPLETE

### Action: `archive_resolved`
- [x] **Status:** COMPLETE

### Action: `propose_merges`
- [x] **Status:** COMPLETE

### Action: `garbage_collect`
- [x] **Status:** COMPLETE

### Action: `emit_event`
- [x] **Status:** COMPLETE

### Action: `update_state`
- [x] **Status:** COMPLETE

### Action: `checkpoint`
- [x] **Status:** COMPLETE

### Action: `resume_checkpoint`
- [x] **Status:** COMPLETE

### Action: `handoff_summary`
- [x] **Status:** COMPLETE

## Facade: `nucleus_tasks`

### Action: `list`
- [ ] **Status:** PENDING

### Action: `get_next`
- [ ] **Status:** PENDING

### Action: `claim`
- [ ] **Status:** PENDING

### Action: `update`
- [ ] **Status:** PENDING

### Action: `add`
- [ ] **Status:** PENDING

### Action: `import_jsonl`
- [ ] **Status:** PENDING

### Action: `escalate`
- [ ] **Status:** PENDING

### Action: `depth_push`
- [ ] **Status:** PENDING

### Action: `depth_pop`
- [ ] **Status:** PENDING

### Action: `depth_show`
- [ ] **Status:** PENDING

### Action: `depth_reset`
- [ ] **Status:** PENDING

### Action: `depth_set_max`
- [ ] **Status:** PENDING

### Action: `depth_map`
- [ ] **Status:** PENDING

### Action: `context_switch`
- [ ] **Status:** PENDING

### Action: `context_switch_status`
- [ ] **Status:** PENDING

### Action: `context_switch_reset`
- [ ] **Status:** PENDING

## Facade: `nucleus_sync`

### Action: `identify_agent`
- [ ] **Status:** PENDING

### Action: `sync_status`
- [ ] **Status:** PENDING

### Action: `sync_now`
- [ ] **Status:** PENDING

### Action: `sync_auto`
- [ ] **Status:** PENDING

### Action: `sync_resolve`
- [ ] **Status:** PENDING

### Action: `read_artifact`
- [ ] **Status:** PENDING

### Action: `write_artifact`
- [ ] **Status:** PENDING

### Action: `list_artifacts`
- [ ] **Status:** PENDING

### Action: `trigger_agent`
- [ ] **Status:** PENDING

### Action: `get_triggers`
- [ ] **Status:** PENDING

### Action: `evaluate_triggers`
- [ ] **Status:** PENDING

### Action: `start_deploy_poll`
- [ ] **Status:** PENDING

### Action: `check_deploy`
- [ ] **Status:** PENDING

### Action: `complete_deploy`
- [ ] **Status:** PENDING

### Action: `smoke_test`
- [ ] **Status:** PENDING


## Facade: `nucleus_orchestration`

### Action: `satellite`
- [x] **Status:** COMPLETE

### Action: `scan_commitments`
- [x] **Status:** COMPLETE

### Action: `archive_stale`
- [x] **Status:** COMPLETE

### Action: `export`
- [x] **Status:** COMPLETE

### Action: `list_commitments`
- [x] **Status:** COMPLETE

### Action: `close_commitment`
- [x] **Status:** COMPLETE

### Action: `commitment_health`
- [x] **Status:** COMPLETE

### Action: `open_loops`
- [x] **Status:** COMPLETE

### Action: `add_loop`
- [x] **Status:** COMPLETE

### Action: `weekly_challenge`
- [x] **Status:** COMPLETE

### Action: `patterns`
- [x] **Status:** COMPLETE

### Action: `metrics`
- [x] **Status:** COMPLETE


## Facade: `nucleus_telemetry`

### Action: `set_llm_tier`
- [x] **Status:** COMPLETE

### Action: `get_llm_status`
- [x] **Status:** COMPLETE

### Action: `record_interaction`
- [x] **Status:** COMPLETE

### Action: `value_ratio`
- [x] **Status:** COMPLETE

### Action: `check_kill_switch`
- [x] **Status:** COMPLETE

### Action: `pause_notifications`
- [x] **Status:** COMPLETE

### Action: `resume_notifications`
- [x] **Status:** COMPLETE

### Action: `record_feedback`
- [x] **Status:** COMPLETE

### Action: `mark_high_impact`
- [x] **Status:** COMPLETE

### Action: `check_protocol`
- [x] **Status:** COMPLETE

### Action: `request_handoff`
- [x] **Status:** COMPLETE

### Action: `get_handoffs`
- [x] **Status:** COMPLETE


## Facade: `nucleus_slots`

### Action: `orchestrate`
- [x] **Status:** COMPLETE

### Action: `slot_complete`
- [x] **Status:** COMPLETE

### Action: `slot_exhaust`
- [x] **Status:** COMPLETE

### Action: `status_dashboard`
- [x] **Status:** COMPLETE

### Action: `autopilot_sprint`
- [x] **Status:** COMPLETE

### Action: `force_assign`
- [x] **Status:** COMPLETE

### Action: `autopilot_sprint_v2`
- [x] **Status:** COMPLETE

### Action: `start_mission`
- [x] **Status:** COMPLETE

### Action: `mission_status`
- [x] **Status:** COMPLETE

### Action: `halt_sprint`
- [x] **Status:** COMPLETE

### Action: `resume_sprint`
- [x] **Status:** COMPLETE


## Facade: `nucleus_infra`

### Action: `file_changes`
- [x] **Status:** COMPLETE

### Action: `gcloud_status`
- [x] **Status:** COMPLETE

### Action: `gcloud_services`
- [x] **Status:** COMPLETE

### Action: `list_services`
- [x] **Status:** COMPLETE

### Action: `scan_marketing_log`
- [x] **Status:** COMPLETE

### Action: `synthesize_strategy`
- [x] **Status:** COMPLETE

### Action: `status_report`
- [x] **Status:** COMPLETE

### Action: `optimize_workflow`
- [x] **Status:** COMPLETE

### Action: `manage_strategy`
- [x] **Status:** COMPLETE

### Action: `update_roadmap`
- [x] **Status:** COMPLETE


## Facade: `nucleus_agents`

### Action: `spawn_agent`
- [x] **Status:** COMPLETE

### Action: `apply_critique`
- [x] **Status:** COMPLETE

### Action: `orchestrate_swarm`
- [x] **Status:** COMPLETE

### Action: `search_memory`
- [x] **Status:** COMPLETE

### Action: `read_memory`
- [x] **Status:** COMPLETE

### Action: `respond_to_consent`
- [x] **Status:** COMPLETE

### Action: `list_pending_consents`
- [x] **Status:** COMPLETE

### Action: `critique_code`
- [x] **Status:** COMPLETE

### Action: `fix_code`
- [x] **Status:** COMPLETE

### Action: `session_briefing`
- [x] **Status:** COMPLETE

### Action: `register_session`
- [x] **Status:** COMPLETE

### Action: `handoff_task`
- [x] **Status:** COMPLETE

### Action: `ingest_tasks`
- [x] **Status:** COMPLETE

### Action: `rollback_ingestion`
- [x] **Status:** COMPLETE

### Action: `ingestion_stats`
- [x] **Status:** COMPLETE

### Action: `dashboard`
- [x] **Status:** COMPLETE

### Action: `snapshot_dashboard`
- [x] **Status:** COMPLETE

### Action: `list_dashboard_snapshots`
- [x] **Status:** COMPLETE

### Action: `get_alerts`
- [x] **Status:** COMPLETE

### Action: `set_alert_threshold`
- [x] **Status:** COMPLETE

## Facilitative God Combos & Hardening (New)

### Action: `validate_strategic_plan`
- **Purpose:** Validate Strategic mode PLAN
- **Parameters Required:** `{plan_text, mode?}`
- **Test Prompt:** *"Please validate this strategic plan for me."*
- [ ] **Status:** PENDING

### Action: `pulse_and_polish`
- **Purpose:** God Combo: automated health check pipeline
- **Parameters Required:** `{write_engram?}`
- **Test Prompt:** *"Run the pulse and polish pipeline."*
- [ ] **Status:** PENDING

### Action: `self_healing_sre`
- **Purpose:** God Combo: SRE diagnosis pipeline
- **Parameters Required:** `{symptom, write_engram?}`
- **Test Prompt:** *"Can you run the self healing sre loop for this symptom?"*
- [ ] **Status:** PENDING

### Action: `fusion_reactor`
- **Purpose:** God Combo: self-reinforcing memory loop
- **Parameters Required:** `{observation, context?, intensity?, write_engrams?}`
- **Test Prompt:** *"Trigger the fusion reactor loop."*
- [ ] **Status:** PENDING

### Action: `context_graph`
- **Purpose:** Build engram relationship graph
- **Parameters Required:** `{include_edges?, min_intensity?}`
- **Test Prompt:** *"Build the context graph."*
- [ ] **Status:** PENDING

### Action: `engram_neighbors`
- **Purpose:** Get neighborhood of an engram
- **Parameters Required:** `{key, max_depth?}`
- **Test Prompt:** *"Get the engram neighbors."*
- [ ] **Status:** PENDING

### Action: `billing_summary`
- **Purpose:** Usage cost tracking from audit logs
- **Parameters Required:** `{since_hours?, group_by?}`
- **Test Prompt:** *"Give me the billing summary."*
- [ ] **Status:** PENDING

### Action: `render_graph`
- **Purpose:** ASCII visualization of engram context graph
- **Parameters Required:** `{max_nodes?, min_intensity?}`
- **Test Prompt:** *"Render the context graph."*
- [ ] **Status:** PENDING

### Action: `agent_cost_dashboard`
- **Purpose:** Get agent cost tracking dashboard
- **Parameters Required:** `{}`
- **Test Prompt:** *"Show me the agent cost dashboard."*
- [ ] **Status:** PENDING

### Action: `dispatch_metrics`
- **Purpose:** Get dispatch telemetry
- **Parameters Required:** `{}`
- **Test Prompt:** *"Pull the dispatch metrics."*
- [ ] **Status:** PENDING
