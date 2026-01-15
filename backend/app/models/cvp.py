from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, TIMESTAMP

class CVPCanvas(SQLModel, table=True):
    __tablename__ = "cvp_canvas"
    
    cvpid: Optional[int] = Field(default=None, primary_key=True)
    teamid: int = Field(foreign_key="teams.team_id", index=True)
    
    customersegment: str
    jobstobedone: List[str] = Field(default=[], sa_column=Column(JSON))
    valueproposition: str
    
    pains: List[str] = Field(default=[], sa_column=Column(JSON))
    gains: List[str] = Field(default=[], sa_column=Column(JSON))
    
    painrelievers: List[str] = Field(default=[], sa_column=Column(JSON))
    gaincreators: List[str] = Field(default=[], sa_column=Column(JSON))
    
    competitivepositioning: str
    
    createddate: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True))
    )
    lastupdated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True))
    )

