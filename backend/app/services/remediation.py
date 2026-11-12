"""Remediation workflow services: resolution, acceptance, and reassessment."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from ..models import Finding, Assessment, AuditEvent, Project
from .runner import execute_assessment


def update_finding_status(
    db: Session,
    finding_id: str,
    new_status: str,
    notes: Optional[str] = None,
    actor: str = "user",
) -> Finding:
    """Updates the resolution status of a finding with an audit log record."""
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise ValueError(f"Finding '{finding_id}' not found.")

    old_status = finding.status
    finding.status = new_status
    finding.resolution_notes = notes
    if new_status in ("RESOLVED", "ACCEPTED_RISK"):
        finding.resolved_at = datetime.now(timezone.utc)
    else:
        finding.resolved_at = None

    # Log audit event
    audit = AuditEvent(
        assessment_id=finding.assessment_id,
        event_type="finding_status_updated",
        actor=actor,
        payload_json=json.dumps({
            "finding_id": finding.id,
            "rule_id": finding.rule_id,
            "old_status": old_status,
            "new_status": new_status,
            "notes": notes,
        }),
    )
    db.add(audit)
    db.commit()
    db.refresh(finding)
    return finding


def request_reassessment(
    db: Session,
    assessment_id: str,
    commit_sha: Optional[str] = None,
    ref: Optional[str] = None,
    github_token: Optional[str] = None,
) -> Assessment:
    """Creates a new assessment cycle to verify fixes pushed for open findings."""
    previous = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not previous:
        raise ValueError(f"Assessment '{assessment_id}' not found.")

    new_assessment = Assessment(
        project_id=previous.project_id,
        commit_sha=commit_sha or previous.commit_sha,
        target_type=previous.target_type,
        status="queued",
    )
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)

    # Log audit event on previous assessment
    db.add(
        AuditEvent(
            assessment_id=previous.id,
            event_type="reassessment_requested",
            actor="user",
            payload_json=json.dumps({"new_assessment_id": new_assessment.id}),
        )
    )
    db.commit()

    # Trigger scan execution synchronously or in worker
    return execute_assessment(
        db=db,
        assessment_id=new_assessment.id,
        github_token=github_token,
        ref=ref,
    )
