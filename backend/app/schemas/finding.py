"""Finding and remediation Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FindingStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(OPEN|RESOLVED|ACCEPTED_RISK)$", example="RESOLVED")
    resolution_notes: Optional[str] = Field(None, example="Enabled RLS and added tenant isolation policy.")


class FindingResponse(BaseModel):
    id: str
    assessment_id: str
    rule_id: str
    asvs_id: str
    severity: str
    title: str
    location: str
    line: Optional[int]
    evidence: str
    remediation: str
    remediation_diff: Optional[str] = None
    status: str
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
