"""Assessments and reports API endpoints."""
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import verify_api_key
from ..models import Assessment, Project, Finding, VerificationItem
from ..schemas.assessment import AssessmentCreate, AssessmentResponse, AssessmentDetailResponse
from ..schemas.review import ReviewerSignoffRequest
from ..services.runner import execute_assessment, run_assessment_background

router = APIRouter(tags=["Assessments"], dependencies=[Depends(verify_api_key)])


@router.post(
    "/api/projects/{project_id}/assessments",
    response_model=AssessmentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_assessment(
    project_id: str,
    data: AssessmentCreate,
    background_tasks: BackgroundTasks,
    sync: bool = Query(False, description="Whether to execute synchronously instead of queuing in background"),
    db: Session = Depends(get_db),
):
    """Triggers an ephemeral assessment against the project repository.

    By default runs asynchronously in background queue returning HTTP 202 immediately.
    Set sync=true for synchronous completion.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    assessment = Assessment(
        project_id=project.id,
        commit_sha=data.commit_sha,
        status="queued",
        reviewer_name=data.reviewer_name,
        reviewer_notes=data.reviewer_notes,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    target_ref = data.ref or project.default_branch or "main"

    if sync:
        try:
            completed = execute_assessment(
                db=db,
                assessment_id=assessment.id,
                github_token=data.github_token,
                ref=target_ref,
                reviewer_name=data.reviewer_name,
                reviewer_notes=data.reviewer_notes,
            )
            return completed
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")

    # Non-blocking async queue
    background_tasks.add_task(
        run_assessment_background,
        assessment_id=assessment.id,
        github_token=data.github_token,
        ref=target_ref,
        reviewer_name=data.reviewer_name,
        reviewer_notes=data.reviewer_notes,
    )
    return assessment


@router.get("/api/projects/{project_id}/assessments", response_model=List[AssessmentResponse])
def list_project_assessments(project_id: str, db: Session = Depends(get_db)):
    """Lists all historical assessments for a project."""
    assessments = (
        db.query(Assessment)
        .filter(Assessment.project_id == project_id)
        .order_by(Assessment.created_at.desc())
        .all()
    )
    return assessments


@router.get("/api/assessments/{assessment_id}", response_model=AssessmentDetailResponse)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Retrieves detailed assessment results, including findings and ASVS ledger."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return assessment


@router.get("/api/assessments/{assessment_id}/report.html", response_class=HTMLResponse)
def download_html_report(assessment_id: str, db: Session = Depends(get_db)):
    """Serves the rendered executive HTML assessment report."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment or not assessment.html_report_path:
        raise HTTPException(status_code=404, detail="Report not generated.")
    path = Path(assessment.html_report_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk.")
    return HTMLResponse(content=path.read_text(encoding="utf-8"))


@router.get("/api/assessments/{assessment_id}/report.json")
def download_json_report(assessment_id: str, db: Session = Depends(get_db)):
    """Downloads the structured JSON assessment data."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment or not assessment.json_report_path:
        raise HTTPException(status_code=404, detail="Report not generated.")
    path = Path(assessment.json_report_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk.")
    return FileResponse(path=path, media_type="application/json", filename=f"productionready-{assessment.id}.json")


@router.post("/api/assessments/{assessment_id}/review", response_model=AssessmentResponse)
def submit_reviewer_signoff(assessment_id: str, data: ReviewerSignoffRequest, db: Session = Depends(get_db)):
    """Applies a human auditor verification sign-off ($299 package deliverable)."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    assessment.reviewer_name = data.reviewer_name
    assessment.reviewer_status = data.reviewer_status
    assessment.reviewer_notes = data.reviewer_notes
    db.commit()
    db.refresh(assessment)
    return assessment
