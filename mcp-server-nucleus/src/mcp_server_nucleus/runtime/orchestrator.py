
"""
Preemptive Swarms Orchestrator.
The "Muscles" of the Nucleus Daemon.

Strategic Role:
- Manages Agent Swarms (Genesis, Execution).
- Enforces "Bounded Autonomy" (Budget/Time limits).
- Bridges the "Context Factory" (Tools) with the "Daemon" (Loop).
- Future: Triggers "Private Graph Training" (Lokesh-GPT).
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

from .locking import get_lock
from .policy import DirectivesLoader, MissionParameters
from .factory import ContextFactory # Integration with Tooling

logger = logging.getLogger(__name__)

class PrivateGraphTrainer:
    """
    Interface for Local Fine-Tuning (Path D: Lokesh-GPT).
    Currently a stub, but architecturally placed for Phase 60.
    """
    def __init__(self, brain_path: Path):
        self.brain_path = brain_path
        
    async def train_on_session(self, session_id: str, content: str):
        """
        Future: Fine-tune local SLM on this session.
        Current: Log intent.
        """
        logger.info(f"🎓 [TRAINER] Would fine-tune on session {session_id}")
        # Append to training dataset
        dataset_path = self.brain_path / "training" / "dataset.jsonl"
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        # Lock not strictly needed for append if atomic, but good practice
        # Skipping lock for MVP Trainer
        pass

class SwarmsOrchestrator:
    def __init__(self, brain_path: Path):
        self.brain_path = brain_path
        self.state_file = brain_path / "swarms" / "state.json"
        
        # Dependencies
        self.policy_engine = DirectivesLoader(brain_path)
        self.context_factory = ContextFactory(brain_path)
        self.trainer = PrivateGraphTrainer(brain_path)
        
        self._active_missions = {}
        self._load_state()

    def _load_state(self):
        """Load swarm state with BrainLock"""
        if not self.state_file.exists():
            return

        try:
            # Read-only, no lock needed if we accept slight staleness on startup
            # But better to check lock if we can commit to it.
            # For simplicity in init, we just read.
            self._active_missions = json.loads(self.state_file.read_text())
        except Exception as e:
            logger.error(f"Failed to load swarm state: {e}")

    def _save_state(self):
        """Save swarm state with BrainLock"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with get_lock("swarms", self.brain_path).section():
                self.state_file.write_text(json.dumps(self._active_missions, indent=2))
        except Exception as e:
            logger.error(f"Failed to save swarm state: {e}")

    async def start_mission(self, mission_goal: str, swarm_type: str = "genesis") -> Dict[str, Any]:
        """
        Start a new mission (Non-blocking).
        """
        mission_id = f"mission-{int(time.time())}"
        logger.info(f"🚀 Starting Mission {mission_id}: {mission_goal}")
        
        # 1. Load Policy constraints
        params = self.policy_engine.get_mission_parameters(swarm_type)
        
        # 2. Initialize Mission State
        mission_state = {
            "id": mission_id,
            "goal": mission_goal,
            "type": swarm_type,
            "status": "running",
            "step_count": 0,
            "cost_usd": 0.0,
            "created_at": time.time(),
            "max_steps": params.max_steps,
            "max_budget": params.max_budget_usd
        }
        
        self._active_missions[mission_id] = mission_state
        self._save_state()
        
        # 3. Spawn Async Execution (Fire and Forget)
        asyncio.create_task(self._run_mission_loop(mission_id, mission_state, params))
        
        return {"mission_id": mission_id, "status": "started"}

    async def _run_mission_loop(self, mission_id: str, state: Dict, params: MissionParameters):
        """
        The Preemptive Execution Loop.
        """
        try:
            logger.info(f"🔄 Mission {mission_id} loop started.")
            
            # Simulated Agent Loop
            while state["status"] == "running":
                # Check Bounds (Safety First)
                if state["step_count"] >= params.max_steps:
                    logger.warning(f"🛑 Mission {mission_id} hit Max Steps ({params.max_steps}). halting.")
                    state["status"] = "halted_steps"
                    break
                    
                if state["cost_usd"] >= params.max_budget_usd:
                    logger.warning(f"💸 Mission {mission_id} hit Budget Limit (${params.max_budget_usd}). halting.")
                    state["status"] = "halted_budget"
                    break
                
                # EXECUTE STEP (Simulated for MVP)
                # In real Phase 60, this calls `self.context_factory.create_context()` and hits the LLM.
                await asyncio.sleep(1) # Simulation delay
                
                state["step_count"] += 1
                state["cost_usd"] += 0.01 # Simulated cost
                
                # Check for completion (Mock)
                if state["step_count"] > 5: # Mock success
                    state["status"] = "completed"
                    logger.info(f"✅ Mission {mission_id} Completed.")
                    
                    # Trigger Training (The "Sovereign Loop")
                    await self.trainer.train_on_session(mission_id, "Simulated interaction content")
                
                # Save checkpoint
                self._active_missions[mission_id] = state
                self._save_state()
                
        except Exception as e:
            logger.error(f"💥 Mission {mission_id} Failed: {e}")
            state["status"] = "failed"
            self._save_state()
            
    async def get_mission_status(self, mission_id: str) -> Optional[Dict]:
        return self._active_missions.get(mission_id)
