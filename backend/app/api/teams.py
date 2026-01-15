from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models.team import Team
from app.models.interview import Interview
from app.schemas.team_schema import TeamCreate, TeamRead
from app.schemas.interview_schema import InterviewCreate, InterviewRead

router = APIRouter()

@router.post("/teams", response_model=TeamRead)
async def create_team(team: TeamCreate, session: AsyncSession = Depends(get_session)):
    db_team = Team.model_validate(team)
    session.add(db_team)
    await session.commit()
    await session.refresh(db_team)
    return db_team

@router.post("/teams/{team_id}/interviews", response_model=InterviewRead)
async def create_interview(team_id: int, interview: InterviewCreate, session: AsyncSession = Depends(get_session)):
    # Verify team exists
    if not await session.get(Team, team_id):
         raise HTTPException(status_code=404, detail="Team not found")
         
    # db_interview = Interview.model_validate(interview)
    # Manual creation since Schema lacks team_id but Model requires it
    data = interview.model_dump()
    db_interview = Interview(**data, team_id=team_id)
    session.add(db_interview)
    await session.commit()
    await session.refresh(db_interview)
    return db_interview

@router.get("/teams/{team_id}/interviews", response_model=List[InterviewRead])
async def list_interviews(team_id: int, session: AsyncSession = Depends(get_session)):
    statement = select(Interview).where(Interview.team_id == team_id)
    result = await session.execute(statement)
    return result.scalars().all()

@router.get("/teams", response_model=List[TeamRead])
async def list_teams(session: AsyncSession = Depends(get_session)):
    statement = select(Team)
    result = await session.execute(statement)
    return result.scalars().all()
