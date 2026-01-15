from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

from sqlalchemy import Column, TIMESTAMP

class Team(SQLModel, table=True):
    __tablename__ = "teams"
    
    team_id: Optional[int] = Field(default=None, primary_key=True)
    team_name: str
    project_focus: str
    created_date: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP(timezone=True)))
