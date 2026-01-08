#!/usr/bin/env python3
"""
Nucleus Meta-Optimizer
=======================
The 72-hour self-improvement loop per synthesizer.md protocol.

This script:
1. MEASURE - Read performance metrics
2. ANALYZE - Identify low-efficiency agents
3. HYPOTHESIZE - Generate improvement ideas
4. MODIFY - Update agent prompts (with rollback capability)
5. VALIDATE - Compare metrics after next cycle
6. DOCUMENT - Log to optimization_log.md

Run via cron: 0 0 */3 * * /path/to/scripts/run_meta_optimizer.sh

Location: scripts/meta_optimizer.py
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
SERVER_SRC = PROJECT_ROOT / "mcp-server-nucleus" / "src"
sys.path.insert(0, str(SERVER_SRC))

from mcp_server_nucleus.runtime.event_stream import emit_event, EventSeverity, EventTypes

# Configuration
BRAIN_PATH = Path(os.environ.get("NUCLEUS_BRAIN_PATH", PROJECT_ROOT / ".brain"))


def get_performance_path() -> Path:
    """Path to performance metrics"""
    return BRAIN_PATH / "meta" / "performance.json"


def get_optimization_log_path() -> Path:
    """Path to optimization log"""
    return BRAIN_PATH / "meta" / "optimization_log.md"


def load_performance() -> dict:
    """Load current performance metrics"""
    path = get_performance_path()
    if path.exists():
        return json.loads(path.read_text())
    
    # Initialize default metrics
    return {
        "agents": {},
        "overall": {
            "success_rate": 0.0,
            "avg_time_seconds": 0,
            "escalation_rate": 0.0
        },
        "last_updated": None
    }


def save_performance(metrics: dict) -> None:
    """Save performance metrics"""
    path = get_performance_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    metrics["last_updated"] = datetime.now().isoformat()
    path.write_text(json.dumps(metrics, indent=2))


def measure() -> dict:
    """
    STEP 1: MEASURE
    Calculate current performance metrics from event stream.
    """
    from mcp_server_nucleus.runtime.event_stream import read_events
    
    events = read_events(BRAIN_PATH, limit=200)
    
    # Count by agent
    agent_stats = {}
    for event in events:
        emitter = event.get("emitter", "unknown")
        event_type = event.get("event_type", "unknown")
        
        if emitter not in agent_stats:
            agent_stats[emitter] = {"completed": 0, "failed": 0, "escalated": 0}
        
        if "complete" in event_type.lower():
            agent_stats[emitter]["completed"] += 1
        elif "fail" in event_type.lower():
            agent_stats[emitter]["failed"] += 1
        elif "escalat" in event_type.lower():
            agent_stats[emitter]["escalated"] += 1
    
    # Calculate rates
    for agent, stats in agent_stats.items():
        total = stats["completed"] + stats["failed"]
        if total > 0:
            stats["success_rate"] = stats["completed"] / total
            stats["escalation_rate"] = stats["escalated"] / total
        else:
            stats["success_rate"] = 0.0
            stats["escalation_rate"] = 0.0
    
    return agent_stats


def analyze(agent_stats: dict) -> list:
    """
    STEP 2: ANALYZE
    Identify low-efficiency agents and problem patterns.
    """
    issues = []
    
    for agent, stats in agent_stats.items():
        # Low success rate
        if stats.get("success_rate", 1.0) < 0.7:
            issues.append({
                "agent": agent,
                "issue": "low_success_rate",
                "value": stats.get("success_rate", 0),
                "severity": "high"
            })
        
        # High escalation rate
        if stats.get("escalation_rate", 0) > 0.3:
            issues.append({
                "agent": agent,
                "issue": "high_escalation_rate",
                "value": stats.get("escalation_rate", 0),
                "severity": "medium"
            })
    
    return issues


def hypothesize(issues: list) -> list:
    """
    STEP 3: HYPOTHESIZE
    Generate improvement ideas for identified issues.
    """
    hypotheses = []
    
    for issue in issues:
        if issue["issue"] == "low_success_rate":
            hypotheses.append({
                "agent": issue["agent"],
                "hypothesis": "Add more explicit tool usage examples to prompt",
                "expected_impact": "Increase success rate by 20%",
                "action": "modify_prompt"
            })
        
        elif issue["issue"] == "high_escalation_rate":
            hypotheses.append({
                "agent": issue["agent"],
                "hypothesis": "Expand autonomous action criteria",
                "expected_impact": "Reduce escalation rate by 15%",
                "action": "modify_constraints"
            })
    
    return hypotheses


def modify(hypotheses: list) -> list:
    """
    STEP 4: MODIFY
    Apply recommended changes (with rollback markers).
    
    NOTE: This is conservative - it logs recommendations rather than
    automatically modifying prompts. Human approval required for actual changes.
    """
    modifications = []
    
    for hyp in hypotheses:
        # Log the recommendation (don't auto-modify without approval)
        modifications.append({
            "agent": hyp["agent"],
            "recommendation": hyp["hypothesis"],
            "status": "pending_approval",
            "timestamp": datetime.now().isoformat()
        })
    
    return modifications


def document(agent_stats: dict, issues: list, hypotheses: list, modifications: list) -> str:
    """
    STEP 6: DOCUMENT
    Write optimization log entry.
    """
    log_path = get_optimization_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    entry = f"""
---

## Meta-Optimization: {datetime.now().strftime('%Y-%m-%d %H:%M')}

### Performance Summary
| Agent | Success Rate | Escalation Rate | Events |
|:------|:-------------|:----------------|:-------|
"""
    
    for agent, stats in agent_stats.items():
        total = stats.get("completed", 0) + stats.get("failed", 0)
        entry += f"| {agent} | {stats.get('success_rate', 0):.1%} | {stats.get('escalation_rate', 0):.1%} | {total} |\n"
    
    entry += f"""
### Issues Identified ({len(issues)})
"""
    
    for issue in issues:
        entry += f"- **{issue['agent']}**: {issue['issue']} ({issue['value']:.1%})\n"
    
    if not issues:
        entry += "_No issues identified._\n"
    
    entry += f"""
### Recommendations ({len(hypotheses)})
"""
    
    for hyp in hypotheses:
        entry += f"- **{hyp['agent']}**: {hyp['hypothesis']}\n"
    
    if not hypotheses:
        entry += "_No recommendations at this time._\n"
    
    entry += """
### Actions Taken
"""
    
    for mod in modifications:
        entry += f"- {mod['agent']}: {mod['recommendation']} [{mod['status']}]\n"
    
    if not modifications:
        entry += "_No modifications applied._\n"
    
    # Append to log
    existing = log_path.read_text() if log_path.exists() else "# Nucleus Meta-Optimization Log\n"
    log_path.write_text(existing + entry)
    
    return entry


def run_meta_optimizer():
    """Main meta-optimization loop"""
    print("=" * 60)
    print(f"NUCLEUS META-OPTIMIZER - {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Step 1: MEASURE
    print("\n📊 Step 1: MEASURE")
    agent_stats = measure()
    print(f"   Analyzed {len(agent_stats)} agents")
    
    # Step 2: ANALYZE
    print("\n🔍 Step 2: ANALYZE")
    issues = analyze(agent_stats)
    print(f"   Found {len(issues)} issues")
    
    # Step 3: HYPOTHESIZE
    print("\n💡 Step 3: HYPOTHESIZE")
    hypotheses = hypothesize(issues)
    print(f"   Generated {len(hypotheses)} recommendations")
    
    # Step 4: MODIFY (conservative - log only)
    print("\n🔧 Step 4: MODIFY (pending approval)")
    modifications = modify(hypotheses)
    
    # Step 5: VALIDATE (next cycle)
    print("\n✅ Step 5: VALIDATE (deferred to next cycle)")
    
    # Step 6: DOCUMENT
    print("\n📝 Step 6: DOCUMENT")
    entry = document(agent_stats, issues, hypotheses, modifications)
    print(f"   Logged to optimization_log.md")
    
    # Update performance metrics
    perf = load_performance()
    perf["agents"] = agent_stats
    save_performance(perf)
    
    # Emit completion event
    emit_event(
        brain_path=BRAIN_PATH,
        event_type=EventTypes.META_OPTIMIZATION_COMPLETE,
        emitter="meta_optimizer",
        payload={
            "agents_analyzed": len(agent_stats),
            "issues_found": len(issues),
            "recommendations": len(hypotheses)
        },
        severity=EventSeverity.NOTABLE
    )
    
    print("\n" + "=" * 60)
    print("META-OPTIMIZER COMPLETE")
    print("=" * 60)
    
    # Print summary
    print(f"\n📋 SUMMARY:")
    print(f"   Issues: {len(issues)}")
    print(f"   Recommendations: {len(hypotheses)}")
    print(f"   Status: Pending human approval for modifications")


if __name__ == "__main__":
    run_meta_optimizer()
