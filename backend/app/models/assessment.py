"""Assessment model representing a security verification execution."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    commit_sha = Column(String(64), nullable=True)
    target_type = Column(String(50), default="github_repository")
    status = Column(String(50), default="queued")  # queued | running | completed | failed
    readiness_status = Column(String(50), default="NOT PRODUCTION READY")  # NOT PRODUCTION READY | NEEDS REMEDIATION | VERIFIED WITH GAPS
    
    blockers_count = Column(Integer, default=0)
    total_findings_count = Column(Integer, default=0)
    verified_controls_count = Column(Integer, default=0)
    unverified_gaps_count = Column(Integer, default=0)
    
    html_report_path = Column(String(512), nullable=True)
    json_report_path = Column(String(512), nullable=True)
    
    # Reviewer sign-off ($299 package)
    reviewer_name = Column(String(255), nullable=True)
    reviewer_status = Column(String(50), default="pending")  # pending | approved | changes_requested
    reviewer_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="assessments")
    findings = relationship("Finding", back_populates="assessment", cascade="all, delete-orphan", order_by="Finding.severity")
    verification_items = relationship("VerificationItem", back_populates="assessment", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="assessment", cascade="all, delete-orphan")
