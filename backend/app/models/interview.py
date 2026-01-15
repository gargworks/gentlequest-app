from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, Integer, TIMESTAMP, JSON, TEXT

class Interview(SQLModel, table=True):
    __tablename__ = "interviews"
    
    interview_id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(index=True)
    interview_date: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True)))
    participant_role: str
    participant_anonymized_id: Optional[str] = None
    interview_notes: str = Field(sa_column=Column(TEXT))
    key_quotes: List[str] = Field(default=[], sa_column=Column(JSON))
    
    # Store ANRUM insights as JSON (DB-agnostic)
    insights_extracted: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    
    researcher_bias_notes: Optional[str] = None
    created_date: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP(timezone=True)))

