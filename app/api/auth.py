"""Authentication routes for register and login."""

from fastapi import APIRouter, Depends, Response, Cookie, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.database import get_session
from app.services import auth_service
from app.types.account_dtos import AccountCreate, AccountResponse
from app.types.auth_dtos import LoginRequest, AuthResponse
from app.utils.settings import ENVIRONMENT, REFRESH_TOKEN_EXPIRES_IN

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
    response_model=AuthResponse,
    summary="Login account"
)
async def login(
    response: Response,
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_session)
) -> AuthResponse:
    """
    Login user account.

    Args:
        response: FastAPI response object to set cookies
        login_data: Login credentials
        session: Database session

    Returns:
        Access token (refresh token sent as httpOnly cookie)

    Raises:
        401: Invalid credentials or account disabled
    """
    token_pair = await auth_service.login_account(
        session,
        login_data.email,
        login_data.password
    )

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=token_pair.refresh_token,
        httponly=True,
        secure=ENVIRONMENT == "production",
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRES_IN
    )

    return AuthResponse(
        access_token=token_pair.access_token,
        token_type=token_pair.token_type
    )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh access token"
)
async def refresh_token(
    response: Response,
    session: AsyncSession = Depends(get_session),
    refresh_token: str = Cookie(None)
) -> AuthResponse:
    """
    Refresh access token using refresh token from httpOnly cookie.

    Args:
        response: FastAPI response object to set cookies
        session: Database session
        refresh_token: Refresh token from httpOnly cookie

    Returns:
        New access token (new refresh token sent as httpOnly cookie)

    Raises:
        401: Invalid or missing refresh token
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )

    token_pair = await auth_service.refresh_tokens(session, refresh_token)

    # Set new refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=token_pair.refresh_token,
        httponly=True,
        secure=ENVIRONMENT == "production",
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRES_IN
    )

    return AuthResponse(
        access_token=token_pair.access_token,
        token_type=token_pair.token_type
    )