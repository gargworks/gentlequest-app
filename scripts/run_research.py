#!/usr/bin/env python3
"""
Research Queue Processor - Execute queued research tasks via Gemini CLI

Usage:
    python scripts/run_research.py           # Process all pending tasks
    python scripts/run_research.py --dry-run # Preview without executing

This script:
1. Reads pending tasks from .brain/artifacts/research/queue.md
2. Executes each via Gemini CLI with project context
3. Saves results to .brain/artifacts/research/
4. Marks tasks as complete in queue
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime, timezone

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
BRAIN_PATH = PROJECT_ROOT / ".brain"
QUEUE_FILE = BRAIN_PATH / "artifacts" / "research" / "queue.md"
OUTPUT_DIR = BRAIN_PATH / "artifacts" / "research"
CONTEXT_FILE = BRAIN_PATH / "memory" / "context.md"

# Gemini model (premium)
MODEL = "gemini-2.0-flash-exp"


def get_pending_tasks() -> list[tuple[str, str]]:
    """Read pending (unchecked) tasks from queue.md.
    
    Returns list of (timestamp, task_description) tuples.
    """
    if not QUEUE_FILE.exists():
        return []
    
    content = QUEUE_FILE.read_text()
    pending = []
    
    # Match: - [ ] YYYY-MM-DD HH:MM | Task description
    pattern = r"- \[ \] (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) \| (.+)"
    for match in re.finditer(pattern, content):
        timestamp, task = match.groups()
        pending.append((timestamp, task.strip()))
    
    return pending


def mark_task_complete(task_desc: str):
    """Mark a task as complete in queue.md ([ ] -> [x])."""
    content = QUEUE_FILE.read_text()
    # Escape special regex chars in task description
    escaped_task = re.escape(task_desc)
    pattern = rf"- \[ \] (\d{{4}}-\d{{2}}-\d{{2}} \d{{2}}:\d{{2}}) \| {escaped_task}"
    replacement = rf"- [x] \1 | {task_desc}"
    new_content = re.sub(pattern, replacement, content)
    QUEUE_FILE.write_text(new_content)


# Ensure mcp-server-nucleus is in path
CURRENT_DIR = Path(__file__).parent
SERVER_SRC = CURRENT_DIR.parent / "mcp-server-nucleus" / "src"
sys.path.append(str(SERVER_SRC))

try:
    from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
except ImportError:
    print("❌ Failed to import Nucleus Runtime (DualEngineLLM). Check paths.")
    sys.exit(1)


def run_gemini_research(task: str) -> tuple[str, bool]:
    """Execute research task via DualEngineLLM (Python SDK).
    
    Returns (output, success).
    """
    prompt = f"""You are a research assistant for a solo founder building GentleQuest (mental health app).

Research Task: {task}

Context: Use project knowledge to make this research actionable and specific.
Output: Provide a concise, well-structured research report with:
1. Key findings (bullet points)
2. Recommendations
3. Sources/references if applicable

Be thorough but concise. Focus on actionable insights."""

    # Add context content to prompt
    context_text = ""
    if CONTEXT_FILE.exists():
        try:
            context_text = CONTEXT_FILE.read_text()
            prompt += f"\n\nProject Context:\n{context_text}"
        except Exception:
            pass # Ignore context read errors

    try:
        # Initialize Dual-Engine (New API -> Legacy Fallback)
        llm = DualEngineLLM(MODEL)
        
        # DualEngineLLM.generate_content returns a simple object with .text (or similar unified interface)
        # Based on my implementation of DualEngineLLM, it returns an object with .text
        response = llm.generate_content(prompt)
        
        return response.text, True
            
    except Exception as e:
        return f"Error executing research: {str(e)}", False


def save_research_result(task: str, result: str, timestamp: str):
    """Save research result to a file."""
    # Create safe filename from task
    safe_name = re.sub(r'[^\w\s-]', '', task)[:50].strip().replace(' ', '_').lower()
    date_prefix = timestamp.split()[0]  # YYYY-MM-DD
    
    filename = f"{date_prefix}_{safe_name}.md"
    output_path = OUTPUT_DIR / filename
    
    content = f"""# 📚 Research: {task}

**Queued:** {timestamp}
**Completed:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
**Model:** {MODEL}

---

{result}
"""
    
    output_path.write_text(content)
    return output_path


def emit_event(event_type: str, payload: dict):
    """Emit event to brain ledger."""
    try:
        from brain_tools import emit_event as _emit
        _emit(emitter="research_worker", event_type=event_type, payload=payload)
    except ImportError:
        # Standalone mode, skip event emission
        pass


def main():
    dry_run = "--dry-run" in sys.argv
    
    print("🔬 Research Queue Processor")
    print(f"   Queue: {QUEUE_FILE}")
    print(f"   Model: {MODEL}")
    print()
    
    tasks = get_pending_tasks()
    
    if not tasks:
        print("✅ No pending research tasks.")
        return
    
    print(f"📋 Found {len(tasks)} pending task(s):\n")
    for ts, task in tasks:
        print(f"   - [{ts}] {task[:60]}...")
    print()
    
    if dry_run:
        print("🔍 Dry run mode - no tasks executed.")
        return
    
    # Process each task
    completed = 0
    failed = 0
    
    for timestamp, task in tasks:
        print(f"⚙️  Processing: {task[:50]}...")
        
        result, success = run_gemini_research(task)
        
        if success:
            output_path = save_research_result(task, result, timestamp)
            mark_task_complete(task)
            completed += 1
            print(f"   ✅ Saved to: {output_path.name}")
            
            emit_event("research_completed", {"task": task, "output": str(output_path)})
        else:
            failed += 1
            print(f"   ❌ Failed: {result[:100]}")
            
            emit_event("research_failed", {"task": task, "error": result[:200]})
    
    print()
    print(f"📊 Summary: {completed} completed, {failed} failed")


if __name__ == "__main__":
    main()
