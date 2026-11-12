"""Payment and webhook security verification rules."""
from __future__ import annotations
import re
from pathlib import Path
from typing import List
from ..models import Finding, Severity

WEBHOOK_ENDPOINT_PATTERNS = [
    re.compile(r"(?i)(?:webhook|stripe|lemonsqueezy)"),
]

STRIPE_CONSTRUCT_EVENT = re.compile(
    r"(?i)(?:stripe\.webhooks\.constructEvent|construct_event|verify_signature)"
)


def inspect_webhook_security(rel_path: str, content: str) -> List[Finding]:
    """Inspects webhook endpoints to verify signature validation is implemented."""
    findings: List[Finding] = []
    
    # Target webhook route files (e.g. app/api/webhook/route.ts, routes/stripe.py)
    is_webhook_file = any(pat.search(rel_path) for pat in WEBHOOK_ENDPOINT_PATTERNS)
    if not is_webhook_file:
        return findings

    # Look for stripe checkout or payment handling
    has_stripe_handling = "stripe" in content.lower() or "checkout" in content.lower()
    if has_stripe_handling:
        has_signature_verification = bool(STRIPE_CONSTRUCT_EVENT.search(content))
        if not has_signature_verification:
            findings.append(
                Finding(
                    rule_id="PR-PAY-001",
                    asvs_id="V5.1",
                    severity=Severity.CRITICAL.value,
                    title="Unverified payment webhook endpoint",
                    location=rel_path,
                    line=1,
                    evidence="Stripe webhook endpoint does not invoke 'stripe.webhooks.constructEvent' or signature validation.",
                    remediation=(
                        "Always verify the webhook signature (stripe-signature header) against the endpoint secret. "
                        "Unverified webhooks allow attackers to spoof 'checkout.session.completed' events."
                    ),
                    remediation_diff=(
                        f"--- a/{rel_path}\n+++ b/{rel_path}\n"
                        "+const event = stripe.webhooks.constructEvent(\n"
                        "+  rawBody,\n"
                        "+  req.headers['stripe-signature'],\n"
                        "+  process.env.STRIPE_WEBHOOK_SECRET!\n"
                        "+);"
                    ),
                    confidence="high",
                )
            )

    return findings
