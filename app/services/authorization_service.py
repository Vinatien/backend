"""Authorization service with dependency injection for FastAPI."""

from typing import Any, Callable, Coroutine, Optional
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

# Import database session dependency
from app.adapters.db.database import get_session

# Import repositories
from app.repositories import account_repository, revoked_tokens_repository

# Import DTOs and exceptions
from app.types.account_dtos import AccountRead
from app.types.exceptions import AuthenticationException, AuthorizationException

# Import token utilities
from app.utils.token_utils import decode_account_access_token
from app.utils.settings import INTERNAL_API_KEY

security = HTTPBearer()


def _is_internal_bypass_token(token: str) -> bool:
    """Check if token is an internal API key for service-to-service communication."""
    return INTERNAL_API_KEY is not None and token == INTERNAL_API_KEY


async def _authorize_authenticated_account_or_internal_request(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> Optional[AccountRead]:
    """
    Core authorization function that validates JWT tokens and retrieves account data.
    Returns None for internal bypass tokens, AccountRead for valid user tokens.
    """
    token = credentials.credentials

    # Allow internal service bypass
    if _is_internal_bypass_token(token):
        return None

    # Check if token is revoked
    if await revoked_tokens_repository.is_token_revoked(session, token):
        raise AuthorizationException("Token has been revoked.")

    # Decode and validate JWT token
    try:
        payload = decode_account_access_token(token)
    except AuthenticationException:
        raise AuthorizationException("Invalid token.")

    # Extract account ID from token payload
    account_id = payload.get("account_id")
    if not account_id:
        raise AuthorizationException("Missing account ID.")

    # Retrieve account from database
    account_model = await account_repository.get_account_by_id(session, account_id)
    if not account_model:
        raise AuthorizationException("Account not found.")

    # Convert to AccountRead DTO with proper field mapping
    return AccountRead(
        account_id=account_model.id,
        email=account_model.email,
        username=account_model.username,
        full_name=account_model.full_name,
        account_verified=account_model.is_active,
        created_at=account_model.created_at,
        last_login=None  # This would need to be tracked separately if needed
    )


def authorize_authenticated_account(
    allow_internal_bypass: bool = False,
) -> Callable[[Optional[AccountRead]], Coroutine[Any, Any, Optional[AccountRead]]]:
    """
    Public dependency for route protection.

    Args:
        allow_internal_bypass: Whether to allow internal API key access

    Returns:
        Dependency function that returns AccountRead or None (for internal)
    """
    async def dependency(
        account: Optional[AccountRead] = Depends(
            _authorize_authenticated_account_or_internal_request
        ),
    ) -> Optional[AccountRead]:
        if account is None:
            if allow_internal_bypass:
                return None
            raise AuthorizationException("Internal access not allowed for this route.")
        return account

    return dependency


def authorize_internal_request(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:
    """
    Dependency for internal-only routes that require API key authentication.
    """
    token = credentials.credentials

    if not _is_internal_bypass_token(token):
        raise AuthorizationException("Not authorized.")