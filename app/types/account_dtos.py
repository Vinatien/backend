"""Account DTOs for user data."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class AccountBase(BaseModel):
    """Base account DTO with common fields."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class AccountCreate(AccountBase):
    """Account creation DTO."""
    password: str


class AccountUpdate(BaseModel):
    """Account update DTO."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class AccountResponse(AccountBase):
    """Account response DTO."""
    id: int
    email: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccountRead(BaseModel):
    """Account read DTO for authorization service."""
    account_id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    account_verified: bool = True  # Mapped from is_active
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True