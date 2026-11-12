"""Projects API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import verify_api_key
from ..models import Project, Assessment
from ..schemas.project import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["Projects"], dependencies=[Depends(verify_api_key)])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """Registers a new repository for deployment readiness assessment."""
    project = Project(
        name=data.name,
        repository_url=data.repository_url,
        default_branch=data.default_branch,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    """Lists all registered projects and their latest assessment status."""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    results = []
    for p in projects:
        latest = db.query(Assessment).filter(Assessment.project_id == p.id).order_by(Assessment.created_at.desc()).first()
        res = ProjectResponse(
            id=p.id,
            name=p.name,
            repository_url=p.repository_url,
            default_branch=p.default_branch,
            created_at=p.created_at,
            updated_at=p.updated_at,
            latest_assessment_status=latest.status if latest else None,
            latest_readiness_status=latest.readiness_status if latest else None,
        )
        results.append(res)
    return results


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Retrieves a single project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    latest = db.query(Assessment).filter(Assessment.project_id == project.id).order_by(Assessment.created_at.desc()).first()
    return ProjectResponse(
        id=project.id,
        name=project.name,
        repository_url=project.repository_url,
        default_branch=project.default_branch,
        created_at=project.created_at,
        updated_at=project.updated_at,
        latest_assessment_status=latest.status if latest else None,
        latest_readiness_status=latest.readiness_status if latest else None,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Deletes a project and all associated assessments."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    db.delete(project)
    db.commit()
    return None
