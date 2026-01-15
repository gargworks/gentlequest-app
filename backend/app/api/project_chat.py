from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models.team import Team
from app.models.project_chat import ProjectChatSession, ProjectChatMessage
from app.services.ai_insights_service import AIInsightsService
from app.services.project_context_service import ProjectContextService
from pydantic import BaseModel

router = APIRouter()
ai_service = AIInsightsService()

class ProjectMessageRequest(BaseModel):
    content: str

@router.post("/teams/{team_id}/project-chat/start", response_model=ProjectChatSession)
async def start_project_chat(
    team_id: int, 
    session: AsyncSession = Depends(get_session)
):
    team = await session.get(Team, team_id)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    chat_session = ProjectChatSession(team_id=team_id, title=f"Chat about {team.team_name}")
    session.add(chat_session)
    await session.commit()
    await session.refresh(chat_session)
    return chat_session

@router.post("/teams/{team_id}/project-chat/{session_id}/message", response_model=ProjectChatMessage)
async def send_project_message(
    team_id: int,
    session_id: int,
    request: ProjectMessageRequest,
    session: AsyncSession = Depends(get_session)
):
    # 1. Verify Session & Team
    chat_session = await session.get(ProjectChatSession, session_id)
    if not chat_session or chat_session.team_id != team_id:
        raise HTTPException(status_code=404, detail="Chat Session not found for this team")

    # 2. Save User Message
    user_msg = ProjectChatMessage(
        session_id=session_id,
        role="user",
        content=request.content
    )
    session.add(user_msg)
    await session.commit()
    
    # 3. Build RAG Context
    context_service = ProjectContextService(session)
    project_context = await context_service.get_project_context(team_id)
    
    # 4. Get AI Response
    ai_text = await ai_service.chat_with_project(project_context, request.content)
    
    # 5. Save AI Message
    ai_msg = ProjectChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_text
    )
    session.add(ai_msg)
    await session.commit()
    await session.refresh(ai_msg)
    
    return ai_msg

