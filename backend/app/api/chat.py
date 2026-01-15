from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_session
from app.models.chat import InterviewSession, ChatMessage
from app.models.interview import Interview
from app.models.team import Team
from app.services.ai_insights_service import AIInsightsService

router = APIRouter()
ai_service = AIInsightsService()

@router.post("/teams/{team_id}/chat/start", response_model=InterviewSession)
async def start_chat_session(
    team_id: int, 
    session: AsyncSession = Depends(get_session)
):
    """
    Starts a new AI Interview Session.
    """
    # Verify team
    team = await session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    chat_session = InterviewSession(team_id=team_id, status="ACTIVE")
    session.add(chat_session)
    await session.commit()
    await session.refresh(chat_session)
    
    # Optional: Initial greeting from AI?
    # For now, let frontend handle the "Hi" or triggered via message.
    # Actually, a greeting is nice.
    greeting_content = "Hi there! I'm your research assistant. I'd love to learn about your team's challenges. What's the biggest problem you're facing right now?"
    greeting = ChatMessage(
        session_id=chat_session.session_id,
        role="assistant",
        content=greeting_content
    )
    session.add(greeting)
    await session.commit()
    await session.refresh(chat_session)
    
    return chat_session



from pydantic import BaseModel

class MessageRequest(BaseModel):
    content: str

@router.post("/chat/{session_id}/message", response_model=ChatMessage)
async def send_chat_message(
    session_id: int, 
    request: MessageRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Sends a user message and returns the AI response (as a new ChatMessage).
    Actually, frontend usually wants the AI response.
    We'll return the AI response message.
    """
    chat_session = await session.get(InterviewSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # 1. Save User Message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.content
    )
    session.add(user_msg)
    await session.commit()
    
    # 2. Fetch History
    # We need to fetch messages ordered by timestamp
    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp)
    result = await session.execute(stmt)
    messages = result.scalars().all()
    
    history = [{"role": m.role, "content": m.content} for m in messages]
    
    # 3. Get AI Response
    ai_text = await ai_service.conduct_interview(history, "") # User message is already in history?
    # Wait, conduct_interview takes (history, user_message).
    # If I append user_msg to history, then I should pass empty string or modify method?
    # My method implementation: conversation_text += f"Participant: {user_message}\n"
    # If user_message is inside history, it will be duplicated.
    # I should pass history EXCLUDING the last message, and pass the last message as user_message?
    # Or just update method to take full history.
    # My method expects user_message separated.
    
    # Let's clean up logic:
    # History = all previous messages (excluding the one just added).
    # content = current message.
    
    # Actually, simpler: Pass full history to AI Service and let it handle formatting.
    # But I implemented `conduct_interview` to take `user_message` separately.
    # So I will pass `history[:-1]` and `history[-1]['content']`.
    
    prev_history = history[:-1] if len(history) > 0 else []
    current_msg = request.content
    
    ai_text = await ai_service.conduct_interview(prev_history, current_msg)
    
    # 4. Save AI Response
    ai_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_text
    )
    session.add(ai_msg)
    await session.commit()
    await session.refresh(ai_msg)
    
    return ai_msg

@router.post("/chat/{session_id}/finalize", response_model=Interview)
async def finalize_chat_session(
    session_id: int, 
    session: AsyncSession = Depends(get_session)
):
    """
    Ends the chat session and converts the transcript into an Interview record used for Persona generation.
    """
    chat_session = await session.get(InterviewSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    chat_session.status = "COMPLETED"
    session.add(chat_session)
    
    # Fetch all messages
    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp)
    result = await session.execute(stmt)
    messages = result.scalars().all()
    
    # Compile params
    transcript = ""
    for m in messages:
        role = "Interviewer" if m.role == "assistant" else "Participant"
        transcript += f"{role}: {m.content}\n\n"
        
    # Create Interview Record
    interview = Interview(
        team_id=chat_session.team_id,
        interview_date=datetime.now(),
        participant_role="User (AI Interview)",
        interview_notes=transcript,
        key_quotes=[] # AI could extract these later
    )
    session.add(interview)
    await session.commit()
    await session.refresh(interview)
    
    # Trigger Analysis immediately?
    # Yes, let's extract ANRUM immediately so it feels magical.
    try:
        insights = await ai_service.extract_anrum(transcript)
        interview.insights_extracted = insights
        session.add(interview)
        await session.commit()
        await session.refresh(interview)
    except Exception:
        # Ignore analysis failure, we have the interview
        pass
        
    return interview
