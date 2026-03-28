import logging

from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timezone

from app.database import get_session
from app.models.cvp import CVPCanvas
from app.models.persona import Persona
from app.schemas.cvp_schema import CVPCreate, CVPRead
from app.dependencies import get_ai_service
from app.services.ai_insights_service import AIInsightsService

router = APIRouter(tags=["cvp"])

@router.get("/teams/{teamid}/cvp", response_model=CVPRead)
async def get_team_cvp(teamid: int, session: AsyncSession = Depends(get_session)):
    query = select(CVPCanvas).where(CVPCanvas.teamid == teamid).order_by(CVPCanvas.lastupdated.desc())
    result = await session.execute(query)
    cvp = result.scalars().first()
    if not cvp:
        raise HTTPException(status_code=404, detail="CVP Canvas not found for this team")
    return cvp

@router.post("/teams/{teamid}/cvp", response_model=CVPRead, status_code=status.HTTP_201_CREATED)
async def upsert_team_cvp(teamid: int, cvp_data: CVPCreate, session: AsyncSession = Depends(get_session)):
    # Check if a CVP already exists to update it (keeping it "Single Current")
    query = select(CVPCanvas).where(CVPCanvas.teamid == teamid)
    result = await session.execute(query)
    cvp = result.scalars().first()
    
    if cvp:
        # Update existing
        for key, value in cvp_data.model_dump().items():
            setattr(cvp, key, value)
        cvp.lastupdated = datetime.now(timezone.utc)
    else:
        # Create new
        cvp = CVPCanvas(**cvp_data.model_dump(), teamid=teamid)
        session.add(cvp)
    
    await session.commit()
    await session.refresh(cvp)
    return cvp

@router.post("/teams/{teamid}/cvp/generate", response_model=CVPRead)
async def generate_team_cvp(
    teamid: int, 
    session: AsyncSession = Depends(get_session),
    ai_service: AIInsightsService = Depends(get_ai_service)
):
    # 1. Fetch all Personas for the team to provide context
    persona_query = select(Persona).where(Persona.team_id == teamid)
    result = await session.execute(persona_query)
    personas = result.scalars().all()
    
    if not personas:
        raise HTTPException(
            status_code=400, 
            detail="No personas found for this team. Generate personas first."
        )
    
    # 2. Call AI Service to synthesize CVP
    try:
        cvp_generated_dict = await ai_service.generate_cvp(personas)
        cvp_generated = CVPCreate(**cvp_generated_dict)
    except Exception as e:
        logger.error("CVP generation failed for team %d: %s", teamid, e)
        raise HTTPException(status_code=500, detail="AI synthesis failed. Please try again.")
    
    # 3. Save/Update CVP (Reuse logic from POST)
    query = select(CVPCanvas).where(CVPCanvas.teamid == teamid)
    result = await session.execute(query)
    cvp = result.scalars().first()
    
    if cvp:
        for key, value in cvp_generated.model_dump().items():
            setattr(cvp, key, value)
        cvp.lastupdated = datetime.now(timezone.utc)
    else:
        cvp = CVPCanvas(**cvp_generated.model_dump(), teamid=teamid)
        session.add(cvp)
        
    await session.commit()
    await session.refresh(cvp)
    return cvp
