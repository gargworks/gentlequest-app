### Phase E – Automated Incident Response (Spec Only – Not Implemented)

**Vision:** Close the agentic loop so Nucleus can auto-heal and auto-respond to incidents, letting the operator sleep while usage and moat grow.

**Principles:**
- Build entirely on existing Phases B–D telemetry (no new infra).
- Actions are explicit, logged, and reversible.
- Start with "progressive automation": suggest → gated actions → full auto.

**Initial capabilities (target):**
1. **Runtime auto-healing**
   - When error rate stays above threshold for N minutes:
     - Restart or scale the affected runtime / worker.
     - Optionally disable specific high-error commands/categories temporarily.
2. **Incident artifact creation**
   - On critical alerts:
     - Generate a Markdown incident report with:
       - Time window, metrics snapshots, top commands, traces links.
       - Hypothesis list and next-step checklist.
     - Store under `incidents/YYYY-MM/INCIDENT-<timestamp>.md`.
     - Optionally open a GitHub issue linking to the incident file (configurable).
3. **Chatops notifications**
   - Post a structured incident summary to Slack:
     - Severity, alert name, command/category, error and traffic stats.
     - Links to Grafana, Prometheus, Jaeger, incident file.
   - Later: PagerDuty integration (Phase F) for on-call.

**Safety rails:**
- No auto-deletion of user data or configs.
- All automated actions behind feature flags / config in `nucleus.yaml`.
- Every action is idempotent and recorded in an "incident action log".

**Exit criteria for Phase E:**
- For a simulated high-error scenario:
  - Incident is auto-detected, auto-documented, and auto-announced in Slack.
  - Optional auto-heal action is executed and logged.
  - Daily brief summarizes the incident and actions taken.
