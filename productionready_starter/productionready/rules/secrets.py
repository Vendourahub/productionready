"""Secret and cryptographic material detection rules."""
from __future__ import annotations
import re
from pathlib import Path
from typing import List
from ..models import Finding, Severity

# Patterns for API keys and secrets
KEY_PATTERNS = [
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "PR-KEY-001", "V8.1", Severity.CRITICAL, "Private key material marker found",
     "PEM private key header present (value withheld).",
     "Remove private keys from source code immediately, rotate the compromised key, and inspect version history.",
     "--- a/{filename}\n+++ b/{filename}\n-<private_key_pem_withheld>\n+PRIVATE_KEY=os.environ[\"PRIVATE_KEY\"]"),
     
    (r"(?i)^\s*(?:SECRET_KEY|JWT_SECRET|SESSION_SECRET)\s*=\s*['\"]?(?:changeme|password|secret|123456|dev-secret|default-secret)['\"]?\s*$",
     "PR-SECRET-001", "V2.1", Severity.HIGH, "Predictable or default application secret",
     "Known weak default secret value detected (value withheld).",
     "Generate a cryptographically secure random secret (e.g. openssl rand -hex 32) and inject via environment variables.",
     "--- a/{filename}\n+++ b/{filename}\n-SECRET_KEY = \"changeme\"\n+SECRET_KEY = os.environ.get(\"APP_SECRET_KEY\")"),

    (r"sk-(?:proj-)?[a-zA-Z0-9_\-]{24,}", "PR-APIKEY-001", "V2.1", Severity.CRITICAL, "Exposed OpenAI API key in source",
     "Active OpenAI / AI platform API key pattern detected (key withheld).",
     "Rotate this API key in the OpenAI developer console and move it to a server-side secret manager.",
     "--- a/{filename}\n+++ b/{filename}\n-const apiKey = \"sk-proj-...\";\n+const apiKey = process.env.OPENAI_API_KEY;"),

    (r"sk-ant-[a-zA-Z0-9_\-]{20,}", "PR-APIKEY-001", "V2.1", Severity.CRITICAL, "Exposed Anthropic API key in source",
     "Anthropic platform secret key detected (key withheld).",
     "Rotate this Anthropic API key immediately and inject via environment variables.",
     None),

    (r"(?:sk|rk)_live_[0-9a-zA-Z]{24,}", "PR-APIKEY-001", "V2.1", Severity.CRITICAL, "Exposed live Stripe secret key in source",
     "Live Stripe secret key found in source code (key withheld).",
     "Immediately revoke and roll this Stripe restricted/secret key in the Stripe Dashboard to prevent unauthorized charges.",
     "--- a/{filename}\n+++ b/{filename}\n-const stripe = new Stripe(\"sk_live_...\");\n+const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);"),

    (r"re_[a-zA-Z0-9]{24,}", "PR-APIKEY-001", "V2.1", Severity.HIGH, "Exposed Resend API key in source",
     "Resend email API key pattern detected (key withheld).",
     "Revoke this key in Resend dashboard and store it in server environment variables.",
     None),

    (r"AKIA[0-9A-Z]{16}", "PR-APIKEY-001", "V2.1", Severity.CRITICAL, "Exposed AWS Access Key ID in source",
     "AWS Access Key ID pattern detected (key withheld).",
     "Deactivate this IAM access key in the AWS Console, audit CloudTrail logs, and use IAM roles.",
     None),

    (r"(?:ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{22,})", "PR-APIKEY-001", "V2.1", Severity.CRITICAL, "Exposed GitHub Personal Access Token",
     "GitHub PAT pattern detected in source file (token withheld).",
     "Revoke this token immediately on GitHub Settings -> Developer settings -> Personal access tokens.",
     None),
]

# Client-side bundle secret leakage patterns (common in AI-generated frontend frameworks)
CLIENT_SECRET_LEAK_PATTERN = re.compile(
    r"(?i)(?:NEXT_PUBLIC_|VITE_|REACT_APP_)(?:[A-Z0-9_]*)(?:SERVICE_ROLE|SECRET|PRIVATE_KEY|DATABASE_URL)"
)


def inspect_secrets_in_file(rel_path: str, content: str) -> List[Finding]:
    """Inspects text content for hardcoded keys, weak secrets, and client-side leakage."""
    findings: List[Finding] = []
    lines = content.splitlines()

    for idx, line in enumerate(lines, 1):
        # 1. Check known key and secret patterns
        for pattern, rule_id, asvs_id, severity, title, evidence, remediation, diff_tmpl in KEY_PATTERNS:
            if re.search(pattern, line):
                diff = diff_tmpl.format(filename=rel_path) if diff_tmpl else None
                findings.append(
                    Finding(
                        rule_id=rule_id,
                        asvs_id=asvs_id,
                        severity=severity.value,
                        title=title,
                        location=rel_path,
                        line=idx,
                        evidence=evidence,
                        remediation=remediation,
                        remediation_diff=diff,
                        confidence="high",
                    )
                )

        # 2. Check client-side env leakage (NEXT_PUBLIC_*_SERVICE_ROLE, etc.)
        match = CLIENT_SECRET_LEAK_PATTERN.search(line)
        if match:
            findings.append(
                Finding(
                    rule_id="PR-CLIENT-001",
                    asvs_id="V4.2",
                    severity=Severity.CRITICAL.value,
                    title="High-privilege secret exposed via client-side prefix",
                    location=rel_path,
                    line=idx,
                    evidence=f"Variable name '{match.group(0)}' prefixes a privileged secret for client-side bundle exposure.",
                    remediation="Never prefix backend secrets with NEXT_PUBLIC_ or VITE_. Restrict database service roles to secure server-side routes.",
                    remediation_diff=f"--- a/{rel_path}\n+++ b/{rel_path}\n-{match.group(0)}=\"...\";\n+SUPABASE_SERVICE_ROLE_KEY=\"...\"; // Server-only",
                    confidence="high",
                )
            )

    return findings
