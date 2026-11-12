"""Assessment execution runner and report generator."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

# Ensure productionready_starter is on sys.path
STARTER_DIR = Path(__file__).resolve().parent.parent.parent.parent / "productionready_starter"
if str(STARTER_DIR) not in sys.path:
    sys.path.insert(0, str(STARTER_DIR))

from productionready.scanner import scan, render_html
from productionready.intake import intake_repository

from ..models import Assessment, Finding, VerificationItem, AuditEvent, Project
from ..config import settings


def execute_assessment(
    db: Session,
    assessment_id: str,
    github_token: Optional[str] = None,
    ref: Optional[str] = None,
    reviewer_name: Optional[str] = None,
    reviewer_notes: Optional[str] = None,
) -> Assessment:
    """Executes a full security assessment against the project repository."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise ValueError(f"Assessment '{assessment_id}' not found.")

    project = db.query(Project).filter(Project.id == assessment.project_id).first()
    if not project:
        raise ValueError(f"Project for assessment '{assessment_id}' not found.")

    assessment.status = "running"
    db.commit()

    try:
        target_ref = ref or project.default_branch or "main"
        
        # Ephemeral intake with zero code retention
        with intake_repository(project.repository_url, github_token=github_token, ref=target_ref) as (repo_path, intake_type, commit_sha):
            # Run the deterministic multi-rule inspection
            report = scan(
                root=repo_path,
                target_type=intake_type,
                commit_sha=commit_sha or assessment.commit_sha,
                reviewer_name=reviewer_name or assessment.reviewer_name,
                reviewer_notes=reviewer_notes or assessment.reviewer_notes,
            )
            report["target"] = project.repository_url

            # Persist findings into database
            assessment.findings.clear()
            for f in report["findings"]:
                finding_row = Finding(
                    assessment_id=assessment.id,
                    rule_id=f["rule_id"],
                    asvs_id=f["asvs_id"],
                    severity=f["severity"],
                    title=f["title"],
                    location=f["location"],
                    line=f["line"],
                    evidence=f["evidence"],
                    remediation=f["remediation"],
                    remediation_diff=f.get("remediation_diff"),
                    status="OPEN",
                )
                db.add(finding_row)

            # Persist ASVS 5.0 verification ledger items
            assessment.verification_items.clear()
            for v in report["verification_ledger"]:
                v_row = VerificationItem(
                    assessment_id=assessment.id,
                    asvs_id=v["asvs_id"],
                    category=v["category"],
                    requirement=v["requirement"],
                    status=v["status"],
                    verification_method=v["verification_method"],
                    evidence_or_reason=v["evidence_or_reason"],
                )
                db.add(v_row)

            # Generate and persist HTML & JSON reports
            html_content = render_html(report)
            json_content = json.dumps(report, indent=2)

            html_path = settings.REPORTS_DIR / f"{assessment.id}.html"
            json_path = settings.REPORTS_DIR / f"{assessment.id}.json"

            html_path.write_text(html_content, encoding="utf-8")
            json_path.write_text(json_content, encoding="utf-8")

            # Update assessment metrics and status
            by_sev = report["summary"]["by_severity"]
            blockers = by_sev.get("critical", 0) + by_sev.get("high", 0)

            assessment.commit_sha = commit_sha or assessment.commit_sha or "HEAD"
            assessment.target_type = intake_type
            assessment.status = "completed"
            assessment.readiness_status = report["readiness_status"]
            assessment.blockers_count = blockers
            assessment.total_findings_count = report["summary"]["total"]
            assessment.verified_controls_count = report["summary"]["verified_controls"]
            assessment.unverified_gaps_count = report["summary"]["unverified_gaps"]
            assessment.html_report_path = str(html_path)
            assessment.json_report_path = str(json_path)
            assessment.completed_at = datetime.now(timezone.utc)

            if reviewer_name:
                assessment.reviewer_name = reviewer_name
                assessment.reviewer_notes = reviewer_notes
                assessment.reviewer_status = "approved" if blockers == 0 else "changes_requested"

            # Record audit event
            audit = AuditEvent(
                assessment_id=assessment.id,
                event_type="scan_completed",
                actor="system",
                payload_json=json.dumps({
                    "readiness": assessment.readiness_status,
                    "blockers": blockers,
                    "findings": assessment.total_findings_count,
                }),
            )
            db.add(audit)
            db.commit()

    except Exception as e:
        assessment.status = "failed"
        db.add(
            AuditEvent(
                assessment_id=assessment.id,
                event_type="scan_failed",
                actor="system",
                payload_json=json.dumps({"error": str(e)}),
            )
        )
        db.commit()
        raise e

    db.refresh(assessment)
    return assessment


def run_assessment_background(
    assessment_id: str,
    github_token: Optional[str] = None,
    ref: Optional[str] = None,
    reviewer_name: Optional[str] = None,
    reviewer_notes: Optional[str] = None,
) -> None:
    """Background worker task executed by FastAPI BackgroundTasks worker pool."""
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        execute_assessment(
            db=db,
            assessment_id=assessment_id,
            github_token=github_token,
            ref=ref,
            reviewer_name=reviewer_name,
            reviewer_notes=reviewer_notes,
        )
    except Exception as exc:
        # Error is logged and persisted into AuditEvent by execute_assessment
        pass
    finally:
        db.close()
