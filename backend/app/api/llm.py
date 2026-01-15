from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models.interview import Interview
from app.services.ai_insights_service import AIInsightsService
from typing import List, Dict, Any

router = APIRouter()
ai_service = AIInsightsService()

@router.post("/teams/{team_id}/interviews/{interview_id}/analyze")
async def analyze_interview(
    team_id: int, 
    interview_id: int, 
    session: AsyncSession = Depends(get_session)
):
    # Fetch interview
    interview = await session.get(Interview, interview_id)
    if not interview or interview.team_id != team_id:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Call LLM
    insights = await ai_service.extract_anrum(interview.interview_notes)
    
    # Update DB
    # Ensure insights is a list of dicts compatible with JSONB
    interview.insights_extracted = insights
    session.add(interview)
    await session.commit()
    await session.refresh(interview)
    
    return {"status": "success", "insights_count": len(insights), "data": insights}
