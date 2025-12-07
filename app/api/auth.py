"""Authentication routes for register and login."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.database import get_session
from app.services import auth_service
from app.types.account_dtos import AccountCreate, AccountResponse
from app.types.auth_dtos import LoginRequest, TokenPair, RefreshTokenRequest

router = APIRouter()


@router.post(
    "/register",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new account"
)
async def register(
    account_data: AccountCreate,
    session: AsyncSession = Depends(get_session)
) -> AccountResponse:
    """
    Register a new user account.

    Args:
        account_data: User registration data
        session: Database session

    Returns:
        Created account information

    Raises:
        409: Username or email already exists
    """
    return await auth_service.register_account(session, account_data)


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Login account"
)
async def login(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_session)
) -> TokenPair:
    """
    Login user account.

    Args:
        login_data: Login credentials
        session: Database session

    Returns:
        Access and refresh tokens

    Raises:
        401: Invalid credentials or account disabled
    """
    return await auth_service.login_account(
        session,
        login_data.email,
        login_data.password
    )


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh access token"
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session)
) -> TokenPair:
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token data
        session: Database session

    Returns:
        New access and refresh tokens

    Raises:
        401: Invalid refresh token
    """
    return await auth_service.refresh_tokens(session, refresh_data.refresh_token)