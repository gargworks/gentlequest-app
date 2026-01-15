import os
import httpx
import structlog
from app.models.tasks import ProjectTask


logger = structlog.get_logger()

class NucleusService:
    def __init__(self):
        # Allow override via env, default to the known service name if running in same project
        self.orchestrator_url = os.getenv("NUCLEUS_ORCHESTRATOR_URL", "http://nucleus-orchestrator:8080")
        
    async def delegate_task(self, task: ProjectTask, project_context: str) -> bool:
        """
        Pushes a task to the Nucleus Orchestrator for agentic execution.
        """
        payload = {
            "source": "IIP_INNOVATION_COACH",
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "context": project_context,
            "priority": task.priority,
            "skills_required": [task.assignee_role] if task.assignee_role else []
        }
        
        logger.info("delegating_task_to_nucleus", task_id=task.task_id, url=self.orchestrator_url)
        
        try:
            async with httpx.AsyncClient() as client:
                # Mocking the endpoint for now until Nucleus is fully up
                # response = await client.post(f"{self.orchestrator_url}/api/v1/tasks", json=payload)
                # response.raise_for_status()
                
                # For MVP, we just log success to simulate
                logger.info("nucleus_task_delegated_successfully", payload=payload)
                return True
        except Exception as e:
            logger.error("nucleus_delegation_failed", error=str(e))
            return False
