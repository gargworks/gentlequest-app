import logging
from typing import List, Any

logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database import get_session
from app.models.tasks import ProjectTask, ProjectTaskCreate, TaskStatus
from app.models.roadmap import MVPRoadmap, MVPFeature
from app.services.ai_insights_service import AIInsightsService
from sqlalchemy.orm import selectinload

router = APIRouter()
ai_service = AIInsightsService()

@router.post("/teams/{team_id}/tasks/generate", response_model=List[ProjectTask])
async def generate_team_tasks(
    team_id: int, 
    session: AsyncSession = Depends(get_session)
):
    """
    Generate engineering tasks based on the existing MVP Roadmap for the team.
    """
    # 1. Fetch Roadmap
    statement = select(MVPRoadmap).where(MVPRoadmap.team_id == team_id).options(selectinload(MVPRoadmap.features))
    result = await session.execute(statement)
    roadmap = result.scalars().first()
    
    if not roadmap:
        raise HTTPException(status_code=404, detail="No Roadmap found for this team. Generate Roadmap first.")

    # 2. Call AI Service
    try:
        # Note: roadmap.features might need explicit loading if lazily loaded.
        # But for now passing the roadmap object should trigger lazy load if accessed, 
        # but in Async, lazy loading attributes FAILS ("Awaited required").
        # We should ideally eager load 'features'.
        # For simplicity, we just pass roadmap, and if AI Service accesses .model_dump(), it might fail if features not loaded in session.
        # However, .model_dump() usually works if fields are present.
        tasks_data = await ai_service.generate_project_tasks(roadmap)
    except Exception as e:
        logger.error("Task generation failed for team %d: %s", team_id, e)
        raise HTTPException(status_code=500, detail="Task generation failed. Please try again.")

    if not tasks_data:
        raise HTTPException(status_code=500, detail="AI returned no tasks.")

    # 3. Save to DB
    # Clear existing tasks
    stmt = select(ProjectTask).where(ProjectTask.team_id == team_id)
    result = await session.execute(stmt)
    existing_tasks = result.scalars().all()
    for t in existing_tasks:
        await session.delete(t)
    
    created_tasks = []
    for task_dict in tasks_data:
        task = ProjectTask(
            team_id=team_id,
            roadmap_id=roadmap.roadmap_id,
            title=task_dict.get("title", "Untitled Task"),
            description=task_dict.get("description", ""),
            priority=task_dict.get("priority", "MEDIUM"),
            estimated_hours=task_dict.get("estimated_hours"),
            assignee_role=task_dict.get("assignee_role"),
            status=TaskStatus.TODO
        )
        session.add(task)
        created_tasks.append(task)
    
    await session.commit()
    
    # Refresh to populate IDs
    for t in created_tasks:
        await session.refresh(t)
        
    return created_tasks

@router.get("/teams/{team_id}/tasks", response_model=List[ProjectTask])
async def get_team_tasks(team_id: int, session: AsyncSession = Depends(get_session)):
    statement = select(ProjectTask).where(ProjectTask.team_id == team_id)
    result = await session.execute(statement)
    return result.scalars().all()

@router.put("/tasks/{task_id}", response_model=ProjectTask)
async def update_task_status(
    task_id: int, 
    status: TaskStatus, 
    session: AsyncSession = Depends(get_session)
):
    task = await session.get(ProjectTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = status
    task.updated_at = datetime.utcnow()
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task

from app.services.nucleus_service import NucleusService
from app.services.project_context_service import ProjectContextService

nucleus_service = NucleusService()

@router.post("/tasks/{task_id}/delegate", response_model=ProjectTask)
async def delegate_task_to_nucleus(
    task_id: int, 
    session: AsyncSession = Depends(get_session)
):
    """
    Delegate a task to the Nucleus Agent System.
    """
    task = await session.get(ProjectTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Get Project Context using Team ID
    context_service = ProjectContextService(session)
    project_context = await context_service.get_project_context(task.team_id)
        
    # Delegate
    try:
        success = await nucleus_service.delegate_task(task, project_context)
    except Exception as e:
        logger.error("Nucleus delegation failed for task %d: %s", task_id, e)
        raise HTTPException(status_code=502, detail="Task delegation failed. Please try again.")

    if success:
        task.status = TaskStatus.IN_PROGRESS # Or a new status "DELEGATED"
        task.updated_at = datetime.utcnow()
        session.add(task)
        await session.commit()
        await session.refresh(task)
    else:
        raise HTTPException(status_code=502, detail="Failed to delegate task to Nucleus")
        
    return task

