from typing import List, Dict, Any
import os
import subprocess
from pathlib import Path
from .base import Capability

class CodeOps(Capability):
    @property
    def name(self) -> str:
        return "code_ops"

    @property
    def description(self) -> str:
        return "FileSystem and Shell Access for Coding Agents."

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "code_read_file",
                "description": "Read file contents.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "path": {"type": "string", "description": "Absolute or relative path"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "code_write_file",
                "description": "Write or overwrite file contents. Creates directories if needed.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "path": {"type": "string", "description": "Absolute or relative path"},
                        "content": {"type": "string"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "code_run_command",
                "description": "Execute a shell command.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "command": {"type": "string"},
                        "timeout": {"type": "integer", "default": 30}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "code_list_files",
                "description": "List files in directory.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "path": {"type": "string", "default": "."}
                    }
                }
            }
        ]

    def _resolve_path(self, path_str: str) -> Path:
        """
        Self-Healing Path Resolver.
        Handles the 'Brain in a Jar' paradox where memories contain absolute paths (e.g., /Users/lokeshgarg/...)
        but the body is in a different universe (e.g., /app in Docker).
        """
        cwd = Path(os.getcwd())
        original_path = Path(path_str)
        
        # 1. Try the path as-is
        if original_path.exists():
            return original_path
        
        # 2. If absolute but missing, try making it relative to CWD
        # Heuristic: If path contains 'ai-mvp-backend', strip everything before it
        # or just take the relative path from the project root.
        
        # Fallback 1: Try treating it as relative to CWD even if it looks absolute
        # (e.g. if we are in /app and path is /app/foo/bar, but maybe we are in /app/subdir)
        if not original_path.is_absolute():
            candidate = cwd / original_path
            if candidate.exists():
                return candidate

        # Fallback 2: The "Sovereign Shift" (Mac -> Docker)
        # If the filename exists in the current directory (recursively? No, too expensive).
        # Let's try to match the *relative* structure.
        # Assumption: The CWD *is* the project root.
        
        # If the path starts with /Users/..., try to find the intersection with CWD
        # This is hard to guess generally. 
        # Strategy: If the file doesn't exist, we return the path object anyway so the tool can error out naturally,
        # UNLESS we can confidently map it.
        
        return original_path

    def execute_tool(self, tool_name: str, args: Dict) -> str:
        """Execute local filesystem/shell operations."""
        cwd = os.getcwd()
        
        if tool_name == "code_read_file":
            path_str = args['path']
            # Manual Patch for Docker Compatibility
            # If we are in Docker (/app) and path starts with /Users, rewrite it.
            if os.path.exists('/.dockerenv') or os.getenv('K_SERVICE'): # Cloud Run check
                 if path_str.startswith('/Users/'):
                     # Extreme Heuristic: Assume mapped to /app
                     # /Users/lokeshgarg/ai-mvp-backend/foo -> /app/foo
                     # Find 'ai-mvp-backend' index?
                     # Simpler: If CWD is /app, and path has 'ai-mvp-backend', replace everything before it with /app
                     if 'ai-mvp-backend' in path_str:
                         parts = path_str.split('ai-mvp-backend')
                         relative = parts[1].lstrip('/')
                         path_str = f"/app/{relative}"
            
            path = Path(path_str)
            
            if not path.is_absolute():
                path = Path(cwd) / path
            
            if not path.exists():
                return f"Error: File not found: {path} (in {cwd})"
            return path.read_text(encoding='utf-8')
            
        elif tool_name == "code_write_file":
            path = Path(args['path'])
            if not path.is_absolute():
                path = Path(cwd) / path
            
            # Ensure parent exists
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(args['content'], encoding='utf-8')
            return f"✅ Wrote {len(args['content'])} bytes to {path}"
            
        elif tool_name == "code_run_command":
            cmd = args['command']
            timeout = args.get('timeout', 30)
            try:
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    cwd=cwd, 
                    timeout=timeout
                )
                return f"Exit Code: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            except subprocess.TimeoutExpired:
                return f"Error: Command timed out after {timeout}s"
            except Exception as e:
                return f"Error: {str(e)}"

        elif tool_name == "code_list_files":
            path = Path(args.get('path', '.'))
            if not path.is_absolute():
                path = Path(cwd) / path
            
            if not path.exists():
                 return f"Error: Path not found: {path}"
                 
            try:
                # Use 'ls -F' style output for simplicity
                entries = []
                for p in path.iterdir():
                    kind = "/" if p.is_dir() else ""
                    entries.append(f"{p.name}{kind}")
                return "\n".join(sorted(entries))
            except Exception as e:
                return f"Error listing files: {str(e)}"
                
        return f"Tool {tool_name} not found in CodeOps."
