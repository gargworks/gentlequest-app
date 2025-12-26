#!/usr/bin/env python3
"""
Nuclear Brain Bootstrap Script
==============================
Initializes the .brain/ directory structure for Level 5 Autonomy operations.

Usage:
    python brain_bootstrap.py [--reset] [--flywheel]
    
Options:
    --reset      Wipe existing .brain/ and reinitialize (WARNING: destructive)
    --flywheel   After bootstrap, start the agent manager flywheel
    
This script is TOOL-AGNOSTIC. All intelligence resides in the files, not memory.

Flywheel Mode (Set-and-Forget):
    1. python brain_bootstrap.py             # Initialize brain
    2. python agent_manager.py sprint "Goal" # Set sprint goal
    3. python agent_manager.py start         # Start flywheel
    4. ... system runs autonomously ...
    5. Review digests in .brain/artifacts/synthesis/
"""

import os
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

BRAIN_ROOT = Path(__file__).parent / ".brain"

DIRECTORY_STRUCTURE = [
    "ledger",
    "agents",
    "memory",
    "artifacts/strategy",
    "artifacts/architecture", 
    "artifacts/code",
    "artifacts/reviews",
    "artifacts/research",
    "artifacts/synthesis",
    "workflows",
    "meta",
    "activations",  # NEW: For automated agent activation files
]

# ============================================================================
# SCHEMA DEFINITIONS
# ============================================================================

def get_initial_state():
    """Initial state.json schema"""
    return {
        "version": "2025.Final",
        "architecture": "Nuclear",
        "initialized": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "active_agents": [],
        "pending_events": [],
        "founder_queue": [],
        "current_sprint": None,
        "meta": {
            "last_optimization": None,
            "optimization_cycle_hours": 72,
            "auto_approval_enabled": True,
            "escalation_threshold": "CRITICAL"
        },
        "counters": {
            "total_events": 0,
            "total_tasks": 0,
            "auto_approvals": 0,
            "founder_decisions": 0
        }
    }


def get_trigger_definitions():
    """Neural trigger definitions"""
    return {
        "version": "1.0",
        "triggers": [
            {
                "id": "strategy_to_architect",
                "event_type": "strategy_updated",
                "emitter": "strategist",
                "activates": ["architect", "synthesizer"],
                "condition": {"type": "always"},
                "priority": "HIGH",
                "description": "Roadmap changes require architecture review"
            },
            {
                "id": "spec_to_developer",
                "event_type": "spec_ready_for_development",
                "emitter": "architect",
                "activates": ["developer"],
                "condition": {"type": "always"},
                "priority": "HIGH",
                "description": "Technical spec ready for implementation"
            },
            {
                "id": "code_to_critic",
                "event_type": "implementation_complete",
                "emitter": "developer",
                "activates": ["critic"],
                "condition": {"type": "always"},
                "priority": "HIGH",
                "description": "Code ready for quality review"
            },
            {
                "id": "review_approved",
                "event_type": "review_approved",
                "emitter": "critic",
                "activates": ["synthesizer"],
                "condition": {"type": "always"},
                "priority": "MEDIUM",
                "description": "Quality gate passed, ready for synthesis"
            },
            {
                "id": "review_blocked",
                "event_type": "review_blocked",
                "emitter": "critic",
                "activates": ["developer"],
                "condition": {"type": "severity_gte", "value": "HIGH"},
                "priority": "CRITICAL",
                "description": "Quality gate failed, requires fix"
            },
            {
                "id": "market_intelligence",
                "event_type": "market_shift_detected",
                "emitter": "researcher",
                "activates": ["strategist"],
                "condition": {"type": "always"},
                "priority": "HIGH",
                "description": "Competitive intelligence requiring strategy review"
            },
            {
                "id": "founder_escalation",
                "event_type": "founder_decision_needed",
                "emitter": "*",
                "activates": ["synthesizer"],
                "condition": {"type": "severity_eq", "value": "CRITICAL"},
                "priority": "CRITICAL",
                "description": "Human decision required"
            },
            {
                "id": "meta_optimization",
                "event_type": "meta_optimization_complete",
                "emitter": "synthesizer",
                "activates": ["*"],
                "condition": {"type": "always"},
                "priority": "LOW",
                "description": "System prompts updated, all agents notified"
            },
            {
                "id": "sprint_started",
                "event_type": "sprint_started",
                "emitter": "synthesizer",
                "activates": ["strategist", "researcher"],
                "condition": {"type": "always"},
                "priority": "HIGH",
                "description": "New sprint initiated"
            },
            {
                "id": "daily_digest",
                "event_type": "daily_digest_generated",
                "emitter": "synthesizer",
                "activates": [],
                "condition": {"type": "schedule", "cron": "0 6 * * *"},
                "priority": "MEDIUM",
                "description": "Daily founder digest ready"
            }
        ]
    }


def get_event_schema():
    """Event schema documentation"""
    return {
        "_schema_version": "1.0",
        "_description": "Schema for events in events.jsonl",
        "event": {
            "event_id": "uuid-v4",
            "timestamp": "ISO8601 UTC",
            "emitter": "agent_name | system",
            "event_type": "string (matches trigger event_type)",
            "severity": "ROUTINE | NOTABLE | CRITICAL",
            "payload": {
                "_note": "Event-specific data"
            },
            "metadata": {
                "task_id": "optional reference",
                "parent_event": "optional chain reference",
                "ttl_hours": "optional expiry"
            }
        },
        "example": {
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "timestamp": "2025-12-26T21:44:00Z",
            "emitter": "developer",
            "event_type": "implementation_complete",
            "severity": "NOTABLE",
            "payload": {
                "feature": "function_calling",
                "files_changed": ["providers/gemini.py", "providers/agent_tools.py"],
                "tests_passed": True
            },
            "metadata": {
                "task_id": "task-001",
                "parent_event": None
            }
        }
    }


def get_initial_performance():
    """Initial performance metrics"""
    agents = ["strategist", "architect", "developer", "critic", "researcher", "synthesizer"]
    return {
        "initialized": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "agents": {
            agent: {
                "tasks_completed": 0,
                "success_rate": None,
                "avg_time_minutes": None,
                "escalation_rate": None,
                "rework_rate": None,
                "last_active": None
            }
            for agent in agents
        },
        "system": {
            "total_events": 0,
            "handoff_efficiency": None,
            "founder_interrupts": 0,
            "auto_approvals": 0,
            "optimization_cycles": 0
        }
    }


# ============================================================================
# MARKDOWN CONTENT GENERATORS
# ============================================================================

def get_decisions_md():
    return f"""# Decision Log

> All significant decisions made by the agentic system.
> Format: [DATE] [AGENT] [SEVERITY] - Decision

---

## {datetime.now().strftime('%Y-%m-%d')}

### System Initialization
- **Agent:** System
- **Severity:** ROUTINE
- **Decision:** Nuclear Brain initialized via bootstrap script
- **Outcome:** Ready for first sprint

---

*This log is append-only. Managed by Synthesizer.*
"""


def get_context_md():
    return """# GentleQuest - Persistent Context

> Shared context for ALL agents. Single source of truth.

---

## Identity

| Field | Value |
|-------|-------|
| **Name** | GentleQuest |
| **Tagline** | Progress Without Pressure |
| **Domain** | AI Mental Health Companion |
| **Stage** | MVP with AI Agent Capabilities |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python/Flask on Render |
| Database | PostgreSQL + pgvector |
| AI | Gemini API with Function Calling |
| Mobile | Flutter (iOS, Android, Web) |
| Memory | Session + RAG (emerging) |

---

## Strategic Position

**Moat:** Orchestration Logic > Product Features

**Differentiation:**
1. Luna ACTS (function calling)
2. Luna REMEMBERS (RAG memory)
3. Luna LEARNS (patterns)

---

## Current Phase

- [x] Phase 1: Function Calling
- [ ] Phase 2: RAG/Memory
- [ ] Phase 3: Clinical Assessments

---

*Updated by Synthesizer during memory curation*
"""


def get_patterns_md():
    return """# Discovered Patterns

> Patterns for agent decision-making.

---

## Core Patterns

### Artifact First
Write to ledger before explaining. Persistence > conversation.

### Batch Over Individual  
Generate 5-10 variants, select best 2-3. Quality through selection.

### Native Over Framework
Prefer Gemini API over LangChain. Simplicity wins.

### Actions Over Advice
Luna should DO things, not just SAY things.

---

*Updated by Synthesizer*
"""


def get_learnings_md():
    return f"""# Learnings Archive

> Institutional memory of what worked and what didn't.

---

## {datetime.now().strftime('%Y-%m-%d')}: Bootstrap

**Learning:** Tool-agnostic architecture enables portability
**What Worked:** All logic in files, not AI memory
**Action:** Initialized Nuclear Brain structure

---

*Append-only log. Archive monthly.*
"""


def get_optimization_log():
    return f"""# Optimization Log

> Self-improvement cycle records.

---

## {datetime.now().strftime('%Y-%m-%d')}: Cycle 0 (Initialization)

**Triggered By:** Bootstrap script
**Changes:** Initial structure created
**Next Cycle:** 72 hours

---

*Managed by Synthesizer*
"""


def get_next_iteration():
    return """# Next Iteration Plan

> Improvements for next optimization cycle.

---

## Planned (Next 72h)

1. Establish baseline metrics
2. Run first Subatomic Sprint
3. Measure agent performance

---

*Updated by Synthesizer*
"""


# ============================================================================
# BOOTSTRAP FUNCTIONS
# ============================================================================

def create_directory_structure():
    """Create the .brain/ directory tree"""
    print("📁 Creating directory structure...")
    
    for subdir in DIRECTORY_STRUCTURE:
        path = BRAIN_ROOT / subdir
        path.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {subdir}/")
    
    print()


def write_json_file(path: Path, data: dict, description: str):
    """Write a JSON file with pretty printing"""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"   ✓ {path.name} ({description})")


def write_md_file(path: Path, content: str, description: str):
    """Write a Markdown file"""
    with open(path, 'w') as f:
        f.write(content)
    print(f"   ✓ {path.name} ({description})")


def write_jsonl_file(path: Path, initial_event: dict, description: str):
    """Write initial event to JSONL file"""
    with open(path, 'w') as f:
        f.write(json.dumps(initial_event) + '\n')
    print(f"   ✓ {path.name} ({description})")


def initialize_ledger():
    """Initialize the ledger/ directory"""
    print("📊 Initializing Ledger (Nervous System)...")
    
    ledger = BRAIN_ROOT / "ledger"
    
    # state.json
    write_json_file(ledger / "state.json", get_initial_state(), "system state")
    
    # triggers.json
    write_json_file(ledger / "triggers.json", get_trigger_definitions(), "neural triggers")
    
    # event_schema.json (documentation)
    write_json_file(ledger / "event_schema.json", get_event_schema(), "event schema docs")
    
    # events.jsonl with bootstrap event
    bootstrap_event = {
        "event_id": "bootstrap-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "emitter": "system",
        "event_type": "brain_initialized",
        "severity": "NOTABLE",
        "payload": {"version": "2025.Final", "method": "bootstrap_script"},
        "metadata": {}
    }
    write_jsonl_file(ledger / "events.jsonl", bootstrap_event, "event stream")
    
    # decisions.md
    write_md_file(ledger / "decisions.md", get_decisions_md(), "decision log")
    
    print()


def initialize_memory():
    """Initialize the memory/ directory"""
    print("🧠 Initializing Memory (Institutional Knowledge)...")
    
    memory = BRAIN_ROOT / "memory"
    
    write_md_file(memory / "context.md", get_context_md(), "shared context")
    write_md_file(memory / "patterns.md", get_patterns_md(), "discovered patterns")
    write_md_file(memory / "learnings.md", get_learnings_md(), "learnings archive")
    
    print()


def initialize_meta():
    """Initialize the meta/ directory"""
    print("🔄 Initializing Meta (Self-Improvement Layer)...")
    
    meta = BRAIN_ROOT / "meta"
    
    write_json_file(meta / "performance.json", get_initial_performance(), "performance metrics")
    write_md_file(meta / "optimization_log.md", get_optimization_log(), "optimization history")
    write_md_file(meta / "next_iteration.md", get_next_iteration(), "improvement plan")
    
    print()


def print_summary():
    """Print bootstrap summary"""
    print("=" * 60)
    print("🔥 NUCLEAR BRAIN BOOTSTRAP COMPLETE")
    print("=" * 60)
    print()
    print(f"📍 Brain Location: {BRAIN_ROOT.absolute()}")
    print()
    print("📂 Structure Created:")
    print("   .brain/")
    print("   ├── ledger/      → Nervous system (state, events, triggers)")
    print("   ├── agents/      → Agent system prompts")
    print("   ├── memory/      → Institutional knowledge")
    print("   ├── artifacts/   → Cross-agent outputs")
    print("   ├── workflows/   → Automated workflows")
    print("   └── meta/        → Self-improvement")
    print()
    print("🚀 Next Steps:")
    print("   1. Copy Synthesizer prompt to .brain/agents/synthesizer.md")
    print("   2. Run: Synthesizer, digest the docs and start first sprint")
    print()


def reset_brain():
    """Remove existing .brain/ directory"""
    import shutil
    if BRAIN_ROOT.exists():
        print(f"⚠️  Removing existing .brain/ at {BRAIN_ROOT}")
        shutil.rmtree(BRAIN_ROOT)
        print("   ✓ Removed")
        print()


# ============================================================================
# MAIN
# ============================================================================

def main():
    print()
    print("=" * 60)
    print("🔥 NUCLEAR BRAIN BOOTSTRAP SCRIPT")
    print("   Version: 2025.Final | Level 5 Autonomy")
    print("=" * 60)
    print()
    
    # Handle --reset flag
    if "--reset" in sys.argv:
        reset_brain()
    
    # Check if already exists
    if BRAIN_ROOT.exists() and any(BRAIN_ROOT.iterdir()):
        print(f"⚠️  .brain/ already exists at {BRAIN_ROOT}")
        print("   Use --reset to reinitialize (WARNING: destructive)")
        print()
        sys.exit(1)
    
    # Run bootstrap
    create_directory_structure()
    initialize_ledger()
    initialize_memory()
    initialize_meta()
    print_summary()


if __name__ == "__main__":
    main()
