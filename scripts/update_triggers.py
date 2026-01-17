
import json
from pathlib import Path

triggers_path = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/ledger/triggers.json")

# Load existing to preserve (if needed) but honestly, full rewrite is safer to ensure state
content = {
  "version": "2.2",
  "triggers": [
    {
      "id": "task-state-changed",
      "event_type": "task_state_changed",
      "condition": "always",
      "activates": "synthesizer",
      "description": "Log task state transitions for digest"
    },
    {
      "id": "task-created",
      "event_type": "task_created",
      "condition": "always",
      "activates": "orchestrator",
      "description": "New task added to queue"
    },
    {
      "id": "commitment-created",
      "event_type": "commitment_created",
      "condition": "always",
      "activates": "synthesizer",
      "description": "New commitment for tracking"
    },
    {
      "id": "commitment-closed",
      "event_type": "commitment_closed",
      "condition": "always",
      "activates": "synthesizer",
      "description": "Commitment closed, update velocity"
    },
    {
      "id": "health-check",
      "event_type": "health_status",
      "condition": "always",
      "activates": "synthesizer",
      "description": "Health check results for monitoring"
    },
    {
      "id": "deploy-complete",
      "event_type": "deploy_complete",
      "condition": "always",
      "activates": "tester",
      "description": "Deploy finished, run verification"
    },
    {
      "id": "session-saved",
      "event_type": "session_saved",
      "condition": "always",
      "activates": "synthesizer",
      "description": "Context saved for continuity"
    },
    {
      "id": "critical-escalation",
      "event_type": "*",
      "condition": "severity == 'CRITICAL'",
      "activates": "synthesizer",
      "description": "Any critical event escalates to Synthesizer"
    },
    {
      "id": "trigger-grooming",
      "event_type": "spec_needed",
      "condition": "always",
      "activates": "product_manager",
      "description": "PM grooms backlog and writes specs."
    },
    {
      "id": "trigger-design",
      "event_type": "spec_ready",
      "condition": "always",
      "activates": "architect",
      "description": "Architect designs system from PM specs."
    },
    {
      "id": "trigger-implementation",
      "event_type": "design_ready",
      "condition": "always",
      "activates": "developer",
      "description": "Developer implements code from Architecture design."
    },
    {
        "id": "trigger-deployment",
        "event_type": "deployment_request",
        "condition": "always",
        "activates": "devops",
        "description": "DevOps handles deployment related requests."
    },
    {
        "id": "trigger-synthesis",
        "event_type": "user_intent",
        "condition": "always",
        "activates": "synthesizer",
        "description": "Synthesizer triages incoming user intent."
    },
    {
        "id": "trigger-task-assigned",
        "event_type": "task_assigned",
        "condition": "always",
        "activates": "{{payload.target_agent}}",
        "description": "Route task to specified agent."
    }
  ]
}

triggers_path.parent.mkdir(parents=True, exist_ok=True)
triggers_path.write_text(json.dumps(content, indent=2))
print("✅ Updated triggers.json with v2.2 (Added user_intent and task_assigned)")
