"""Audit event model for tracking verification lifecycle, changes, and sign-offs."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)  # scan_triggered | finding_status_updated | reassessment_requested | reviewer_signed_off
    actor = Column(String(255), default="system")
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    assessment = relationship("Assessment", back_populates="audit_events")
