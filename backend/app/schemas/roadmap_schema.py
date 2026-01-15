from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class MVPFeatureBase(BaseModel):
    title: str
    description: str
    priority: str
    complexity: str
    rationale: str
    relatedcvpelement: str = Field(alias="related_cvp_element")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class MVPFeatureCreate(MVPFeatureBase):
    pass

class MVPFeatureRead(MVPFeatureBase):
    featureid: int = Field(alias="feature_id")
    roadmapid: int = Field(alias="roadmap_id")

class MVPRoadmapBase(BaseModel):
    visionstatement: str = Field(alias="vision_statement")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class MVPRoadmapCreate(MVPRoadmapBase):
    features: List[MVPFeatureCreate]

class MVPRoadmapRead(MVPRoadmapBase):
    roadmapid: int = Field(alias="roadmap_id")
    teamid: int = Field(alias="team_id")
    createddate: datetime = Field(alias="created_date")
    lastupdated: datetime = Field(alias="last_updated")
    features: List[MVPFeatureRead] = []
