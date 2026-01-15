from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class TeamCreate(BaseModel):
    team_name: str = Field(alias="teamname")
    project_focus: str = Field(alias="projectfocus")

class TeamRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    team_id: int = Field(alias="teamid")
    team_name: str = Field(alias="teamname")
    project_focus: str = Field(alias="projectfocus")
    created_date: datetime = Field(alias="createddate")
