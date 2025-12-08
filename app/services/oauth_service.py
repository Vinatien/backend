"""OAuth service for Google authentication."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.oauth.google_oauth_adapter import (
    exchange_code_for_credentials,
    fetch_full_profile,
    verify_id_token,
)
from app.repositories import account_repository
from app.types.auth_dtos import TokenPair
from app.types.exceptions import AuthenticationException
from app.utils.token_utils import create_access_token, create_refresh_token
from models.account_model import Account


async def login_or_register_with_google(
    session: AsyncSession, code: str, code_verifier: str, redirect_uri: str
) -> TokenPair:
    """
    Login or register a user with Google OAuth.

    Args:
        session: Database session
        code: Authorization code from Google
        code_verifier: PKCE code verifier
        redirect_uri: Redirect URI used in OAuth flow

    Returns:
        TokenPair with access and refresh tokens

    Raises:
        AuthenticationException: If OAuth process fails
    """
    # Exchange authorization code for credentials
    creds = exchange_code_for_credentials(code, code_verifier, redirect_uri)

    # Verify ID token and extract email
    idinfo = verify_id_token(creds)
    email = idinfo.get("email")
    if not email:
        raise AuthenticationException("ID token missing email")

    # Fetch full user profile
    profile = fetch_full_profile(creds)

    # Check if user already exists
    existing_account = await account_repository.get_account_by_email(session, email)

    if existing_account:
        # User exists, check if active
        if not existing_account.is_active:
            raise AuthenticationException("Account is disabled")
        account = existing_account
    else:
        # Create new user account
        first_name = (
            profile.get("given_name")
            or profile.get("name", "").split()[0]
            or "User"
        )
        last_name = (
            profile.get("family_name")
            or (
                profile.get("name", "").split()[1]
                if len(profile.get("name", "").split()) > 1
                else ""
            )
            or ""
        )

        full_name = f"{first_name} {last_name}".strip()

        # Generate username from email (before @)
        username = email.split("@")[0]

        # Ensure username uniqueness
        counter = 1
        original_username = username
        while await account_repository.get_account_by_username(session, username):
            username = f"{original_username}{counter}"
            counter += 1

        # Create account with dummy password hash (OAuth users don't use password login)
        account = await account_repository.create_account_with_data(
            session=session,
            username=username,
            email=email,
            password_hash="oauth_user_no_password",  # Placeholder for OAuth users
            full_name=full_name
        )

    # Generate JWT tokens
    access_token = create_access_token(account.id, account.email)
    refresh_token = create_refresh_token(account.id, account.email)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token
    )