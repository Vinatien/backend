"""Transaction DTOs for requests and responses."""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel


class TransactionResponse(BaseModel):
    """Response containing transaction details, aligned with the simplified model."""
    id: int
    
    # --- Dates ---
    booking_date: datetime
    value_date: Optional[datetime]
    
    # --- Amount & Status ---
    amount: Decimal
    currency: str
    booking_status: str

    # --- Counterparties ---
    creditor_name: Optional[str] = None
    debtor_name: Optional[str] = None
    
    # --- Account Identifiers ---
    creditor_account_last4: Optional[str] = None
    debtor_account_last4: Optional[str] = None
    
    # --- Audit ---
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Response containing list of transactions."""
    transactions: list[TransactionResponse]
    total: int
    bank_account_id: int


class SyncTransactionsResponse(BaseModel):
    """Response after syncing transactions."""
    synced_count: int
    new_transactions: int
    last_synced_at: datetime
    message: str
