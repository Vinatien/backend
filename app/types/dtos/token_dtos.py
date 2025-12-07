"""Token DTOs for authorization and authentication."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TokenValidationRequest(BaseModel):
    """Request DTO for token validation."""
    token: str


class TokenValidationResponse(BaseModel):
    """Response DTO for token validation."""
    valid: bool
    account_id: Optional[int] = None
    email: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


class RevokeTokenRequest(BaseModel):
    """Request DTO for token revocation."""
    token: str


class TokenCleanupResponse(BaseModel):
    """Response DTO for token cleanup operations."""
    tokens_removed: int
    message: str