"""Project Pydantic schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., example="Client SaaS Portal")
    repository_url: str = Field(..., example="https://github.com/agency/client-app")
    default_branch: str = Field("main", example="main")


class ProjectResponse(BaseModel):
    id: str
    name: str
    repository_url: str
    default_branch: str
    created_at: datetime
    updated_at: datetime
    latest_assessment_status: Optional[str] = None
    latest_readiness_status: Optional[str] = None

    class Config:
        from_attributes = True
