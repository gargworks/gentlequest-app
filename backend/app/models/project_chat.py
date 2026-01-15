from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class ProjectChatSession(SQLModel, table=True):
    session_id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(index=True) # Changed from project_id
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    title: str = Field(default="New Chat")

class ProjectChatMessage(SQLModel, table=True):
    message_id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="projectchatsession.session_id")
    role: str # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

