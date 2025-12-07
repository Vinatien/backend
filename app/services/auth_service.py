"""Authentication service for account management."""

import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import account_repository
from app.types.account_dtos import AccountCreate, AccountResponse
from app.types.auth_dtos import TokenPair
from app.utils.password import hash_password, verify_password
from app.utils.token_utils import create_access_token, create_refresh_token, decode_refresh_token


async def register_account(session: AsyncSession, account_data: AccountCreate) -> AccountResponse:
    """
    Register a new account.

    Args:
        session: Database session
        account_data: Account creation data

    Returns:
        Created account data

    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username or email already exists
    if await account_repository.account_exists_by_username_or_email(
        session, account_data.username, account_data.email
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists"
        )

    # Hash password and create account
    hashed_password = hash_password(account_data.password)
    new_account = await account_repository.create_account_with_data(
        session=session,
        username=account_data.username,
        email=account_data.email,
        password_hash=hashed_password,
        full_name=account_data.full_name
    )

    return AccountResponse.model_validate(new_account)


async def login_account(session: AsyncSession, email: str, password: str) -> TokenPair:
    """
    Login an account.

    Args:
        session: Database session
        email: Account email
        password: Account password

    Returns:
        Token pair (access and refresh tokens)

    Raises:
        HTTPException: If credentials are invalid or account is inactive
    """
    # Find account by email
    account = await account_repository.get_account_by_email(session, email)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if account is active
    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )

    # Verify password
    if not verify_password(password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create tokens
    access_token = create_access_token(account.id, account.email)
    refresh_token = create_refresh_token(account.id, account.email)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token
    )


async def refresh_tokens(session: AsyncSession, refresh_token: str) -> TokenPair:
    """
    Refresh access token using refresh token.

    Args:
        session: Database session
        refresh_token: Valid refresh token

    Returns:
        New token pair

    Raises:
        HTTPException: If refresh token is invalid or account not found
    """
    try:
        payload = decode_refresh_token(refresh_token)
        account_id = int(payload.get("sub"))
        email = payload.get("email")
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify account still exists and is active
    account = await account_repository.get_account_by_id(session, account_id)

    if not account or not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found or disabled"
        )

    # Create new tokens
    access_token = create_access_token(account.id, account.email)
    new_refresh_token = create_refresh_token(account.id, account.email)

    return TokenPair(
        access_token=access_token,
        refresh_token=new_refresh_token
    )


async def get_account_by_id(session: AsyncSession, account_id: int) -> AccountResponse:
    """
    Get account by ID.

    Args:
        session: Database session
        account_id: Account ID

    Returns:
        Account data

    Raises:
        HTTPException: If account not found
    """
    account = await account_repository.get_account_by_id(session, account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return AccountResponse.model_validate(account)