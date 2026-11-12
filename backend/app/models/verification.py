"""Verification item model representing ASVS 5.0 controls ledger."""
import uuid
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class VerificationItem(Base):
    __tablename__ = "verification_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    asvs_id = Column(String(20), nullable=False)
    category = Column(String(100), nullable=False)
    requirement = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)  # verified_pass | finding_fail | unverified_gap
    verification_method = Column(String(100), nullable=False)
    evidence_or_reason = Column(Text, nullable=False)

    assessment = relationship("Assessment", back_populates="verification_items")
