"""Sovereign orchestrator extensions — Third Brother routing + archive training."""

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class PrivateGraphTrainer:
    """Local fine-tuning interface — records sessions to the archive pipeline."""

    def __init__(self, brain_path: Path):
        self.brain_path = brain_path

    async def train_on_session(self, session_id: str, content: str):
        """Record session to archive for Third Brother training."""
        logger.info(f"🎓 [TRAINER] Recording session {session_id} to archive")
        try:
            from ..runtime.archive_pipeline import ArchivePipeline
            archive = ArchivePipeline(brain_path=self.brain_path)
            archive.record_turn(
                brother="code",
                intent=f"Orchestrated session {session_id}",
                actions=[content[:200] if content else ""],
                tools_used=[],
                decisions=[],
                outcome=f"Session {session_id} completed",
                signal_absorbed=[],
                signal_produced=[f"session/{session_id}"],
                confidence=0.8,
                context="Orchestrator auto-archive",
            )
        except Exception:
            pass  # Non-blocking


def sovereign_get_best_model(orchestrator, job_type: str = "ORCHESTRATION"):
    """Route to Third Brother (local) when available, Gemini otherwise.

    The Third Brother handles routine orchestration at $0 cost.
    Complex tasks (PREMIUM tier) always go to frontier models.
    Cache TTL: re-checks local availability every 5 minutes so
    starting Ollama after the orchestrator is detected.
    """
    from ..runtime.llm_client import DualEngineLLM

    # Premium/complex tasks → always frontier
    if job_type in ("PREMIUM", "CRITICAL"):
        return DualEngineLLM(job_type=job_type)

    # Check if local model is available (cached with TTL)
    now = time.time()
    if orchestrator._local_available is None or (now - orchestrator._local_checked_at) > orchestrator._LOCAL_TTL:
        prev = orchestrator._local_available
        try:
            from .local_llm import LocalLLM
            local = LocalLLM()
            local.generate_content("test", max_tokens=5)
            orchestrator._local_available = True
            if not prev:
                logger.info("🧬 Third Brother (local) available — routing routine tasks locally")
        except Exception:
            orchestrator._local_available = False
            if prev:
                logger.info("🧬 Third Brother (local) went offline — falling back to Gemini")
        orchestrator._local_checked_at = now

    if orchestrator._local_available:
        try:
            from .local_llm import LocalLLM
            return LocalLLM()
        except Exception:
            pass

    # Fallback: Gemini
    return DualEngineLLM(job_type=job_type)
