"""Assessment Pydantic schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from .finding import FindingResponse
from .verification import VerificationItemResponse


class AssessmentCreate(BaseModel):
    commit_sha: Optional[str] = Field(None, example="a1b2c3d4")
    ref: Optional[str] = Field("main", example="main")
    github_token: Optional[str] = Field(None, example="ghp_...")
    reviewer_name: Optional[str] = None
    reviewer_notes: Optional[str] = None


class AssessmentResponse(BaseModel):
    id: str
    project_id: str
    commit_sha: Optional[str]
    target_type: str
    status: str
    readiness_status: str
    blockers_count: int
    total_findings_count: int
    verified_controls_count: int
    unverified_gaps_count: int
    reviewer_name: Optional[str]
    reviewer_status: str
    reviewer_notes: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AssessmentDetailResponse(AssessmentResponse):
    findings: List[FindingResponse] = []
    verification_items: List[VerificationItemResponse] = []
