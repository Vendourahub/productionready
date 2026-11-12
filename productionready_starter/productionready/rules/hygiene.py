"""Repository hygiene, manifest, and test suite inspection rules."""
from __future__ import annotations
from pathlib import Path
from typing import List, Set
from ..models import Finding, Severity

MANIFEST_NAMES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "go.mod",
    "Cargo.toml",
    "composer.json",
    "pom.xml",
    "build.gradle",
}


def inspect_repository_hygiene(root: Path, seen_filenames: Set[str]) -> List[Finding]:
    """Evaluates top-level repository hygiene: manifests, test suites, and gitignore."""
    findings: List[Finding] = []

    # 1. Dependency manifest presence
    if not (seen_filenames & MANIFEST_NAMES):
        findings.append(
            Finding(
                rule_id="PR-MANIFEST-001",
                asvs_id="V1.1",
                severity=Severity.INFO.value,
                title="No recognized dependency manifest detected",
                location=".",
                line=None,
                evidence="No standard package manifest (e.g. package.json, requirements.txt) detected in repository root.",
                remediation="Ensure dependency manifests are committed to pin dependency versions and maintain reproducible builds.",
                confidence="low",
            )
        )

    # 2. Automated test suite presence
    test_dirs = ["tests", "test", "__tests__", "spec"]
    has_tests = any((root / d).is_dir() for d in test_dirs)
    if not has_tests:
        findings.append(
            Finding(
                rule_id="PR-TEST-001",
                asvs_id="V1.2",
                severity=Severity.INFO.value,
                title="No conventional test directory found",
                location=".",
                line=None,
                evidence="No standard test directory (tests/, test/, __tests__/, spec/) detected in repository root.",
                remediation="Establish an automated testing suite to verify critical business logic and prevent regressions.",
                confidence="low",
            )
        )

    # 3. .gitignore presence
    if not (root / ".gitignore").exists():
        findings.append(
            Finding(
                rule_id="PR-GIT-001",
                asvs_id="V14.1",
                severity=Severity.LOW.value,
                title="Missing .gitignore file",
                location=".",
                line=None,
                evidence="Repository root lacks a .gitignore file, risking inadvertent commits of secrets, .env files, and build artifacts.",
                remediation="Add a tailored .gitignore file for your framework to keep credentials and build caches out of Git history.",
                confidence="high",
            )
        )

    return findings
