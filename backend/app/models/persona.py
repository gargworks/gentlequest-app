from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON, TIMESTAMP

class Persona(SQLModel, table=True):
    persona_id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(index=True)
    
    name: str
    age: Optional[int] = None
    context: Optional[str] = None
    
    # JSON List Fields (DB-agnostic)
    goals: List[str] = Field(default=[], sa_column=Column(JSON))
    frustrations: List[str] = Field(default=[], sa_column=Column(JSON))
    behaviors: List[str] = Field(default=[], sa_column=Column(JSON))
    motivations: List[str] = Field(default=[], sa_column=Column(JSON))
    barriers: List[str] = Field(default=[], sa_column=Column(JSON))
    environment: Optional[str] = None
    
    # Traceability
    supporting_quotes: List[str] = Field(default=[], sa_column=Column(JSON))
    supporting_interview_ids: List[int] = Field(default=[], sa_column=Column(JSON))
    
    created_date: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True))
    )

