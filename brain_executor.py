#!/usr/bin/env python3
"""
Brain Executor - Automated LLM Agent Bridge
============================================

This module executes agents by:
1. Reading their system prompt from .brain/agents/{agent}.md
2. Building context from the task and relevant files
3. Calling the Gemini API
4. Capturing output and emitting events

Usage:
    python brain_executor.py execute <agent> <task_description>
    python brain_executor.py process-pending

Requires:
    pip install google-generativeai
    export GEMINI_API_KEY=your_api_key

Author: Nuclear Brain System
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import re

# Try to import Gemini API
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("Warning: google-generativeai not installed. Run: pip install google-generativeai")

# MDR_010: Telemetry Integration
try:
    sys.path.append(str(Path(__file__).parent / "mcp-server-nucleus" / "src"))
    from mcp_server_nucleus import commitment_ledger
    HAS_LEDGER = True
except ImportError:
    HAS_LEDGER = False
    print("Warning: mcp_server_nucleus not found. Telemetry disabled.")

# ============================================================================
# CONFIGURATION
# ============================================================================

BRAIN_ROOT = Path(__file__).parent / ".brain"
AGENTS_DIR = BRAIN_ROOT / "agents"
LEDGER_DIR = BRAIN_ROOT / "ledger"
ARTIFACTS_DIR = BRAIN_ROOT / "artifacts"
MEMORY_DIR = BRAIN_ROOT / "memory"
ACTIVATIONS_DIR = BRAIN_ROOT / "activations"

STATE_FILE = LEDGER_DIR / "state.json"
EVENTS_FILE = LEDGER_DIR / "events.jsonl"
TRIGGERS_FILE = LEDGER_DIR / "triggers.json"

# Default model (can be overridden via env)
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

# Agent → System Prompt mapping
AGENT_PROMPTS = {
    "synthesizer": AGENTS_DIR / "synthesizer.md",
    "researcher": AGENTS_DIR / "researcher.md",
    "strategist": AGENTS_DIR / "strategist.md",
    "architect": AGENTS_DIR / "architect.md",
    "developer": AGENTS_DIR / "developer.md",
    "critic": AGENTS_DIR / "critic.md",
}

# Agent → Output Directory mapping
AGENT_OUTPUT_DIRS = {
    "synthesizer": ARTIFACTS_DIR / "synthesis",
    "researcher": ARTIFACTS_DIR / "research",
    "strategist": ARTIFACTS_DIR / "strategy",
    "architect": ARTIFACTS_DIR / "architecture",
    "developer": ARTIFACTS_DIR / "code",
    "critic": ARTIFACTS_DIR / "reviews",
}

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def read_state() -> dict:
    """Read current state.json"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def write_state(state: dict):
    """Write state.json"""
    state['last_updated'] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

def emit_event(event_type: str, emitter: str, severity: str, payload: dict, metadata: dict = None):
    """Append event to events.jsonl"""
    event = {
        "event_id": hashlib.md5(f"{datetime.now().isoformat()}-{emitter}".encode()).hexdigest()[:16],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "emitter": emitter,
        "event_type": event_type,
        "severity": severity,
        "payload": payload,
        "metadata": metadata or {}
    }
    with open(EVENTS_FILE, 'a') as f:
        f.write(json.dumps(event) + '\n')
    return event

def read_file_content(path: str) -> str:
    """Read a file, handling relative paths from brain root"""
    if path.startswith('.brain/'):
        full_path = Path(__file__).parent / path
    elif path.startswith('./'):
        full_path = Path(__file__).parent / path[2:]
    else:
        full_path = Path(__file__).parent / path
    
    if full_path.exists():
        return full_path.read_text()
    return f"[File not found: {path}]"

# ============================================================================
# AGENT EXECUTION
# ============================================================================

class AgentExecutor:
    """Executes an agent via Gemini API"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name.lower()
        self.prompt_file = AGENT_PROMPTS.get(self.agent_name)
        self.output_dir = AGENT_OUTPUT_DIRS.get(self.agent_name, ARTIFACTS_DIR / "other")
        
        if not self.prompt_file or not self.prompt_file.exists():
            raise ValueError(f"Unknown agent or missing prompt: {agent_name}")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load system prompt
        self.system_prompt = self.prompt_file.read_text()
        
        # Initialize LLM (Dual-Engine Migration)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.model = None
        else:
            try:
                from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
                self.model = DualEngineLLM(DEFAULT_MODEL, api_key=api_key)
            except Exception as e:
                print(f"Error initializing DualEngineLLM: {e}")
                self.model = None
    
    def build_context(self, task: dict, include_files: List[str] = None) -> str:
        """Build execution context for the agent"""
        context_parts = []
        
        # Current state
        state = read_state()
        context_parts.append("## CURRENT STATE")
        context_parts.append(f"Sprint: {state.get('current_sprint', {}).get('name', 'None')}")
        context_parts.append(f"Active Agents: {', '.join(state.get('active_agents', []))}")
        context_parts.append("")
        
        # Task details
        context_parts.append("## YOUR TASK")
        context_parts.append(f"Task ID: {task.get('task_id', 'N/A')}")
        context_parts.append(f"Description: {task.get('task_description', 'No description')}")
        context_parts.append(f"Expected Output: {task.get('expected_output', 'N/A')}")
        context_parts.append(f"Deadline: {task.get('deadline_hours', 'N/A')} hours")
        context_parts.append("")
        
        # Context files
        files_to_include = include_files or task.get('context_files', [])
        if files_to_include:
            context_parts.append("## CONTEXT FILES")
            for file_path in files_to_include:
                content = read_file_content(file_path)
                context_parts.append(f"### {file_path}")
                context_parts.append("```")
                context_parts.append(content[:5000])  # Limit size
                context_parts.append("```")
                context_parts.append("")
        
        # Memory (patterns + learnings)
        patterns_file = MEMORY_DIR / "patterns.md"
        if patterns_file.exists():
            context_parts.append("## KNOWN PATTERNS")
            context_parts.append(patterns_file.read_text()[:2000])
            context_parts.append("")
        
        return '\n'.join(context_parts)
    
    def execute(self, task: dict, dry_run: bool = False) -> dict:
        """Execute the agent on a task"""
        
        # MDR_010: Record Usage
        if HAS_LEDGER and not dry_run:
            try:
                commitment_ledger.record_interaction(BRAIN_ROOT)
            except Exception as e:
                print(f"Warning: Telemetry failed: {e}")

        # Build context
        context = self.build_context(task)
        
        # Full prompt = System prompt + Context
        full_prompt = f"""
{self.system_prompt}

---

# EXECUTION CONTEXT

{context}

---

# INSTRUCTIONS

Execute your task now. Produce your output in a well-structured format.
At the end, include a JSON block with metadata:

```json
{{
    "success": true/false,
    "output_file": "suggested_filename.md",
    "highlights": ["key point 1", "key point 2"],
    "next_actions": ["optional next step"]
}}
```
"""
        
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "prompt_length": len(full_prompt),
                "agent": self.agent_name,
                "task_id": task.get('task_id')
            }
        
        if not self.model:
            return {
                "success": False,
                "error": "Gemini API not available"
            }
        
        # Call Gemini API
        try:
            response = self.model.generate_content(full_prompt)
            output_text = response.text
            
            # Parse metadata from response
            metadata = self._extract_metadata(output_text)
            
            # Save output to file
            output_filename = metadata.get('output_file', f"{self.agent_name}_{task.get('task_id', 'output')}.md")
            output_path = self.output_dir / output_filename
            output_path.write_text(output_text)
            
            # Emit completion event
            emit_event(
                event_type="task_completed",
                emitter=self.agent_name,
                severity="NOTABLE",
                payload={
                    "task_id": task.get('task_id'),
                    "task_description": task.get('task_description', '')[:100],
                    "output_path": str(output_path.relative_to(Path(__file__).parent)),
                    "success": metadata.get('success', True),
                    "highlights": metadata.get('highlights', [])
                },
                metadata={"model": DEFAULT_MODEL}
            )
            
            return {
                "success": True,
                "output_path": str(output_path),
                "output_length": len(output_text),
                "highlights": metadata.get('highlights', [])
            }
            
        except Exception as e:
            # Log failure
            emit_event(
                event_type="task_failed",
                emitter=self.agent_name,
                severity="CRITICAL",
                payload={
                    "task_id": task.get('task_id'),
                    "error": str(e)
                }
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_metadata(self, text: str) -> dict:
        """Extract JSON metadata block from output"""
        try:
            # Find JSON block
            match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except:
            pass
        return {}

# ============================================================================
# PENDING TASK PROCESSOR
# ============================================================================

def get_pending_tasks() -> List[dict]:
    """Get all unprocessed task_assigned events"""
    pending = []
    processed_ids = set()
    
    # Get already completed task IDs
    if EVENTS_FILE.exists():
        with open(EVENTS_FILE, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event.get('event_type') in ('task_completed', 'task_failed'):
                        processed_ids.add(event.get('payload', {}).get('task_id'))
                except:
                    pass
    
    # Get pending task_assigned events
    if EVENTS_FILE.exists():
        with open(EVENTS_FILE, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event.get('event_type') == 'task_assigned':
                        task_id = event.get('payload', {}).get('task_id')
                        if task_id and task_id not in processed_ids:
                            pending.append({
                                "event_id": event.get('event_id'),
                                "target_agent": event.get('payload', {}).get('target_agent'),
                                "task_id": task_id,
                                "task_description": event.get('payload', {}).get('task_description'),
                                "expected_output": event.get('payload', {}).get('expected_output'),
                                "deadline_hours": event.get('payload', {}).get('deadline_hours'),
                                "context_files": event.get('payload', {}).get('context_files', [])
                            })
                except:
                    pass
    
    return pending

def process_pending_tasks(dry_run: bool = False, limit: int = None):
    """Process all pending task assignments"""
    pending = get_pending_tasks()
    
    if not pending:
        print("No pending tasks to process.")
        return
    
    if limit:
        pending = pending[:limit]
    
    print(f"Found {len(pending)} pending task(s)")
    
    for task in pending:
        agent_name = task.get('target_agent')
        task_id = task.get('task_id')
        
        print(f"\n>>> Executing: {agent_name} → {task_id}")
        print(f"    Task: {task.get('task_description', '')[:60]}...")
        
        try:
            executor = AgentExecutor(agent_name)
            result = executor.execute(task, dry_run=dry_run)
            
            if result.get('success'):
                print(f"    ✅ Success: {result.get('output_path', 'dry_run')}")
            else:
                print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Brain Executor - Automated Agent LLM Bridge")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Execute single agent
    exec_parser = subparsers.add_parser('execute', help='Execute a single agent with a task')
    exec_parser.add_argument('agent', choices=list(AGENT_PROMPTS.keys()), help='Agent to execute')
    exec_parser.add_argument('task', help='Task description')
    exec_parser.add_argument('--dry-run', action='store_true', help='Simulate without calling API')
    
    # Process pending tasks
    pending_parser = subparsers.add_parser('process', help='Process all pending task assignments')
    pending_parser.add_argument('--dry-run', action='store_true', help='Simulate without calling API')
    pending_parser.add_argument('--limit', type=int, help='Limit number of tasks to process')
    
    # List pending
    list_parser = subparsers.add_parser('list', help='List pending tasks')
    
    # Status
    status_parser = subparsers.add_parser('status', help='Show executor status')
    
    args = parser.parse_args()
    
    if args.command == 'execute':
        task = {
            "task_id": f"manual-{int(datetime.now().timestamp())}",
            "task_description": args.task,
            "expected_output": "Output based on task",
            "deadline_hours": 24
        }
        executor = AgentExecutor(args.agent)
        result = executor.execute(task, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'process':
        process_pending_tasks(dry_run=args.dry_run, limit=args.limit)
    
    elif args.command == 'list':
        pending = get_pending_tasks()
        if pending:
            print(f"Pending Tasks ({len(pending)}):")
            for t in pending:
                print(f"  • {t['target_agent']} → {t['task_id']}: {t['task_description'][:50]}...")
        else:
            print("No pending tasks.")
    
    elif args.command == 'status':
        print("=" * 60)
        print("BRAIN EXECUTOR STATUS")
        print("=" * 60)
        print(f"Gemini API: {'Available' if HAS_GENAI else 'NOT INSTALLED'}")
        print(f"API Key: {'Set' if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
        print(f"Model: {DEFAULT_MODEL}")
        print(f"Agents: {', '.join(AGENT_PROMPTS.keys())}")
        pending = get_pending_tasks()
        print(f"Pending Tasks: {len(pending)}")
        print("=" * 60)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
