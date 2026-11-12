"""GitHub Webhook integration router."""
import json
from fastapi import APIRouter, Header, Request, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Project, Assessment
from ..services.github import verify_github_signature
from ..services.runner import run_assessment_background

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/github", status_code=status.HTTP_200_OK)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_db),
):
    """Handles incoming GitHub App push and installation webhooks."""
    body = await request.body()
    if not verify_github_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")

    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    # Process repository push event
    if x_github_event == "push":
        repo_data = payload.get("repository", {})
        repo_url = repo_data.get("html_url")
        commit_sha = payload.get("after")
        ref = payload.get("ref", "").replace("refs/heads/", "") or "main"

        if repo_url:
            # Find matching registered project
            project = (
                db.query(Project)
                .filter(Project.repository_url.ilike(f"%{repo_data.get('full_name')}%"))
                .first()
            )
            if project:
                assessment = Assessment(
                    project_id=project.id,
                    commit_sha=commit_sha,
                    status="queued",
                )
                db.add(assessment)
                db.commit()
                db.refresh(assessment)

                # Queue background task execution
                background_tasks.add_task(
                    run_assessment_background,
                    assessment_id=assessment.id,
                    ref=ref,
                )
                return {"status": "assessment_queued", "assessment_id": assessment.id}

    return {"status": "ignored", "event": x_github_event}
