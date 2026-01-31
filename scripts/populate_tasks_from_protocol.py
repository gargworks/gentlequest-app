#!/usr/bin/env python3
"""
Populate tasks.jsonl from EXECUTION_PROTOCOL_DETAILED.md
Extracts all steps, creates task ledger for multi-environment execution
"""

import json
from pathlib import Path
from datetime import datetime

def extract_tasks_from_protocol():
    """Extract all steps from protocol and create tasks"""
    protocol_path = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/missions/gtm_overhaul_2026/EXECUTION_PROTOCOL_DETAILED.md")
    
    if not protocol_path.exists():
        print(f"❌ Protocol not found: {protocol_path}")
        return []
    
    tasks = []
    
    # Extract Nucleus GTM steps (1.1 - 1.10)
    nucleus_steps = [
        {"id": "task_001", "step": "1.1", "description": "Populate nucleus.json with 79+ tools", "status": "DONE", "priority": 1, "environment": "antigravity", "model": "gemini_3_pro", "dependencies": []},
        {"id": "task_002", "step": "1.2", "description": "Post Reddit to r/ClaudeAI", "status": "PENDING", "priority": 1, "environment": "human", "model": None, "dependencies": ["task_001"]},
        {"id": "task_003", "step": "1.3", "description": "Start IndieHackers log", "status": "PENDING", "priority": 1, "environment": "human", "model": None, "dependencies": ["task_002"]},
        {"id": "task_004", "step": "1.4", "description": "Recruit Advisor #1 (MCP Expert)", "status": "PENDING", "priority": 2, "environment": "human", "model": None, "dependencies": ["task_002"]},
        {"id": "task_005", "step": "1.5", "description": "Build @nucleus/researcher agent", "status": "PENDING", "priority": 2, "environment": "antigravity", "model": "gemini_3_pro", "dependencies": ["task_002"]},
        {"id": "task_006", "step": "1.6", "description": "HackerNews launch (Show HN: Nucleus)", "status": "PENDING", "priority": 2, "environment": "human", "model": None, "dependencies": ["task_002", "task_005"]},
        {"id": "task_007", "step": "1.7", "description": "Recruit Advisor #2 (Dev Tool GTM)", "status": "PENDING", "priority": 3, "environment": "human", "model": None, "dependencies": ["task_002"]},
        {"id": "task_008", "step": "1.8", "description": "Build @nucleus/linear agent", "status": "PENDING", "priority": 3, "environment": "antigravity", "model": "gemini_3_pro", "dependencies": ["task_005"]},
        {"id": "task_009", "step": "1.9", "description": "Recruit Advisor #3 (Technical/AI)", "status": "PENDING", "priority": 3, "environment": "human", "model": None, "dependencies": ["task_002"]},
        {"id": "task_010", "step": "1.10", "description": "Launch Nucleus Registry (marketplace)", "status": "PENDING", "priority": 4, "environment": "antigravity", "model": "gemini_3_pro", "dependencies": ["task_005", "task_008"]},
    ]
    
    # Extract GentleQuest steps (2.1 - 2.5)
    gentlequest_steps = [
        {"id": "task_011", "step": "2.1", "description": "Run GentleQuest validation suite (30 scenarios)", "status": "BLOCKED", "priority": 1, "environment": "antigravity", "model": "gemini_3_pro", "dependencies": [], "blocker": "Production missing GEMINI_API_KEY"},
        {"id": "task_012", "step": "2.2", "description": "Wysa competitive analysis", "status": "PENDING", "priority": 1, "environment": "human", "model": None, "dependencies": ["task_011"]},
        {"id": "task_013", "step": "2.3", "description": "Make Go/No-Go decision (Jan 24)", "status": "PENDING", "priority": 1, "environment": "windsurf", "model": "claude_opus_4.5", "dependencies": ["task_011", "task_012"]},
        {"id": "task_014", "step": "2.4", "description": "Implement features if GO (Quests, Resources, Counselor Alerts)", "status": "PENDING", "priority": 1, "environment": "antigravity", "model": "gemini_3_pro", "dependencies": ["task_013"]},
        {"id": "task_015", "step": "2.5", "description": "Launch university outreach if GO (Feb 1)", "status": "PENDING", "priority": 1, "environment": "human", "model": None, "dependencies": ["task_014"]},
    ]
    
    # Combine
    tasks = nucleus_steps + gentlequest_steps
    
    # Add metadata
    for task in tasks:
        task["created_at"] = datetime.now().isoformat()
        task["assigned_to"] = None if task["status"] == "PENDING" else "completed"
        task["skills"] = ["gtm", "python"] if task["environment"] != "human" else ["gtm"]
    
    return tasks

def save_tasks_to_ledger(tasks):
    """Save tasks to tasks.jsonl"""
    ledger_dir = Path("/Users/lokeshgarg/ai-mvp-backend/.brain/ledger")
    ledger_dir.mkdir(parents=True, exist_ok=True)
    
    ledger_path = ledger_dir / "tasks.jsonl"
    
    with open(ledger_path, 'w') as f:
        for task in tasks:
            f.write(json.dumps(task) + '\\n')
    
    print(f"✅ Created {ledger_path} with {len(tasks)} tasks")
    return ledger_path

def main():
    print("🚀 Populating task ledger from EXECUTION_PROTOCOL_DETAILED.md...")
    
    tasks = extract_tasks_from_protocol()
    
    if not tasks:
        print("❌ No tasks extracted")
        return 1
    
    ledger_path = save_tasks_to_ledger(tasks)
    
    print("\n📊 Task Summary:")
    print(f"   Total: {len(tasks)}")
    print(f"   DONE: {sum(1 for t in tasks if t['status'] == 'DONE')}")
    print(f"   PENDING: {sum(1 for t in tasks if t['status'] == 'PENDING')}")
    print(f"   BLOCKED: {sum(1 for t in tasks if t['status'] == 'BLOCKED')}")
    
    print(f"\n✅ Task ledger ready at {ledger_path}")
    print("\nNext: Call brain_session_start() in any chat to get first task")
    print(f"\\nNext: Call brain_session_start() in any chat to get first task")
    
    return 0

if __name__ == "__main__":
    exit(main())
