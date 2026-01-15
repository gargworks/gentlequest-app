from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP

class Persona(SQLModel, table=True):
    # Primary Key
    persona_id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Key
    team_id: int = Field(index=True)
    
    # Core Persona Fields
    name: str
    age: Optional[int] = None
    context: Optional[str] = None
    environment: Optional[str] = None
    
    # Lists (using Postgres ARRAY)
    goals: List[str] = Field(default=[], sa_column=Column(ARRAY(String))) # Error: String not imported? Need JSONB or ARRAY(String)
    # Actually, SQLModel + Postgres Arrays can be tricky. Using JSONB is safer for flexibility if simple ARRAY(String) fails with some drivers, 
    # BUT standard SQLAlchemy ARRAY works well with asyncpg.
    # Let's use JSONB for lists to be safe and consistent with previous choices, or ARRAY?
    # api_schemas.json defines them as arrays of strings. 
    # Let's use ARRAY(String) if valid, else JSONB. 
    # Previously used JSONB for `insights_extracted`.
    # Let's use JSONB for complex lists, but `goals`, `frustrations` are simple string lists.
    # ARRAY(String) is efficient.
    
    goals: List[str] = Field(default=[], sa_column=Column(JSONB)) 
    frustrations: List[str] = Field(default=[], sa_column=Column(JSONB))
    behaviors: List[str] = Field(default=[], sa_column=Column(JSONB))
    motivations: List[str] = Field(default=[], sa_column=Column(JSONB))
    barriers: List[str] = Field(default=[], sa_column=Column(JSONB))
    supporting_quotes: List[str] = Field(default=[], sa_column=Column(JSONB))
    
    # Traceability
    supporting_interview_ids: List[int] = Field(default=[], sa_column=Column(JSONB))
    
    # Audit
    created_date: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True))
    )

# Correction: Import String if using ARRAY, but JSONB handles List[str] serialization automatically in Pydantic models usually.
# Let's stick to JSONB for all "Array" fields to avoid "type 'List[str]' doesn't match" errors.
# Re-writing code content below cleanly.
