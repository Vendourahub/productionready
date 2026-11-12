"""Reviewer sign-off Pydantic schemas for $299 audit package."""
from typing import Optional
from pydantic import BaseModel, Field


class ReviewerSignoffRequest(BaseModel):
    reviewer_name: str = Field(..., example="Jane Doe, Lead AppSec Auditor")
    reviewer_status: str = Field("approved", pattern="^(approved|changes_requested|pending)$")
    reviewer_notes: Optional[str] = Field(None, example="Manual code review confirmed RLS and webhook signatures.")
