"""Transaction repository for data access operations."""

from typing import List
from sqlalchemy import select, desc, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from decimal import Decimal

from models.transaction_model import Transaction


async def get_transactions_by_bank_account(
    session: AsyncSession,
    bank_account_id: int,
    limit: int = 100,
    offset: int = 0
) -> List[Transaction]:
    """Get transactions for a bank account with pagination."""
    result = await session.execute(
        select(Transaction)
        .where(Transaction.bank_account_id == bank_account_id)
        .order_by(desc(Transaction.booking_date))
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def count_transactions_by_bank_account(
    session: AsyncSession,
    bank_account_id: int
) -> int:
    """Count total transactions for a bank account."""
    result = await session.execute(
        select(func.count()).select_from(Transaction)
        .where(Transaction.bank_account_id == bank_account_id)
    )
    return result.scalar()


async def transaction_exists(
    session: AsyncSession,
    bank_account_id: int,
    transaction_id: str
) -> bool:
    """Check if transaction already exists."""
    result = await session.execute(
        select(Transaction).where(
            and_(
                Transaction.bank_account_id == bank_account_id,
                Transaction.transaction_id == transaction_id
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def transaction_exists_by_details(
    session: AsyncSession,
    bank_account_id: int,
    booking_date: datetime,
    amount: Decimal,
    creditor_account_last4: str | None,
    debtor_account_last4: str | None
) -> bool:
    """Check if transaction exists based on composite unique key."""
    result = await session.execute(
        select(Transaction).where(
            and_(
                Transaction.bank_account_id == bank_account_id,
                Transaction.booking_date == booking_date,
                Transaction.amount == amount,
                Transaction.creditor_account_last4 == creditor_account_last4,
                Transaction.debtor_account_last4 == debtor_account_last4
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def bulk_create_transactions(
    session: AsyncSession,
    transactions: List[Transaction]
) -> int:
    """Bulk insert transactions."""
    session.add_all(transactions)
    await session.commit()
    return len(transactions)
