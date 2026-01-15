from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import TIMESTAMP

class MVPRoadmap(SQLModel, table=True):
    __tablename__ = "mvp_roadmaps"
    
    roadmap_id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="teams.team_id", index=True)
    vision_statement: str
    
    created_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True))
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True))
    )
    
    features: List["MVPFeature"] = Relationship(back_populates="roadmap")

class MVPFeature(SQLModel, table=True):
    __tablename__ = "mvp_features"
    
    feature_id: Optional[int] = Field(default=None, primary_key=True)
    roadmap_id: int = Field(foreign_key="mvp_roadmaps.roadmap_id", index=True)
    
    title: str
    description: str
    priority: str  # MUST_HAVE, SHOULD_HAVE, COULD_HAVE, WONT_HAVE
    complexity: str # LOW, MEDIUM, HIGH
    rationale: str
    related_cvp_element: str
    
    roadmap: Optional[MVPRoadmap] = Relationship(back_populates="features")
