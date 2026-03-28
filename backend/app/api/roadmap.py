import logging

from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timezone

from app.database import get_session
from app.models.roadmap import MVPRoadmap, MVPFeature
from app.models.cvp import CVPCanvas
from app.schemas.roadmap_schema import MVPRoadmapRead, MVPRoadmapCreate, MVPFeatureCreate, MVPFeatureRead
from app.dependencies import get_ai_service
from app.services.ai_insights_service import AIInsightsService

router = APIRouter(tags=["roadmap"])

@router.get("/teams/{teamid}/roadmap", response_model=MVPRoadmapRead)
async def get_team_roadmap(teamid: int, session: AsyncSession = Depends(get_session)):
    query = select(MVPRoadmap).where(MVPRoadmap.team_id == teamid).order_by(MVPRoadmap.last_updated.desc())
    result = await session.execute(query)
    roadmap = result.scalars().first()
    
    if not roadmap:
        raise HTTPException(status_code=404, detail="MVP Roadmap not found for this team")
    
    # Eager load features manually if needed, or rely on lazy loading/default loading depending on SA configuration.
    # For SQLModel with AsyncSession, we often need to explicit load or join.
    # But let's try a simple fetch of features.
    features_query = select(MVPFeature).where(MVPFeature.roadmap_id == roadmap.roadmap_id)
    features_result = await session.execute(features_query)
    features_list = features_result.scalars().all()
    
    return MVPRoadmapRead(
        roadmap_id=roadmap.roadmap_id,
        team_id=roadmap.team_id,
        vision_statement=roadmap.vision_statement,
        created_date=roadmap.created_date,
        last_updated=roadmap.last_updated,
        features=[
            MVPFeatureRead(
                featureid=f.feature_id,
                roadmapid=f.roadmap_id,
                title=f.title,
                description=f.description,
                priority=f.priority,
                complexity=f.complexity,
                rationale=f.rationale,
                relatedcvpelement=f.related_cvp_element
            ) for f in features_list
        ]
    )

@router.post("/teams/{teamid}/roadmap/generate", response_model=MVPRoadmapRead)
async def generate_team_roadmap(
    teamid: int, 
    session: AsyncSession = Depends(get_session),
    ai_service: AIInsightsService = Depends(get_ai_service)
):
    # 1. Fetch CVP for context
    cvp_query = select(CVPCanvas).where(CVPCanvas.teamid == teamid).order_by(CVPCanvas.lastupdated.desc())
    result = await session.execute(cvp_query)
    cvp = result.scalars().first()
    
    if not cvp:
        raise HTTPException(
            status_code=400, 
            detail="No CVP Canvas found for this team. Generate CVP first."
        )
    
    # 2. Synthesize Roadmap via AI
    try:
        roadmap_dict = await ai_service.generate_mvp_roadmap(cvp)
    except Exception as e:
        logger.error("Roadmap generation failed for team %d: %s", teamid, e)
        raise HTTPException(status_code=500, detail="AI synthesis failed. Please try again.")
    
    # 3. Save Roadmap and Features
    # Check for existing roadmap to update or create new? 
    # For now, let's assume one roadmap per team (Single Current)
    
    query = select(MVPRoadmap).where(MVPRoadmap.team_id == teamid)
    result = await session.execute(query)
    existing_roadmap = result.scalars().first()
    
    if existing_roadmap:
        # Update vision
        existing_roadmap.vision_statement = roadmap_dict.get("vision_statement")
        existing_roadmap.last_updated = datetime.now(timezone.utc)
        
        # Clear old features? Or append? 
        # Strategy: Wipe and Replace for "Generate" action to keep it clean with the new CVP.
        # Ideally we'd archive, but MVP simplicity first.
        delete_features_query = select(MVPFeature).where(MVPFeature.roadmap_id == existing_roadmap.roadmap_id)
        # Delete properly via session execute delete
        # For simplicity in async sqlmodel, manual fetch and delete
        feats_res = await session.execute(delete_features_query)
        feats = feats_res.scalars().all()
        for f in feats:
            await session.delete(f)
            
        current_roadmap = existing_roadmap
    else:
        current_roadmap = MVPRoadmap(
            team_id=teamid, 
            vision_statement=roadmap_dict.get("vision_statement")
        )
        session.add(current_roadmap)
        await session.flush() # to get generated id
        await session.refresh(current_roadmap)

    # Add Features
    features_data = roadmap_dict.get("features", [])
    new_features = []
    
    for f_data in features_data:
        # Normalize keys for robustness (handle alias vs snake_case)
        # Fixes 500 error if LLM returns "relatedcvpelement" vs "related_cvp_element"
        related_cvp = f_data.get("related_cvp_element") or f_data.get("relatedcvpelement") or ""
        
        feat = MVPFeature(
            roadmap_id=current_roadmap.roadmap_id,
            title=f_data.get("title", "Untitled Feature"),
            description=f_data.get("description", ""),
            priority=f_data.get("priority", "COULD_HAVE"),
            complexity=f_data.get("complexity", "MEDIUM"),
            rationale=f_data.get("rationale", ""),
            related_cvp_element=related_cvp
        )
        session.add(feat)
        new_features.append(feat)

    await session.commit()
    await session.refresh(current_roadmap)
    
    # Explicitly construct response to avoid MissingGreenlet on lazy load
    return MVPRoadmapRead(
        roadmap_id=current_roadmap.roadmap_id,
        team_id=current_roadmap.team_id,
        vision_statement=current_roadmap.vision_statement,
        created_date=current_roadmap.created_date,
        last_updated=current_roadmap.last_updated,
        features=[
        MVPFeatureRead(
            featureid=f.feature_id,
            roadmapid=f.roadmap_id,
            title=f.title,
            description=f.description,
            priority=f.priority,
            complexity=f.complexity,
            rationale=f.rationale,
            relatedcvpelement=f.related_cvp_element
        ) for f in new_features
    ]
    )

