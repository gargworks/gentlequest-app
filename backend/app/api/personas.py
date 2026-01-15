from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models.persona import Persona
from app.models.team import Team
from app.schemas.persona_schema import PersonaCreate, PersonaRead

router = APIRouter()

@router.post("/teams/{team_id}/personas", response_model=PersonaRead, status_code=201)
async def create_persona(team_id: int, persona: PersonaCreate, session: AsyncSession = Depends(get_session)):
    # Verify team exists
    if not await session.get(Team, team_id):
         raise HTTPException(status_code=404, detail="Team not found")
    
    # Create Persona (Inject team_id)
    # Using model_dump to handle aliases -> internal mapping if naming matches
    # But PersonaCreate has standard snake_case field names (with aliases).
    # SQLModel has standard snake_case field names.
    # So model_dump() should work perfectly.
    data = persona.model_dump()
    db_persona = Persona(**data, team_id=team_id)
    session.add(db_persona)
    await session.commit()
    await session.refresh(db_persona)
    return db_persona

@router.get("/teams/{team_id}/personas", response_model=List[PersonaRead])
async def list_personas(team_id: int, session: AsyncSession = Depends(get_session)):
    statement = select(Persona).where(Persona.team_id == team_id)
    result = await session.execute(statement)
    return result.scalars().all()

from app.models.interview import Interview
from app.dependencies import get_ai_service
from app.services.ai_insights_service import AIInsightsService

@router.post("/teams/{team_id}/personas/generate", response_model=List[PersonaRead])
async def generate_personas(
    team_id: int, 
    session: AsyncSession = Depends(get_session),
    service: AIInsightsService = Depends(get_ai_service)
):
    # 1. Fetch all interviews
    statement = select(Interview).where(Interview.team_id == team_id)
    result = await session.execute(statement)
    interviews = result.scalars().all()
    
    if not interviews:
        return []

    # 2. Prepare Data
    interviews_data = []
    for i in interviews:
        interviews_data.append({
            "id": i.interview_id,
            "notes": i.interview_notes,
            "insights": i.insights_extracted
        })
        
    # 3. Call LLM
    generated_personas_data = await service.generate_personas(interviews_data)
    
    # 4. Save to DB
    saved_personas = []
    for p_data in generated_personas_data:
        # Validate using Pydantic Schema manually?
        # Or just create Model directy if trusted? 
        # Better to validate via PersonaCreate to strip unknowns
        try:
             # Map keys if needed? LLM prompt asked for snake_case keys or strict JSON? 
             # Prompt said: "supportingquotes", "supportinginterviewids".
             # PersonaCreate expects: `supporting_quotes` (alias supportingquotes).
             # pydantic `model_validate(p_data)` might fail if keys are aliases and populate_by_name is not set on CREATE schema?
             # PersonaCreate doesn't have ConfigDict(populate_by_name=True).
             # But `alias` works for Input.
             # So if LLM returns `{"supportingquotes": [...]}` -> PersonaCreate(supporting_quotes=...) works.
             # Yes.
             
             persona_in = PersonaCreate.model_validate(p_data)
             db_persona = Persona(**persona_in.model_dump(), team_id=team_id)
             session.add(db_persona)
             saved_personas.append(db_persona)
        except Exception as e:
            print(f"Skipping invalid persona data: {e}")
            continue
            
    if saved_personas:
        await session.commit()
        for p in saved_personas:
            await session.refresh(p)
            
    return saved_personas
