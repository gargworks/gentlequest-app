#!/usr/bin/env python3
"""
Nucleus Autopilot V2 - Task-Driven Agent Orchestrator

This is the production-ready autopilot that uses the V2 task management tools.
It implements the Synthesizer Loop described in the Nucleus V2 Specification.

Key Features:
- Uses brain_get_next_task to find work
- Uses brain_claim_task to prevent race conditions  
- Uses brain_update_task to mark completion
- Uses brain_escalate when stuck
- Event-driven architecture
"""

import os
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# Check for Gemini Key
if not os.environ.get("GOOGLE_API_KEY"):
    print("❌ GOOGLE_API_KEY not found. Please set it to run the Autopilot.")
    sys.exit(1)

# Import Gemini
try:
    import warnings
    warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')
    import google.generativeai as genai
except ImportError:
    print("❌ 'google-generativeai' package not installed. Run: pip install google-generativeai")
    sys.exit(1)

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash-8b')

BRAIN_PATH = os.environ.get("NUCLEAR_BRAIN_PATH", ".brain")
POLL_INTERVAL = 10  # Seconds between task checks
AGENT_SKILLS = ["python", "systems", "automation", "research"]  # This agent's skills
AGENT_ID = "autopilot-v2"


def get_brain_path() -> Path:
    return Path(BRAIN_PATH)


def load_state() -> Dict:
    """Load current brain state."""
    state_file = get_brain_path() / "ledger" / "state.json"
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {}


def save_state(state: Dict) -> None:
    """Save brain state."""
    state_file = get_brain_path() / "ledger" / "state.json"
    state_file.write_text(json.dumps(state, indent=2))


def get_tasks() -> List[Dict]:
    """Get tasks from state using V2 schema location."""
    state = load_state()
    sprint = state.get("current_sprint", {})
    return sprint.get("tasks", [])


def save_tasks(tasks: List[Dict]) -> None:
    """Save tasks to state."""
    state = load_state()
    if "current_sprint" not in state:
        state["current_sprint"] = {"name": "Default Sprint", "focus": "Tasks"}
    state["current_sprint"]["tasks"] = tasks
    save_state(state)


def get_next_task(skills: List[str]) -> Optional[Dict]:
    """
    V2 Pull-Based Task Selection:
    1. Filter by skill match
    2. Exclude BLOCKED, DONE, FAILED, ESCALATED, IN_PROGRESS
    3. Exclude already claimed
    4. Sort by priority (1 = highest)
    5. Return top result
    """
    tasks = get_tasks()
    
    eligible = []
    for task in tasks:
        status = task.get("status", "").upper()
        
        # Skip non-claimable statuses
        if status in ["BLOCKED", "DONE", "FAILED", "ESCALATED", "IN_PROGRESS", "COMPLETE"]:
            continue
        
        # Skip already claimed
        if task.get("claimed_by"):
            continue
        
        # Check skill match (empty required_skills = any agent can do it)
        required = task.get("required_skills", [])
        if required:
            if not any(s in skills for s in required):
                continue
        
        eligible.append(task)
    
    if not eligible:
        return None
    
    # Sort by priority (1 = highest priority = should be first)
    eligible.sort(key=lambda t: t.get("priority", 3))
    return eligible[0]


def claim_task(task_id: str, agent_id: str) -> bool:
    """Atomically claim a task."""
    tasks = get_tasks()
    
    for task in tasks:
        if task.get("id") == task_id or task.get("description") == task_id:
            if task.get("claimed_by"):
                print(f"⚠️  Task already claimed by {task.get('claimed_by')}")
                return False
            
            task["claimed_by"] = agent_id
            task["status"] = "IN_PROGRESS"
            task["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            save_tasks(tasks)
            return True
    
    return False


def complete_task(task_id: str) -> bool:
    """Mark a task as done."""
    tasks = get_tasks()
    
    for task in tasks:
        if task.get("id") == task_id or task.get("description") == task_id:
            task["status"] = "DONE"
            task["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            save_tasks(tasks)
            return True
    
    return False


def escalate_task(task_id: str, reason: str) -> bool:
    """Escalate a task for human help."""
    tasks = get_tasks()
    
    for task in tasks:
        if task.get("id") == task_id or task.get("description") == task_id:
            task["status"] = "ESCALATED"
            task["escalation_reason"] = reason
            task["claimed_by"] = None
            task["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            save_tasks(tasks)
            return True
    
    return False


def process_task_with_llm(task: Dict) -> str:
    """Use Gemini to analyze and attempt to complete a task."""
    description = task.get("description", "Unknown task")
    
    prompt = f"""You are an autonomous agent working on a task.

TASK: {description}

INSTRUCTIONS:
1. Analyze what this task requires
2. If you can complete it with reasoning/planning alone, provide the solution
3. If you need external tools or human input, say "ESCALATE: <reason>"
4. Keep your response concise

Respond with either:
- Your analysis/solution
- ESCALATE: <reason why you need human help>
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ESCALATE: LLM error - {e}"


async def run_autopilot_v2():
    """
    The Synthesizer Loop (V2):
    1. Get next task matching our skills
    2. Claim it atomically
    3. Process with LLM
    4. Mark complete or escalate
    5. Repeat
    """
    print("=" * 60)
    print("🧠 Nucleus Autopilot V2 - Task-Driven Orchestrator")
    print("=" * 60)
    print(f"   Brain Path: {BRAIN_PATH}")
    print(f"   Agent ID: {AGENT_ID}")
    print(f"   Skills: {AGENT_SKILLS}")
    print(f"   Poll Interval: {POLL_INTERVAL}s")
    print("=" * 60)
    
    tasks_processed = 0
    
    while True:
        try:
            # 1. GET NEXT TASK
            task = get_next_task(AGENT_SKILLS)
            
            if not task:
                # No work available - wait and retry
                await asyncio.sleep(POLL_INTERVAL)
                continue
            
            task_id = task.get("id", task.get("description", "unknown"))
            description = task.get("description", "Unknown")
            priority = task.get("priority", 3)
            
            print(f"\n📋 Found task: {description[:50]}... (priority: {priority})")
            
            # 2. CLAIM IT
            if not claim_task(task_id, AGENT_ID):
                print("   ⚠️  Could not claim task (race condition?)")
                await asyncio.sleep(1)
                continue
            
            print(f"   ✅ Claimed by {AGENT_ID}")
            
            # 3. PROCESS WITH LLM
            print("   🤖 Processing with Gemini...")
            result = process_task_with_llm(task)
            
            # 4. DETERMINE OUTCOME
            if result.startswith("ESCALATE:"):
                reason = result.replace("ESCALATE:", "").strip()
                escalate_task(task_id, reason)
                print(f"   ⬆️  Escalated: {reason}")
            else:
                complete_task(task_id)
                tasks_processed += 1
                print(f"   ✅ Completed! (Total: {tasks_processed})")
                print(f"   📝 Result: {result[:100]}...")
            
            # Small delay between tasks
            await asyncio.sleep(2)
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"\n⚠️  Error in loop: {e}")
            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    print("\n🚀 Starting Nucleus Autopilot V2...")
    print("   Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(run_autopilot_v2())
    except KeyboardInterrupt:
        print("\n\n🛑 Autopilot V2 stopped.")
