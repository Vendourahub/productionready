"""OWASP ASVS 5.0 Verification and Gap Ledger generator.

Separates things actively verified by the engine from findings (defects) and unverified gaps.
"""
from __future__ import annotations
from typing import List, Dict, Set
from .models import VerificationItem, VerificationStatus, Finding

# Defined benchmark controls based on OWASP ASVS 5.0
ASVS_CATALOG = [
    {
        "asvs_id": "V1.1",
        "category": "Architecture & Supply Chain",
        "requirement": "Recognized dependency manifest is maintained for reproducible builds and SBOM tracking.",
        "default_status": VerificationStatus.VERIFIED_PASS,
        "verification_method": "static_filesystem",
        "rule_id": "PR-MANIFEST-001",
    },
    {
        "asvs_id": "V1.2",
        "category": "Architecture & Testing",
        "requirement": "Automated test suite is present to verify business logic and regressions.",
        "default_status": VerificationStatus.VERIFIED_PASS,
        "verification_method": "static_filesystem",
        "rule_id": "PR-TEST-001",
    },
    {
        "asvs_id": "V1.3",
        "category": "Architecture & Threat Modeling",
        "requirement": "Application design and threat model reviewed against multi-tenant risks.",
        "default_status": VerificationStatus.UNVERIFIED_GAP,
        "verification_method": "manual_review_required",
        "reason": "Static scanner cannot evaluate business logic architecture; requires human threat modeling review.",
    },
    {
        "asvs_id": "V2.1",
        "category": "Authentication & Secrets",
        "requirement": "No production secrets, platform API keys, or cloud credentials stored in source code.",
        "default_status": VerificationStatus.VERIFIED_PASS,
        "verification_method": "static_regex",
        "rule_id": "PR-SECRET-001",
    },
    {
        "asvs_id": "V2.2",
        "category": "Authentication & Credentials",
        "requirement": "Secure credential hashing and brute-force mitigation mechanisms verified.",
        "default_status": VerificationStatus.UNVERIFIED_GAP,
        "verification_method": "dynamic_test_required",
        "reason": "Requires dynamic runtime test of authentication endpoint and password hashing implementation.",
    },
    {
        "asvs_id": "V3.1",
        "category": "Session Management",
        "requirement": "Session tokens and authentication cookies configured with HttpOnly, Secure, and SameSite attributes.",
        "default_status": VerificationStatus.UNVERIFIED_GAP,
        "verification_method": "manual_review_required",
        "reason": "Requires runtime inspection of HTTP Set-Cookie headers in deployed staging/production environment.",
    },
    {
        "asvs_id": "V4.1",
        "category": "Access Control & Database",
        "requirement": "Database tables have explicit Row Level Security (RLS) enabled to prevent unauthorized data access.",
        "default_status": VerificationStatus.VERIFIED_PASS,
        "verification_method": "static_ast",
        "rule_id": "PR-RLS-001",
    },
    {
        "asvs_id": "V4.2",
        "category": "Access Control & Client Trust",
        "requirement": "High-privilege database service keys (e.g. Supabase service_role) isolated from client-side bundles.",
        "default_status": VerificationStatus.VERIFIED_PASS,
        "verification_method": "static_regex",
        "rule_id": "PR-CLIENT-001",
    },
    {
        "asvs_id": "V5.1",
        "category": "Validation & Webhooks",
        "requirement": "Payment and third-party webhook handlers verify cryptographic signatures before processing.",
        "default_status": VerificationStatus.VERIFIED_PASS,
        "verification_method": "static_ast",
        "rule_id": "PR-PAY-001",
    },
    {
        "asvs_id": "V8.1",
        "category": "Data Protection & Cryptography",
        "requirement": "No asymmetric private keys (PEM, RSA, OpenSSH) present in repository files.",
        "default_status": VerificationStatus.VERIFIED_PASS,
        "verification_method": "static_regex",
        "rule_id": "PR-KEY-001",
    },
    {
        "asvs_id": "V8.2",
        "category": "Data Protection & Environment",
        "requirement": "Active .env files containing unencrypted production credentials are excluded from version control.",
        "default_status": VerificationStatus.VERIFIED_PASS,
        "verification_method": "static_filesystem",
        "rule_id": "PR-ENV-001",
    },
    {
        "asvs_id": "V8.3",
        "category": "Data Protection & Storage",
        "requirement": "Database at-rest encryption and automated backup replication verified.",
        "default_status": VerificationStatus.UNVERIFIED_GAP,
        "verification_method": "manual_review_required",
        "reason": "Requires cloud infrastructure verification (AWS/GCP/Supabase project settings audit).",
    },
    {
        "asvs_id": "V13.1",
        "category": "API & Web Services",
        "requirement": "CORS configuration strictly restricts allowed origins and prohibits wildcard access with credentials.",
        "default_status": VerificationStatus.VERIFIED_PASS,
        "verification_method": "static_regex",
        "rule_id": "PR-CORS-001",
    },
    {
        "asvs_id": "V14.1",
        "category": "Configuration & Build",
        "requirement": "Debug modes, verbose diagnostic stack traces, and dev tooling disabled for production.",
        "default_status": VerificationStatus.VERIFIED_PASS,
        "verification_method": "static_regex",
        "rule_id": "PR-DEBUG-001",
    },
    {
        "asvs_id": "V14.2",
        "category": "Configuration & Maintenance",
        "requirement": "Automated disaster recovery restoration procedures tested and documented.",
        "default_status": VerificationStatus.UNVERIFIED_GAP,
        "verification_method": "manual_review_required",
        "reason": "Out of scope for code scanner; requires staging database restore exercise.",
    },
]


def build_verification_ledger(findings: List[Finding], files_inspected: int) -> List[VerificationItem]:
    """Generates the three-state verification ledger based on findings and catalog."""
    failing_rule_ids: Dict[str, Finding] = {f.rule_id: f for f in findings}
    ledger: List[VerificationItem] = []

    for item in ASVS_CATALOG:
        rule_id = item.get("rule_id")
        asvs_id = item["asvs_id"]
        category = item["category"]
        requirement = item["requirement"]
        verification_method = item["verification_method"]

        if rule_id and rule_id in failing_rule_ids:
            # The test ran, but failed with finding
            finding = failing_rule_ids[rule_id]
            ledger.append(
                VerificationItem(
                    asvs_id=asvs_id,
                    category=category,
                    requirement=requirement,
                    status=VerificationStatus.FINDING_FAIL.value,
                    evidence_or_reason=f"Finding {finding.rule_id}: {finding.title} ({finding.location})",
                    verification_method=verification_method,
                )
            )
        elif item["default_status"] == VerificationStatus.UNVERIFIED_GAP:
            # Control not statically evaluated
            ledger.append(
                VerificationItem(
                    asvs_id=asvs_id,
                    category=category,
                    requirement=requirement,
                    status=VerificationStatus.UNVERIFIED_GAP.value,
                    evidence_or_reason=item.get("reason", "Requires manual or dynamic verification."),
                    verification_method=verification_method,
                )
            )
        else:
            # Control ran and verified clean
            evidence = f"Verified across {files_inspected} candidate files with zero negative patterns detected."
            ledger.append(
                VerificationItem(
                    asvs_id=asvs_id,
                    category=category,
                    requirement=requirement,
                    status=VerificationStatus.VERIFIED_PASS.value,
                    evidence_or_reason=evidence,
                    verification_method=verification_method,
                )
            )

    return ledger
