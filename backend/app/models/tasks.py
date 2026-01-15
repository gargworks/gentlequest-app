from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"

class ProjectTaskBase(SQLModel):
    team_id: int = Field(index=True)
    roadmap_id: Optional[int] = Field(default=None, foreign_key="mvp_roadmaps.roadmap_id")
    feature_id: Optional[int] = Field(default=None, foreign_key="mvp_features.feature_id") # Link to specific feature if granular
    title: str
    description: str
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: str = "MEDIUM" # HIGH, MEDIUM, LOW
    estimated_hours: Optional[int] = None
    assignee_role: Optional[str] = None # e.g. "Frontend Dev", "Backend Dev"
    
class ProjectTask(ProjectTaskBase, table=True):
    __tablename__ = "project_tasks"
    task_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectTaskCreate(ProjectTaskBase):
    pass

class ProjectTaskRead(ProjectTaskBase):
    task_id: int
    created_at: datetime
    updated_at: datetime
