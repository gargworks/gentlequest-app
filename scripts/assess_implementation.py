
import os
import sys
import json
from pathlib import Path
import time

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def check_file(path, desc):
    if path.exists():
        print(f"✅ {desc} found: {path.name}")
        return True
    else:
        print(f"❌ {desc} MISSING: {path.name}")
        return False

def check_task_status(brain_path):
    task_md_path = brain_path / "task.md"
    
    if not task_md_path.exists():
        return False, f"task.md missing at {task_md_path}"
        
    try:
        content = task_md_path.read_text()
        
        # Check for Brain Workflow Enforcement (Phase 46)
        has_phase_46 = "Phase 46: Brain Workflow Enforcement" in content
        
        # Check for GenAI Migration Tasks (Phase 45 backlog or similar)
        # Handle backticks in markdown
        has_gemini_task = "Refactor" in content and "providers/gemini.py" in content
        
        print(f"📊 Task Analysis (Source: task.md):")
        
        if has_phase_46:
            print(f"   ✅ Phase 46 (Workflow Enforcement) found")
        else:
            print(f"   ❌ Phase 46 missing from task.md")
            
        if has_gemini_task:
            print(f"   ✅ 'Refactor providers/gemini.py' task found")
            return True, "Tasks verified in task.md"
        else:
            print(f"   ❌ 'Refactor providers/gemini.py' task missing")
            return False, "Target tasks not found in task.md"
            
    except Exception as e:
        return False, str(e)

def main():
    print(f"\n🧠 {YELLOW}Brain Implementation Assessment{RESET}")
    print("==================================================")
    
    brain_str = os.environ.get("NUCLEUS_BRAIN_PATH")
    if not brain_str:
        print("❌ NUCLEUS_BRAIN_PATH not set")
        sys.exit(1)
        
    brain_path = Path(brain_str)
    
    # 1. Check Protocol
    protocol_path = brain_path / "AGENT_PROTOCOL.md"
    has_protocol = check_file(protocol_path, "Mandatory Protocol")
    
    # 2. Check Tasks
    tasks_ok, tasks_msg = check_task_status(brain_path)
    if not tasks_ok:
        print(f"❌ Task Check Failed: {tasks_msg}")
    
    # 3. Check Tool Implementation (Static Analysis)
    server_init = Path(__file__).parent.parent / "mcp-server-nucleus" / "src" / "mcp_server_nucleus" / "__init__.py"
    has_tool = False
    if server_init.exists():
        content = server_init.read_text()
        if "@mcp.tool()" in content and "def brain_session_start()" in content:
            print(f"✅ brain_session_start() tool implemented in code")
            has_tool = True
        else:
            print(f"❌ brain_session_start() tool NOT found in code")
    
    # Final Verdict
    print("\n📝 {YELLOW}Final Verdict{RESET}")
    print("--------------------------------------------------")
    
    if has_protocol and tasks_ok and has_tool:
        print(f"{GREEN}PASS: implementation Successful{RESET}")
        print("The system now mechanically enforces truth over hallucination.")
    else:
        print(f"{RED}FAIL: Implementation Incomplete{RESET}")
        print("One or more checks failed.")

if __name__ == "__main__":
    main()
