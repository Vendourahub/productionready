"""Configuration, environment, and network header inspection rules."""
from __future__ import annotations
import re
from pathlib import Path
from typing import List
from ..models import Finding, Severity

DEBUG_PATTERNS = [
    re.compile(r"(?i)^\s*(?:DEBUG|FLASK_DEBUG)\s*=\s*(?:true|1)\s*(?:#.*)?$"),
    re.compile(r"(?i)^\s*(?:NODE_ENV)\s*=\s*['\"]?development['\"]?\s*(?:#.*)?$"),
    re.compile(r"(?i)^\s*app\.run\(.*debug\s*=\s*True.*\)"),
]

CORS_WILDCARD_CREDENTIALS = [
    re.compile(r"(?i)allow_origins\s*=\s*\[[\"']\*[\"']\].*allow_credentials\s*=\s*True"),
    re.compile(r"(?i)cors\(\{.*origin:\s*['\"]\*['\"].*credentials:\s*true"),
]


def inspect_configuration_file(rel_path: str, content: str) -> List[Finding]:
    """Inspects file for debug flags and dangerous CORS configurations."""
    findings: List[Finding] = []
    lines = content.splitlines()

    for idx, line in enumerate(lines, 1):
        # 1. Debug flag check
        for pat in DEBUG_PATTERNS:
            if pat.search(line):
                findings.append(
                    Finding(
                        rule_id="PR-DEBUG-001",
                        asvs_id="V14.1",
                        severity=Severity.MEDIUM.value,
                        title="Debug mode enabled in configuration",
                        location=rel_path,
                        line=idx,
                        evidence="A debug or development flag is set to a truthy value.",
                        remediation="Disable debug mode for production deployments to prevent sensitive error disclosure.",
                        remediation_diff=f"--- a/{rel_path}\n+++ b/{rel_path}\n-DEBUG = True\n+DEBUG = False",
                        confidence="medium",
                    )
                )

        # 2. CORS wildcard with credentials
        for pat in CORS_WILDCARD_CREDENTIALS:
            if pat.search(line):
                findings.append(
                    Finding(
                        rule_id="PR-CORS-001",
                        asvs_id="V13.1",
                        severity=Severity.HIGH.value,
                        title="Insecure CORS policy: Wildcard origin with credentials enabled",
                        location=rel_path,
                        line=idx,
                        evidence="CORS configuration allows wildcard origin '*' while permitting authenticated credentials.",
                        remediation="Explicitly specify authorized frontend origins instead of '*' when allowing credentials.",
                        confidence="high",
                    )
                )

    return findings


def inspect_env_file_presence(p: Path, rel_path: str) -> List[Finding]:
    """Flags active .env files present in repository."""
    findings: List[Finding] = []
    if p.name == ".env" or (
        p.name.startswith(".env.")
        and p.name not in {".env.example", ".env.sample", ".env.template"}
    ):
        findings.append(
            Finding(
                rule_id="PR-ENV-001",
                asvs_id="V8.2",
                severity=Severity.HIGH.value,
                title="Active environment configuration file present in repository",
                location=rel_path,
                line=None,
                evidence="A non-template .env file is present in repository; credentials risk exposure.",
                remediation=(
                    "Confirm the file is included in .gitignore. Never commit live production credentials to Git. "
                    "If previously committed, immediately rotate all included secret values."
                ),
                confidence="high",
            )
        )
    return findings
