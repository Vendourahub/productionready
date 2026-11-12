"""Finding model representing identified security defects."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(String(50), nullable=False)
    asvs_id = Column(String(20), nullable=False)
    severity = Column(String(20), nullable=False)  # critical | high | medium | low | info
    title = Column(String(255), nullable=False)
    location = Column(String(512), nullable=False)
    line = Column(Integer, nullable=True)
    evidence = Column(Text, nullable=False)
    remediation = Column(Text, nullable=False)
    remediation_diff = Column(Text, nullable=True)
    
    # Remediation workflow status
    status = Column(String(50), default="OPEN")  # OPEN | RESOLVED | ACCEPTED_RISK
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    assessment = relationship("Assessment", back_populates="findings")
