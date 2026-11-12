"""GitHub App webhook verification and intake processing."""
from __future__ import annotations
import hmac
import hashlib
from typing import Optional
from ..config import settings


def verify_github_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
    """Verifies HMAC SHA256 signature sent by GitHub App webhooks."""
    if not settings.GITHUB_WEBHOOK_SECRET:
        # If no secret configured in dev mode, accept payload
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_sig = signature_header.split("sha256=")[1]
    computed_sig = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_sig, computed_sig)
