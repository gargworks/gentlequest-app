from datetime import datetime
from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator

class CVPBase(BaseModel):
    customersegment: str = Field(alias="customersegment")
    jobstobedone: Union[List[str], str] = Field(default=[], alias="jobstobedone")
    valueproposition: str = Field(alias="valueproposition")
    pains: List[str] = Field(default=[], alias="pains")
    gains: List[str] = Field(default=[], alias="gains")
    painrelievers: List[str] = Field(default=[], alias="painrelievers")
    gaincreators: List[str] = Field(default=[], alias="gaincreators")
    competitivepositioning: str = Field(alias="competitivepositioning")

    @field_validator('jobstobedone', mode='before')
    @classmethod
    def normalize_to_list(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        return []

class CVPCreate(CVPBase):
    pass

class CVPRead(CVPBase):
    cvpid: int = Field(alias="cvpid")
    teamid: int = Field(alias="teamid")
    createddate: datetime = Field(alias="createddate")
    lastupdated: datetime = Field(alias="lastupdated")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
