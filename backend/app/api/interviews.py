from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models.interview import Interview
from app.services.ai_insights_service import AIInsightsService

router = APIRouter()
ai_service = AIInsightsService()

class InterviewCreate(SQLModel):
    interview_date: datetime
    participant_role: str
    participant_anonymized_id: Optional[str] = None
    interview_notes: str
    researcher_bias_notes: Optional[str] = None
    key_quotes: List[str] = []

@router.post("/teams/{team_id}/interviews", response_model=Interview)
async def create_interview(
    team_id: int, 
    interview_data: InterviewCreate, 
    session: AsyncSession = Depends(get_session)
):
    db_interview = Interview.from_orm(interview_data)
    db_interview.team_id = team_id
    session.add(db_interview)
    await session.commit()
    await session.refresh(db_interview)
    return db_interview

@router.get("/teams/{team_id}/interviews", response_model=List[Interview])
async def get_interviews(team_id: int, session: AsyncSession = Depends(get_session)):
    statement = select(Interview).where(Interview.team_id == team_id)
    result = await session.execute(statement)
    return result.scalars().all()

@router.post("/teams/{team_id}/interviews/{interview_id}/analyze", response_model=Interview)
async def analyze_interview(
    team_id: int, 
    interview_id: int, 
    session: AsyncSession = Depends(get_session)
):
    interview = await session.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    try:
        insights_data = await ai_service.extract_anrum(interview.interview_notes)
        interview.insights_extracted = insights_data
        session.add(interview)
        await session.commit()
        await session.refresh(interview)
        return interview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
