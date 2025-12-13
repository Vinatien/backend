"""Bank Account DTOs for requests and responses."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class BankProviderEnum(str, Enum):
    """Supported bank providers"""
    VPBANK = "vpbank"


class ConsentStatus(str, Enum):
    """Consent status values"""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"


class LinkBankAccountRequest(BaseModel):
    """Request to link a bank account."""
    bank_provider: BankProviderEnum = Field(default=BankProviderEnum.VPBANK)


class BankAccountResponse(BaseModel):
    """Response containing bank account details."""
    id: int
    bank_provider: BankProviderEnum
    iban: str
    consent_valid_until: datetime
    consent_status: ConsentStatus
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BankAccountListResponse(BaseModel):
    """Response containing list of bank accounts."""
    bank_accounts: list[BankAccountResponse]
    total: int
