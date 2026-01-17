#!/usr/bin/env python3
"""
oracle_reflexion.py
Phase 66: The Surgeon.
Automatically applies fixes from the Backlog.
"""
import json
import logging
import os
import sys
import re
from pathlib import Path
from datetime import datetime

# Add project root to path to find mcp_server_nucleus
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

try:
    from mcp_server_nucleus.runtime.llm_client import DualEngineLLM
except ImportError:
    print("❌ Critical Error: Could not import mcp_server_nucleus.runtime.llm_client")
    print("Ensure mcp-server-nucleus is installed or in python path.")
    sys.exit(1)

# Setup Logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] 🩺 %(message)s')
logger = logging.getLogger("OracleSurgeon")

BRAIN_PATH = Path(".brain")

class BrainFixCode:
    """
    Inline implementation of the Code Fixer Capability for the Surgeon.
    """
    def __init__(self, llm: DualEngineLLM):
        self.llm = llm

    def run(self, diagnosis: str, file_path: str = "AUTO_DETECT") -> str:
        """
        Generates and applies a code fix based on the diagnosis.
        """
        prompt = f"""
You are The Surgeon. 
Your task is to fix the codebase based on the Auditor's Critique and the Surgeon's Diagnosis.

## Diagnosis
{diagnosis}

## Task
1. Identify the file that needs to be changed.
2. Make the necessary changes to fix the issue.
3. Use `replace_file_content` checks to ensure precision.

## Important
You CANNOT use tools directly. You must output the FILE PATH and the NEW CONTENT (or specific lines) in a structured format that I can parse.
Output a JSON object representing the tool call you WOULD make.

Format:
```json
{{
  "tool": "replace_file_content",
  "args": {{
      "path": "/absolute/path/to/file",
      "target_content": "exact string to replace",
      "replacement_content": "new string"
  }}
}}
```
OR
```json
{{
  "tool": "write_file",
  "args": {{
      "path": "/absolute/path/to/file",
      "content": "full new content"
  }}
}}
```
Only output ONE JSON block.
"""
        response = self.llm.generate_content(prompt)
        try:
            # Extract JSON
            text = response.text if hasattr(response, 'text') else str(response)
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
            if not json_match:
                 # Try finding just { ... }
                 json_match = re.search(r"(\{.*\})", text, re.DOTALL)
            
            if json_match:
                tool_call = json.loads(json_match.group(1))
                return self._execute_tool(tool_call)
            else:
                return f"Error: Could not parse JSON from Surgeon response: {text[:200]}..."
        except Exception as e:
            return f"Error executing fix: {e}"

    def _execute_tool(self, tool_call: dict) -> str:
        tool_name = tool_call.get("tool")
        args = tool_call.get("args", {})
        
        path_str = args.get("path")
        if not path_str:
            return "Error: No path provided."
            
        path = Path(path_str)
        if not path.is_absolute():
            # Assume relative to CWD
            path = Path.cwd() / path

        if tool_name == "write_file":
            content = args.get("content")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return f"✅ Wrote {len(content)} chars to {path}."
            
        elif tool_name == "replace_file_content":
            target = args.get("target_content")
            replacement = args.get("replacement_content")
            
            if not path.exists():
                return f"Error: File {path} not found."
                
            original = path.read_text()
            if target not in original:
                 # Fuzzy match fallback? No, strict is safer for Surgeon.
                 return f"Error: Target content not found in {path}. Refusing to patch."
            
            new_content = original.replace(target, replacement)
            path.write_text(new_content)
            return f"✅ Patched {path} successfully."

        return f"Error: Unknown tool {tool_name}"

def apply_fix():
    backlog_path = BRAIN_PATH / "backlog" / "fixes.json"
    
    if not backlog_path.exists():
        logger.info("No backlog found.")
        return

    try:
        backlog = json.loads(backlog_path.read_text())
    except Exception:
        backlog = []
    
    # Find oldest pending fix
    target = None
    target_idx = -1
    for idx, fix in enumerate(backlog):
        if fix.get("status") == "pending":
            target = fix
            target_idx = idx
            break
            
    if not target:
        logger.info("No pending fixes in the waiting room.")
        return

    instruction = target.get("instruction", "No instruction")
    logger.info(f"💉 Attempting Surgery: {instruction}")
    
    # Check for Mock Mode
    if os.environ.get("MOCK_SIMULATION") == "1":
        logger.info("⚠️  MOCK MODE: Simulating Surgery.")
        response = "✅ [MOCK] Patched file successfully."
        # Update Backlog
        try:
            backlog = json.loads(backlog_path.read_text())
            for f in backlog:
                if f.get("instruction") == instruction and f.get("status") == "pending":
                     f["status"] = "applied"
                     f["result"] = str(response)
                     f["applied_at"] = datetime.now().isoformat()
                     break
            backlog_path.write_text(json.dumps(backlog, indent=2))
            logger.info("✅ Fix applied and marked as resolved (MOCK).")
        except Exception as e:
            logger.error(f"Failed to update backlog: {e}")
        return

    # Initialize LLM (Surgeon)
    # Using DualEngineLLM which handles GEMINI_API_KEY fallback
    try:
        llm = DualEngineLLM(
            model_name="gemini-2.0-flash-exp",
            system_instruction="You are The Surgeon."
        )
    except Exception as e:
        logger.error(f"Failed to initialize Surgeon LLM: {e}")
        return
    
    fixer = BrainFixCode(llm)
    
    # Load Ledger Context
    journal_path = BRAIN_PATH / "memory" / "ORACLE_LEDGER.md"
    journal_context = ""
    if journal_path.exists():
        journal_text = journal_path.read_text()[-3000:]
        journal_context = f"PREVIOUS LESSONS:\n{journal_text}\n"

    diagnosis = f"{journal_context}\nINSTRUCTION:\n{instruction}"
    
    response = fixer.run(diagnosis)
    
    logger.info(f"Result: {response}")
    
    # Log to Ledger
    try:
        log_entry = f"\n## [{datetime.now().isoformat()}] - SURGERY APPLIED\n**Instruction:** {instruction}\n**Result:** {response}\n---"
        with open(journal_path, "a") as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"Failed to record surgery: {e}")

    # Update Backlog
    # Re-read to minimize race conditions
    try:
        backlog = json.loads(backlog_path.read_text())
        # Find item again by instruction since objects are new
        for f in backlog:
            if f.get("instruction") == instruction and f.get("status") == "pending":
                 f["status"] = "applied"
                 f["result"] = str(response)
                 f["applied_at"] = datetime.now().isoformat()
                 break
        backlog_path.write_text(json.dumps(backlog, indent=2))
        logger.info("✅ Fix applied and marked as resolved.")
    except Exception as e:
        logger.error(f"Failed to update backlog: {e}")

if __name__ == "__main__":
    apply_fix()
