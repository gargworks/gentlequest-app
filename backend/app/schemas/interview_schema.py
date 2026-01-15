from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class InterviewCreate(BaseModel):
    # team_id removed (supplied by path)
    interview_date: datetime = Field(alias="interviewdate")
    participant_role: str = Field(alias="participantrole")
    interview_notes: str = Field(alias="interviewnotes")
    participant_anonymized_id: Optional[str] = None
    researcher_bias_notes: Optional[str] = None

class InterviewRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    interview_id: int = Field(alias="interviewid")
    team_id: int = Field(alias="teamid")
    interview_date: datetime = Field(alias="interviewdate")
    participant_role: str = Field(alias="participantrole")
    participant_anonymized_id: Optional[str] = Field(default=None, alias="participantanonymizedid")
    interview_notes: str = Field(alias="interviewnotes")
    key_quotes: List[str] = Field(default=[], alias="keyquotes")
    insights_extracted: List[Dict[str, Any]] = Field(default=[], alias="insightsextracted")
    researcher_bias_notes: Optional[str] = Field(default=None, alias="researcherbiasnotes")
    created_date: datetime = Field(alias="createddate")
