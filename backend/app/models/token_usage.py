from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, TIMESTAMP


class TokenUsage(SQLModel, table=True):
    __tablename__ = "iip_token_usage"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(index=True)
    message_id: Optional[int] = Field(default=None)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True)),
    )
