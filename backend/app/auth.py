"""API Key and Token Authentication dependencies for ProductionReady orchestrator."""
import hmac
from typing import Optional
from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_auth = HTTPBearer(auto_error=False)


def verify_api_key(
    x_api_key: Optional[str] = Security(api_key_header),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth),
) -> str:
    """Validates X-API-Key header or Authorization: Bearer token against configured key.

    Returns the authenticated key identifier or raises 401 Unauthorized.
    """
    if not settings.REQUIRE_AUTH:
        return "auth_disabled"

    expected_key = settings.effective_api_key
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server API key authentication is required but no key is configured.",
        )

    provided_key = x_api_key
    if not provided_key and bearer_creds:
        provided_key = bearer_creds.credentials

    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials. Provide 'X-API-Key' or 'Authorization: Bearer <key>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(provided_key.strip(), expected_key.strip()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return "authenticated_user"
