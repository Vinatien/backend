"""Bank Account repository for data access operations."""

from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from models.bank_account_model import BankAccount


async def create_bank_account(
    session: AsyncSession,
    account_id: int,
    bank_provider: str,
    consent_id: str,
    iban: str,
    consent_valid_until: datetime
) -> BankAccount:
    """Create a new bank account link."""
    bank_account = BankAccount(
        account_id=account_id,
        bank_provider=bank_provider,
        consent_id=consent_id,
        iban=iban,
        consent_valid_until=consent_valid_until,
        consent_status="valid",
        is_active=True
    )
    session.add(bank_account)
    await session.commit()
    await session.refresh(bank_account)
    return bank_account


async def get_bank_account_by_id(
    session: AsyncSession,
    bank_account_id: int,
    account_id: int
) -> Optional[BankAccount]:
    """Get bank account by ID, ensuring it belongs to the specified account."""
    result = await session.execute(
        select(BankAccount).where(
            and_(
                BankAccount.id == bank_account_id,
                BankAccount.account_id == account_id
            )
        )
    )
    return result.scalar_one_or_none()


async def get_bank_account_by_consent_id(
    session: AsyncSession,
    consent_id: str
) -> Optional[BankAccount]:
    """Get bank account by consent ID."""
    result = await session.execute(
        select(BankAccount).where(BankAccount.consent_id == consent_id)
    )
    return result.scalar_one_or_none()


async def update_bank_account_sync_time(
    session: AsyncSession,
    bank_account_id: int,
    sync_time: datetime
) -> BankAccount:
    """Update last synced timestamp."""
    result = await session.execute(
        select(BankAccount).where(BankAccount.id == bank_account_id)
    )
    bank_account = result.scalar_one()
    bank_account.last_synced_at = sync_time
    await session.commit()
    await session.refresh(bank_account)
    return bank_account
