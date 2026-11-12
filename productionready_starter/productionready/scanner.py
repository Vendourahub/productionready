"""ProductionReady core static inspection and verification engine.

Performs offline code and configuration analysis, separating verified controls
from defects and unverified operational gaps according to OWASP ASVS 5.0.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Set, List
import json

from .models import (
    Finding,
    VerificationItem,
    ReviewerSignOff,
    AssessmentReport,
    Severity,
    VerificationStatus,
)
from .ledger import build_verification_ledger
from .rules.secrets import inspect_secrets_in_file
from .rules.database import inspect_sql_rls
from .rules.configuration import inspect_configuration_file, inspect_env_file_presence
from .rules.payments import inspect_webhook_security
from .rules.hygiene import inspect_repository_hygiene
from .reporter import render_html as reporter_render_html

IGNORE = {
    ".git",
    "node_modules",
    ".next",
    "dist",
    "build",
    ".venv",
    "venv",
    "coverage",
    "vendor",
    "__pycache__",
    ".turbo",
    ".output",
    ".vercel",
}

EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
    ".md",
    ".sh",
    ".sql",
}

MAX_FILE_BYTES = 512_000
MAX_FILES = 15_000


def _iter_files(root: Path):
    """Safely traverses repository files, ignoring build caches and oversized artifacts."""
    count = 0
    for path in root.rglob("*"):
        if any(x in IGNORE for x in path.relative_to(root).parts):
            continue
        if not path.is_file() or path.is_symlink():
            continue
        count += 1
        if count > MAX_FILES:
            break
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        yield path


def scan(
    root: str | Path,
    target_type: str = "local_directory",
    commit_sha: Optional[str] = None,
    reviewer_name: Optional[str] = None,
    reviewer_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Inspects a repository directory and returns a structured AssessmentReport dictionary."""
    root_path = Path(root).expanduser().resolve(strict=True)
    if not root_path.is_dir():
        raise ValueError(f"Target '{root}' must be a directory.")

    findings: List[Finding] = []
    seen_names: Set[str] = set()
    files_inspected = 0

    for p in _iter_files(root_path):
        rel = p.relative_to(root_path)
        rel_str = str(rel).replace("\\", "/")
        seen_names.add(p.name)

        # Check for uncommitted / active .env files
        findings.extend(inspect_env_file_presence(p, rel_str))

        if p.suffix not in EXTENSIONS and not p.name.startswith(".env"):
            continue

        files_inspected += 1

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # 1. Secrets and cryptographic keys
        findings.extend(inspect_secrets_in_file(rel_str, content))

        # 2. Database & Row Level Security (SQL files)
        findings.extend(inspect_sql_rls(rel_str, content))

        # 3. Configuration & Debug flags
        findings.extend(inspect_configuration_file(rel_str, content))

        # 4. Payment webhook signatures
        findings.extend(inspect_webhook_security(rel_str, content))

    # 5. Top-level repository hygiene
    findings.extend(inspect_repository_hygiene(root_path, seen_names))

    # Severity ordering
    sev_order = {
        Severity.CRITICAL.value: 0,
        Severity.HIGH.value: 1,
        Severity.MEDIUM.value: 2,
        Severity.LOW.value: 3,
        Severity.INFO.value: 4,
    }
    findings.sort(key=lambda x: (sev_order.get(x.severity, 9), x.location, x.line or 0))

    # Readiness status calculation
    crit_count = sum(1 for f in findings if f.severity == Severity.CRITICAL.value)
    high_count = sum(1 for f in findings if f.severity == Severity.HIGH.value)
    med_count = sum(1 for f in findings if f.severity == Severity.MEDIUM.value)
    low_count = sum(1 for f in findings if f.severity == Severity.LOW.value)

    if crit_count > 0 or high_count > 0:
        readiness_status = "NOT PRODUCTION READY"
    elif med_count > 0 or low_count > 0:
        readiness_status = "NEEDS REMEDIATION"
    else:
        readiness_status = "VERIFIED WITH GAPS"

    # Build the ASVS 5.0 Verification & Gap Ledger
    ledger = build_verification_ledger(findings, files_inspected)

    summary = {
        "total": len(findings),
        "by_severity": {
            "critical": crit_count,
            "high": high_count,
            "medium": med_count,
            "low": low_count,
            "info": sum(1 for f in findings if f.severity == Severity.INFO.value),
        },
        "verified_controls": sum(1 for v in ledger if v.status == VerificationStatus.VERIFIED_PASS.value),
        "unverified_gaps": sum(1 for v in ledger if v.status == VerificationStatus.UNVERIFIED_GAP.value),
    }

    coverage_summary = {
        "files_inspected": files_inspected,
        "file_size_limit_bytes": MAX_FILE_BYTES,
        "max_file_candidates": MAX_FILES,
        "checks_performed": [
            "private-key-header-pattern",
            "weak-default-secret-pattern",
            "saas-api-key-exposure-patterns",
            "client-side-secret-leakage-pattern",
            "database-table-rls-declaration",
            "risky-debug-settings",
            "cors-wildcard-with-credentials",
            "payment-webhook-signature-verification",
            "tracked-environment-file-presence",
            "dependency-manifest-presence",
            "test-directory-presence",
            "gitignore-presence",
        ],
        "not_performed": [
            "live penetration testing",
            "cloud database backup and restore validation",
            "runtime session cookie inspection",
            "server-side dynamic brute-force mitigation testing",
            "cloud infrastructure access control verification",
        ],
    }

    reviewer = ReviewerSignOff(
        reviewer_name=reviewer_name,
        reviewer_email=None,
        review_date_utc=datetime.now(timezone.utc).isoformat() if reviewer_name else None,
        status="approved" if reviewer_name and crit_count == 0 and high_count == 0 else ("changes_requested" if reviewer_name else "pending"),
        notes=reviewer_notes,
    )

    report = AssessmentReport(
        product="ProductionReady",
        version="0.2.0",
        target=str(root_path),
        target_type=target_type,
        commit_sha=commit_sha,
        scan_time_utc=datetime.now(timezone.utc).isoformat(),
        status="partial_static_review_only",
        readiness_status=readiness_status,
        findings=findings,
        verification_ledger=ledger,
        coverage=coverage_summary,
        coverage_summary=coverage_summary,
        summary=summary,
        reviewer_sign_off=reviewer,
    )

    return report.to_dict()


def render_html(report: Dict[str, Any]) -> str:
    """Pass-through to reporter.render_html for backwards compatibility."""
    return reporter_render_html(report)
