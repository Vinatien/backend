"""JWT token utilities for account authentication."""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from app.utils.settings import (
    ACCESS_TOKEN_SECRET,
    REFRESH_TOKEN_SECRET,
    ACCESS_TOKEN_EXPIRES_IN,
    REFRESH_TOKEN_EXPIRES_IN
)
from app.types.exceptions import AuthenticationException


def create_access_token(account_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create an access token for an account.

    Args:
        account_id: The account ID
        email: The account email
        expires_delta: Optional custom expiration time

    Returns:
        JWT access token as string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            seconds=ACCESS_TOKEN_EXPIRES_IN
        )

    payload = {
        "sub": str(account_id),
        "account_id": account_id,
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }

    return jwt.encode(
        payload,
        ACCESS_TOKEN_SECRET,
        algorithm="HS256"
    )


def create_refresh_token(account_id: int, email: str) -> str:
    """
    Create a refresh token for an account.

    Args:
        account_id: The account ID
        email: The account email

    Returns:
        JWT refresh token as string
    """
    expire = datetime.now(timezone.utc) + timedelta(
        seconds=REFRESH_TOKEN_EXPIRES_IN
    )

    payload = {
        "sub": str(account_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }

    return jwt.encode(
        payload,
        REFRESH_TOKEN_SECRET,
        algorithm="HS256"
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate an access token.

    Args:
        token: The JWT token to decode

    Returns:
        Token payload as dictionary

    Raises:
        jwt.PyJWTError: If token is invalid or expired
    """
    payload = jwt.decode(
        token,
        ACCESS_TOKEN_SECRET,
        algorithms=["HS256"]
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")

    return payload


def decode_refresh_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a refresh token.

    Args:
        token: The JWT token to decode

    Returns:
        Token payload as dictionary

    Raises:
        jwt.PyJWTError: If token is invalid or expired
    """
    payload = jwt.decode(
        token,
        REFRESH_TOKEN_SECRET,
        algorithms=["HS256"]
    )

    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("Invalid token type")

    return payload


def decode_account_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate an account access token.
    This function is specifically designed for the authorization service.

    Args:
        token: The JWT token to decode

    Returns:
        Token payload as dictionary

    Raises:
        AuthenticationException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            ACCESS_TOKEN_SECRET,
            algorithms=["HS256"]
        )

        if payload.get("type") != "access":
            raise AuthenticationException("Invalid token type")

        return payload

    except jwt.PyJWTError as e:
        raise AuthenticationException(f"Invalid token: {str(e)}")