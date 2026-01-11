"""
Nucleus MCP Server
==================
Model Context Protocol server for brain state management.

Exposes the following tools:
- brain_get_state: Read current brain state
- brain_update_state: Update brain state
- brain_emit_event: Emit event to ledger
- brain_read_events: Read recent events
- brain_list_artifacts: List artifacts
- brain_read_artifact: Read artifact content
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nucleus.state import get_state, set_state
from nucleus.events import emit_event, get_events

# MCP protocol constants
MCP_VERSION = "0.1.0"

def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    """Route tool calls to appropriate handlers."""
    
    handlers = {
        "brain_get_state": handle_get_state,
        "brain_update_state": handle_update_state,
        "brain_emit_event": handle_emit_event,
        "brain_read_events": handle_read_events,
        "brain_list_artifacts": handle_list_artifacts,
        "brain_read_artifact": handle_read_artifact,
        "brain_scan_marketing_log": handle_scan_marketing_log,
    }
    
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        return handler(arguments)
    except Exception as e:
        return {"error": str(e)}

def handle_get_state(args: dict) -> dict:
    """Get current brain state."""
    path = args.get("path")
    state = get_state(path)
    return {"state": state}

def handle_update_state(args: dict) -> dict:
    """Update brain state."""
    updates = args.get("updates", {})
    success = set_state(updates)
    return {"success": success}

def handle_emit_event(args: dict) -> dict:
    """Emit an event to the ledger."""
    event_id = emit_event(
        emitter=args.get("emitter", "mcp_server"),
        event_type=args.get("event_type", "unknown"),
        payload=args.get("data", {}),
        severity=args.get("severity", "NOTABLE")
    )
    return {"event_id": event_id}

def handle_read_events(args: dict) -> dict:
    """Read recent events from ledger."""
    limit = args.get("limit", 10)
    event_type = args.get("event_type")
    events = get_events(limit=limit, event_type=event_type)
    return {"events": events, "count": len(events)}

def handle_list_artifacts(args: dict) -> dict:
    """List artifacts in the brain."""
    artifacts_dir = Path(".brain/artifacts")
    folder = args.get("folder")
    
    if folder:
        artifacts_dir = artifacts_dir / folder
    
    if not artifacts_dir.exists():
        return {"artifacts": [], "count": 0}
    
    artifacts = []
    for path in artifacts_dir.iterdir():
        artifacts.append({
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "size": path.stat().st_size if path.is_file() else None
        })
    
    return {"artifacts": artifacts, "count": len(artifacts)}

def handle_read_artifact(args: dict) -> dict:
    """Read artifact content."""
    artifact_path = args.get("path")
    if not artifact_path:
        return {"error": "path required"}
    
    full_path = Path(".brain/artifacts") / artifact_path
    
    if not full_path.exists():
        return {"error": f"Artifact not found: {artifact_path}"}
    
    if full_path.is_dir():
        return {"error": "Cannot read directory"}
    
    try:
        content = full_path.read_text()
        return {"content": content, "path": str(full_path)}
    except Exception as e:
        return {"error": f"Read error: {e}"}


def handle_scan_marketing_log(args: dict) -> dict:
    """Scan marketing_log.md for failures."""
    try:
        # Resolve path relative to project root (parent of parent of parent of this file)
        # This file is in nucleus/mcp_server/server.py
        root_dir = Path(__file__).parent.parent.parent
        log_path = root_dir / "docs" / "marketing" / "marketing_log.md"
        
        if not log_path.exists():
            return {"status": "error", "message": "Log file not found"}
            
        content = log_path.read_text()
        
        # Parse failures
        import re
        failures = []
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if "[FAILURE]" in line:
                # Extract context if possible (tag inside brackets)
                tag_match = re.search(r"\[FAILURE\]\s*\[(.*?)\]", line)
                tag = tag_match.group(1) if tag_match else "UNKNOWN"
                
                failures.append({
                    "line": i + 1,
                    "tag": tag,
                    "content": line.strip()
                })
        
        status = "degraded" if failures else "healthy"
        
        return {
            "status": status,
            "failure_count": len(failures),
            "failures": failures[-5:] # Return last 5 failures
        }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_tool_definitions() -> list:
    """Return MCP tool definitions."""
    return [
        {
            "name": "brain_get_state",
            "description": "Get the current state of the brain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Optional dot-notation path (e.g., 'current_sprint.name')"
                    }
                }
            }
        },
        {
            "name": "brain_update_state",
            "description": "Update the brain state with new values (shallow merge).",
            "parameters": {
                "type": "object",
                "properties": {
                    "updates": {
                        "type": "object",
                        "description": "Dictionary of fields to update"
                    }
                },
                "required": ["updates"]
            }
        },
        {
            "name": "brain_emit_event",
            "description": "Emit a new event to the brain ledger.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_type": {"type": "string"},
                    "emitter": {"type": "string"},
                    "data": {"type": "object"},
                    "severity": {"type": "string", "enum": ["ROUTINE", "NOTABLE", "CRITICAL"]}
                },
                "required": ["event_type", "emitter", "data"]
            }
        },
        {
            "name": "brain_read_events",
            "description": "Read the most recent events from the ledger.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "event_type": {"type": "string"}
                }
            }
        },
        {
            "name": "brain_list_artifacts",
            "description": "List artifacts in a folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder": {"type": "string"}
                }
            }
        },
        {
            "name": "brain_read_artifact",
            "description": "Read contents of an artifact file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "brain_scan_marketing_log",
            "description": "Scan the marketing log for system failures.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    ]


if __name__ == "__main__":
    # Test the handlers
    print("Testing Nucleus MCP Server...")
    
    # Test get state
    result = handle_tool_call("brain_get_state", {})
    print(f"get_state: {json.dumps(result, indent=2)[:200]}...")
    
    # Test emit event
    result = handle_tool_call("brain_emit_event", {
        "event_type": "test_event",
        "emitter": "mcp_test",
        "data": {"message": "MCP server test"}
    })
    print(f"emit_event: {result}")

    # Test scan marketing log (Adaptive Protocol)
    print("\nTesting brain_scan_marketing_log...")
    result = handle_tool_call("brain_scan_marketing_log", {})
    print(f"scan_result: {json.dumps(result, indent=2)}")
    
    print("✅ MCP Server handlers working")
