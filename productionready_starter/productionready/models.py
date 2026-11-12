"""Core domain models for ProductionReady assessments and verification."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VerificationStatus(str, Enum):
    VERIFIED_PASS = "verified_pass"
    FINDING_FAIL = "finding_fail"
    UNVERIFIED_GAP = "unverified_gap"


@dataclass
class Finding:
    rule_id: str
    asvs_id: str
    severity: str
    title: str
    location: str
    line: Optional[int]
    evidence: str
    remediation: str
    remediation_diff: Optional[str] = None
    confidence: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationItem:
    asvs_id: str
    category: str
    requirement: str
    status: str  # verified_pass | finding_fail | unverified_gap
    evidence_or_reason: str
    verification_method: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewerSignOff:
    reviewer_name: Optional[str] = None
    reviewer_email: Optional[str] = None
    review_date_utc: Optional[str] = None
    status: str = "pending"  # pending | approved | changes_requested
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AssessmentReport:
    product: str = "ProductionReady"
    version: str = "0.2.0"
    target: str = ""
    target_type: str = "local_directory"
    commit_sha: Optional[str] = None
    scan_time_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "partial_static_review_only"
    readiness_status: str = "NOT PRODUCTION READY"
    findings: List[Finding] = field(default_factory=list)
    verification_ledger: List[VerificationItem] = field(default_factory=list)
    coverage: Dict[str, Any] = field(default_factory=dict)
    coverage_summary: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    reviewer_sign_off: ReviewerSignOff = field(default_factory=ReviewerSignOff)
    disclaimer: str = (
        "This is NOT a certification, penetration test, safe-to-deploy verdict, or complete audit. "
        "Verified controls reflect checks actively performed and passed. "
        "Items marked 'unverified_gap' represent security controls requiring separate "
        "infrastructure, runtime, or penetration testing."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product": self.product,
            "version": self.version,
            "target": self.target,
            "target_type": self.target_type,
            "commit_sha": self.commit_sha,
            "scan_time_utc": self.scan_time_utc,
            "status": self.status,
            "readiness_status": self.readiness_status,
            "findings": [f.to_dict() for f in self.findings],
            "verification_ledger": [v.to_dict() for v in self.verification_ledger],
            "coverage": self.coverage,
            "coverage_summary": self.coverage_summary,
            "summary": self.summary,
            "reviewer_sign_off": self.reviewer_sign_off.to_dict(),
            "disclaimer": self.disclaimer,
        }
