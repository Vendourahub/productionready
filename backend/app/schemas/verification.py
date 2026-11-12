"""Verification ledger Pydantic schemas."""
from pydantic import BaseModel


class VerificationItemResponse(BaseModel):
    id: str
    assessment_id: str
    asvs_id: str
    category: str
    requirement: str
    status: str
    verification_method: str
    evidence_or_reason: str

    class Config:
        from_attributes = True
