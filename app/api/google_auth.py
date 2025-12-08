from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.database import get_session
from app.services.oauth_service import login_or_register_with_google
from app.types.auth_dtos import GoogleAuthCodeRequest, TokenPair

router = APIRouter()


@router.post(
    "/token",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary="Authenticate via Google (Auth Code + PKCE)",
    description=(
        "Exchange a one-time authorization code (with PKCE verifier) for an ID + "
        "access token, verify them, fetch full profile, and return your app's JWTs."
    ),
)
async def google_token_auth(
    request: GoogleAuthCodeRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Authenticate user via Google OAuth.

    This endpoint:
    1. Exchanges the authorization code for Google credentials
    2. Verifies the ID token
    3. Fetches user profile information
    4. Creates or retrieves user account
    5. Returns JWT access and refresh tokens

    Args:
        request: Google OAuth request containing code, code_verifier, and redirect_uri
        session: Database session

    Returns:
        TokenPair: Contains access_token and refresh_token
    """
    return await login_or_register_with_google(
        session=session,
        code=request.code,
        code_verifier=request.code_verifier,
        redirect_uri=request.redirect_uri,
    )