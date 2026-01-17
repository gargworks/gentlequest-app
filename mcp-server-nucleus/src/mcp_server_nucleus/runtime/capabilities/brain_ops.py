from typing import List, Dict, Any
from pathlib import Path
from .base import Capability
from ... import commitment_ledger

class BrainOps(Capability):
    @property
    def name(self) -> str:
        return "brain_ops"

    @property
    def description(self) -> str:
        return "Tools for managing the centralized commitment ledger (The Brain)."

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "brain_add_commitment",
                "description": "Add a new commitment (task, todo, loop) to the ledger.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "description": {"type": "string"},
                        "loop_type": {"type": "string", "enum": ["task", "todo", "draft", "decision"]},
                        "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                        "source": {"type": "string"}
                    },
                    "required": ["description"]
                }
            },
            {
                "name": "brain_get_open_loops",
                "description": "Get all active open loops.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "type_filter": {"type": "string"}
                    }
                }
            },
            {
                "name": "brain_scan_commitments",
                "description": "Trigger the Librarian to scan artifacts for checklist items.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "brain_archive_stale",
                "description": "Trigger the Librarian to archive stale commitments.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "brain_orchestrate_swarm",
                "description": "Initialize a multi-agent swarm for a complex mission.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "mission": {"type": "string"},
                        "agents": {"type": "array", "items": {"type": "string"}},
                        "swarm_type": {"type": "string", "enum": ["genesis", "execution"]}
                    },
                    "required": ["mission"]
                }
            },
            {
                "name": "brain_export",
                "description": "Export the brain content to a zip file (respecting .brainignore).",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "brain_consolidate_logs",
                "description": "Consolidate raw JSON logs in .brain/raw/ into a daily archive.",
                "parameters": {"type": "object", "properties": {}}
            }
        ]

    def execute_tool(self, tool_name: str, args: Dict) -> str:
        """Execute the tool locally using commitment_ledger."""
        if tool_name == "brain_orchestrate_swarm":
             # Use configured brain path
            import os
            brain_path = Path(os.environ.get("NUCLEUS_BRAIN_PATH", "/Users/lokeshgarg/ai-mvp-backend/.brain"))
        else:
             # Default functionality (Ledger etc)
             brain_path = Path(os.environ.get("NUCLEUS_BRAIN_PATH", "/Users/lokeshgarg/ai-mvp-backend/.brain"))
        
        if tool_name == "brain_add_commitment":
            result = commitment_ledger.add_commitment(
                brain_path=brain_path,
                source_file="NAR_AGENT",
                source_line=0,
                description=args['description'],
                comm_type=args.get('loop_type', 'task'),
                priority=args.get('priority', 3),
                source=args.get('source', 'nar_agent')
            )
            return f"Commitment Added: {result['id']}"
            
        elif tool_name == "brain_get_open_loops":
            loops = commitment_ledger.load_ledger(brain_path)["commitments"]
            # Filter logic could go here
            return f"Found {len([c for c in loops if c['status']=='open'])} open loops."
            
        elif tool_name == "brain_scan_commitments":
            result = commitment_ledger.scan_for_commitments(brain_path)
            return f"Scan Complete: {result}"
            
        elif tool_name == "brain_archive_stale":
            count = commitment_ledger.auto_archive_stale(brain_path)
            return f"Archived {count} stale items."
            
        elif tool_name == "brain_export":
            # Call export logic (implemented in commitment_ledger for centralization)
            if hasattr(commitment_ledger, 'export_brain'):
                result = commitment_ledger.export_brain(brain_path)
                return f"Export Complete: {result}"
            return "Error: export_brain not implemented in ledger."

        elif tool_name == "brain_delegate_task":
             # Dynamic import to avoid circular dependency
            from uuid import uuid4
            from ..factory import ContextFactory
            from ..agent import EphemeralAgent
            from ..llm_client import DualEngineLLM
            
            persona = args.get('persona')
            intent = args.get('intent')
            
            # Use factory to create specialized agent
            session_id = f"delegated-{str(uuid4())[:8]}"
            factory = ContextFactory()
            
            # Create context for the specific persona
            context = factory.create_context_for_persona(session_id, persona, intent)
            
            # Execute
            llm = DualEngineLLM()
            agent = EphemeralAgent(context, model=llm)
            
            # In a real async environment, we'd await this. 
            # But execute_tool is currently sync in this base class signature.
            # We need to run it synchronously or change the signature.
            # Using asyncio.run() for now as a bridge.
            # Using asyncio.run() or existing loop via nest_asyncio
            import asyncio
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                pass

            try:
                # With nest_asyncio, we can just use asyncio.run or loop.run_until_complete
                # even if a loop is running.
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    log = loop.run_until_complete(agent.run())
                else:
                    log = asyncio.run(agent.run())
                
                return f"✅ Delegation Complete:\n{log}"
                
            except RuntimeError:
                # Fallback if nest_asyncio failed or not installed and loop is running
                return f"⚠️ Cannot block on delegation (Async Loop Running & nest_asyncio missing). Task queued for {persona}: {intent}"

        elif tool_name == "brain_orchestrate_swarm":
            from ..orchestrator import SwarmsOrchestrator
            
            orchestrator = SwarmsOrchestrator(brain_path=brain_path)
            result = orchestrator.start_mission(
                mission=args['mission'],
                swarm_type=args.get('swarm_type', 'genesis') # Default to Planning
            )
            
            return f"✅ Swarm Initiated:\nMission ID: {result['mission_id']}\nRole: {result['lead_agent']}\n\nContext:\n{result['kickoff_context'][:500]}..."

        elif tool_name == "brain_consolidate_logs":
            # Consolidate raw logs into daily archives
            import json
            from datetime import datetime
            
            brain_path = Path(os.environ.get("NUCLEUS_BRAIN_PATH", "/Users/lokeshgarg/ai-mvp-backend/.brain"))
            raw_path = brain_path / "raw"
            archive_dir = brain_path / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            if not raw_path.exists():
                return "No raw logs to consolidate."
                
            logs = list(raw_path.glob("*.json"))
            if not logs:
                return "0 logs found. Nothing to consolidate."
            
            # Group by date
            count = 0
            size_saved = 0
            
            # Use current date for the archive bucket
            # Ideally we group by the timestamp in the file, but for V1 just dumping current pile is fine.
            today = datetime.now().strftime("%Y-%m-%d")
            archive_file = archive_dir / f"raw_interactions_{today}.jsonl"
            
            with open(archive_file, "a") as out_f:
                for log_file in logs:
                    try:
                         content = log_file.read_text()
                         # Minify JSON line
                         data = json.loads(content)
                         out_f.write(json.dumps(data) + "\n")
                         
                         size_saved += log_file.stat().st_size
                         log_file.unlink() # Delete original
                         count += 1
                    except Exception as e:
                        print(f"Error consolidating {log_file}: {e}")
                        
            return f"✅ Consolidated {count} raw logs into {archive_file.name}. Saved {size_saved/1024:.2f} KB of inode space."

        return f"Tool {tool_name} not found in BrainOps."

