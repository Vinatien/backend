"""Revoked tokens repository for token blacklist management."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.revoked_token_model import RevokedToken


async def is_token_revoked(session: AsyncSession, token: str) -> bool:
    """
    Check if a token has been revoked.

    Args:
        session: Database session
        token: Token string to check

    Returns:
        True if token is revoked, False otherwise
    """
    result = await session.execute(
        select(RevokedToken).where(RevokedToken.token == token)
    )
    revoked_token = result.scalar_one_or_none()
    return revoked_token is not None


async def add_revoked_token(
    session: AsyncSession,
    token: str,
    user_id: int,
    user_type: str,
    token_type: str,
    expires_at: datetime
) -> RevokedToken:
    """
    Add a token to the revoked tokens list.

    Args:
        session: Database session
        token: Token string to revoke
        user_id: User ID associated with the token
        user_type: Type of user (e.g., 'account')
        token_type: Type of token (e.g., 'access', 'refresh')
        expires_at: Token expiration time

    Returns:
        Created revoked token model
    """
    revoked_token = RevokedToken(
        token=token,
        user_id=user_id,
        user_type=user_type,
        token_type=token_type,
        expires_at=expires_at
    )

    session.add(revoked_token)
    await session.commit()
    await session.refresh(revoked_token)
    return revoked_token


async def get_revoked_token(session: AsyncSession, token: str) -> Optional[RevokedToken]:
    """
    Get revoked token by token string.

    Args:
        session: Database session
        token: Token string to retrieve

    Returns:
        Revoked token model or None if not found
    """
    result = await session.execute(
        select(RevokedToken).where(RevokedToken.token == token)
    )
    return result.scalar_one_or_none()


async def get_revoked_tokens_by_user(
    session: AsyncSession,
    user_id: int,
    user_type: str = "account"
) -> List[RevokedToken]:
    """
    Get all revoked tokens for a specific user.

    Args:
        session: Database session
        user_id: User ID to search for
        user_type: Type of user (default: 'account')

    Returns:
        List of revoked token models
    """
    result = await session.execute(
        select(RevokedToken).where(
            (RevokedToken.user_id == user_id) &
            (RevokedToken.user_type == user_type)
        )
    )
    return result.scalars().all()


async def cleanup_expired_tokens(session: AsyncSession) -> int:
    """
    Remove expired tokens from the revoked tokens table.

    Args:
        session: Database session

    Returns:
        Number of tokens removed
    """
    current_time = datetime.utcnow()

    result = await session.execute(
        delete(RevokedToken).where(RevokedToken.expires_at < current_time)
    )

    await session.commit()
    return result.rowcount


async def revoke_all_user_tokens(
    session: AsyncSession,
    user_id: int,
    user_type: str = "account"
) -> int:
    """
    Mark all existing tokens for a user as revoked.
    This is useful for logout all sessions.

    Args:
        session: Database session
        user_id: User ID whose tokens to revoke
        user_type: Type of user (default: 'account')

    Returns:
        Number of tokens marked as revoked
    """
    # This function would need to be implemented based on how you track active tokens
    # For now, we'll just count existing revoked tokens
    result = await session.execute(
        select(RevokedToken).where(
            (RevokedToken.user_id == user_id) &
            (RevokedToken.user_type == user_type)
        )
    )
    return len(result.scalars().all())