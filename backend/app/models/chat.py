from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, TIMESTAMP, TEXT

class InterviewSession(SQLModel, table=True):
    __tablename__ = "iip_interview_sessions"
    
    session_id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(index=True)
    status: str = Field(default="ACTIVE") # ACTIVE, COMPLETED
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP(timezone=True)))
    
    messages: List["ChatMessage"] = Relationship(back_populates="session")

class ChatMessage(SQLModel, table=True):
    __tablename__ = "iip_chat_messages"
    
    message_id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="iip_interview_sessions.session_id", index=True)
    role: str # "user" or "assistant"
    content: str = Field(sa_column=Column(TEXT))
    timestamp: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(TIMESTAMP(timezone=True)))
    
    session: Optional[InterviewSession] = Relationship(back_populates="messages")
