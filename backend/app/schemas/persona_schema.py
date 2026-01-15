from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class PersonaCreate(BaseModel):
    name: str = Field(alias="name")
    age: Optional[int] = Field(default=None, alias="age")
    context: Optional[str] = Field(default=None, alias="context")
    goals: List[str] = Field(default=[], alias="goals")
    frustrations: List[str] = Field(default=[], alias="frustrations")
    behaviors: List[str] = Field(default=[], alias="behaviors")
    motivations: List[str] = Field(default=[], alias="motivations")
    barriers: List[str] = Field(default=[], alias="barriers")
    environment: Optional[str] = Field(default=None, alias="environment")
    supporting_quotes: List[str] = Field(default=[], alias="supportingquotes")
    supporting_interview_ids: List[int] = Field(default=[], alias="supportinginterviewids")

    model_config = ConfigDict(populate_by_name=True)

class PersonaRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    persona_id: int = Field(alias="personaid")
    team_id: int = Field(alias="teamid")
    name: str = Field(alias="name")
    age: Optional[int] = Field(alias="age")
    context: Optional[str] = Field(alias="context")
    goals: List[str] = Field(alias="goals")
    frustrations: List[str] = Field(alias="frustrations")
    behaviors: List[str] = Field(alias="behaviors")
    motivations: List[str] = Field(alias="motivations")
    barriers: List[str] = Field(alias="barriers")
    environment: Optional[str] = Field(alias="environment")
    supporting_quotes: List[str] = Field(alias="supportingquotes")
    supporting_interview_ids: List[int] = Field(alias="supportinginterviewids")
    created_date: datetime = Field(alias="createddate")
