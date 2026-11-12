"""Project model representing connected codebases."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from ..database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    repository_url = Column(String(512), nullable=False)
    default_branch = Column(String(100), default="main")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    assessments = relationship("Assessment", back_populates="project", cascade="all, delete-orphan", order_by="desc(Assessment.created_at)")
