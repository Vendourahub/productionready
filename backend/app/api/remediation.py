"""Remediation and finding status management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import verify_api_key
from ..models import Finding, Assessment
from ..schemas.finding import FindingResponse, FindingStatusUpdate
from ..schemas.assessment import AssessmentResponse
from ..services.remediation import update_finding_status, request_reassessment

router = APIRouter(tags=["Remediation"], dependencies=[Depends(verify_api_key)])


@router.patch("/api/findings/{finding_id}/status", response_model=FindingResponse)
def change_finding_status(
    finding_id: str,
    data: FindingStatusUpdate,
    db: Session = Depends(get_db),
):
    """Updates the remediation status of a finding (OPEN, RESOLVED, ACCEPTED_RISK)."""
    try:
        updated = update_finding_status(
            db=db,
            finding_id=finding_id,
            new_status=data.status,
            notes=data.resolution_notes,
            actor="dashboard_user",
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/assessments/{assessment_id}/reassessment", response_model=AssessmentResponse)
def trigger_reassessment(
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """Triggers a clean reassessment cycle to verify that resolved issues pass."""
    try:
        new_assessment = request_reassessment(
            db=db,
            assessment_id=assessment_id,
        )
        return new_assessment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reassessment failed: {str(e)}")
