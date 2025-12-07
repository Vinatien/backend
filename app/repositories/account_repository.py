"""Account repository for data access operations."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.account_model import Account


async def get_account_by_id(session: AsyncSession, account_id: int) -> Optional[Account]:
    """
    Retrieve account by ID.

    Args:
        session: Database session
        account_id: Account ID to retrieve

    Returns:
        Account model or None if not found
    """
    result = await session.execute(
        select(Account).where(Account.id == account_id)
    )
    return result.scalar_one_or_none()


async def get_account_by_email(session: AsyncSession, email: str) -> Optional[Account]:
    """
    Retrieve account by email.

    Args:
        session: Database session
        email: Account email to search for

    Returns:
        Account model or None if not found
    """
    result = await session.execute(
        select(Account).where(Account.email == email)
    )
    return result.scalar_one_or_none()


async def get_account_by_username(session: AsyncSession, username: str) -> Optional[Account]:
    """
    Retrieve account by username.

    Args:
        session: Database session
        username: Account username to search for

    Returns:
        Account model or None if not found
    """
    result = await session.execute(
        select(Account).where(Account.username == username)
    )
    return result.scalar_one_or_none()


async def create_account(session: AsyncSession, account: Account) -> Account:
    """
    Create a new account.

    Args:
        session: Database session
        account: Account model to create

    Returns:
        Created account model
    """
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account


async def update_account(session: AsyncSession, account: Account) -> Account:
    """
    Update an existing account.

    Args:
        session: Database session
        account: Account model with updates

    Returns:
        Updated account model
    """
    await session.commit()
    await session.refresh(account)
    return account


async def delete_account(session: AsyncSession, account_id: int) -> bool:
    """
    Delete an account by ID.

    Args:
        session: Database session
        account_id: Account ID to delete

    Returns:
        True if account was deleted, False if not found
    """
    result = await session.execute(
        select(Account).where(Account.id == account_id)
    )
    account = result.scalar_one_or_none()

    if account:
        await session.delete(account)
        await session.commit()
        return True
    return False


async def account_exists_by_username_or_email(session: AsyncSession, username: str, email: str) -> bool:
    """
    Check if an account exists with the given username or email.

    Args:
        session: Database session
        username: Username to check
        email: Email to check

    Returns:
        True if account exists, False otherwise
    """
    result = await session.execute(
        select(Account).where(
            (Account.username == username) |
            (Account.email == email)
        )
    )
    return result.scalar_one_or_none() is not None


async def create_account_with_data(session: AsyncSession, username: str, email: str, password_hash: str, full_name: str = None) -> Account:
    """
    Create a new account with the provided data.

    Args:
        session: Database session
        username: Account username
        email: Account email
        password_hash: Hashed password
        full_name: Optional full name

    Returns:
        Created account model
    """
    new_account = Account(
        username=username,
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        is_active=True
    )

    session.add(new_account)
    await session.commit()
    await session.refresh(new_account)
    return new_account