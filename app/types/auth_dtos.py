"""Authentication DTOs for requests and responses."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request DTO."""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Register request DTO."""
    username: str
    email: EmailStr
    password: str
    full_name: str = None


class TokenPair(BaseModel):
    """Token pair response DTO (internal use)."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Authentication response DTO (only access token, refresh token sent as cookie)."""
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Generic message response DTO."""
    message: str


class GoogleAuthCodeRequest(BaseModel):
    """Google OAuth authorization code request DTO."""
    code: str
    code_verifier: str
    redirect_uri: str