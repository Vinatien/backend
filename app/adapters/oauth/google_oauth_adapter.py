from typing import Dict

from google.auth.transport.requests import AuthorizedSession
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as id_token_module
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.types.exceptions import AuthenticationException
from app.utils.settings import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URIS,
)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def exchange_code_for_credentials(
    code: str, code_verifier: str, redirect_uri: str
) -> Credentials:
    """Exchange authorization code for OAuth credentials using PKCE."""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": GOOGLE_TOKEN_URL,
                "redirect_uris": GOOGLE_REDIRECT_URIS,
            }
        },
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        redirect_uri=redirect_uri,
    )
    flow.code_verifier = code_verifier
    flow.fetch_token(code=code)
    return flow.credentials


def verify_id_token(creds: Credentials) -> Dict[str, str]:
    """Verify and decode Google ID token."""
    payload = id_token_module.verify_oauth2_token(
        creds.id_token,
        GoogleRequest(),
        GOOGLE_CLIENT_ID,
    )

    if payload.get("aud") != GOOGLE_CLIENT_ID:
        raise AuthenticationException("ID token audience mismatch")

    return payload


def fetch_full_profile(creds: Credentials) -> Dict[str, str]:
    """Fetch complete user profile from Google."""
    auth_sess = AuthorizedSession(creds)
    resp = auth_sess.get(GOOGLE_USERINFO_URL)
    resp.raise_for_status()
    return resp.json()