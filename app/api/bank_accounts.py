"""Bank Account routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.db.database import get_session
from app.services import bank_account_service, transaction_service
from app.services.authorization_service import authorize_authenticated_account
from app.types.account_dtos import AccountRead
from app.types.bank_account_dtos import (
    LinkBankAccountRequest,
    BankAccountResponse
)
from app.types.transaction_dtos import (
    TransactionListResponse,
    SyncTransactionsResponse
)

router = APIRouter()


@router.get(
    "/",
    response_model=BankAccountResponse | None,
    summary="Get user's bank account"
)
async def get_user_bank_account(
    session: AsyncSession = Depends(get_session),
    account: AccountRead = Depends(authorize_authenticated_account())
) -> BankAccountResponse | None:
    """
    Get the bank account associated with the authenticated user.

    Args:
        session: Database session
        account: Authenticated user account

    Returns:
        Bank account details if exists, None otherwise
    """
    return await bank_account_service.get_user_bank_account(
        session=session,
        account_id=account.account_id
    )


@router.post(
    "/link",
    response_model=BankAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link bank account"
)
async def link_bank_account(
    request: LinkBankAccountRequest,
    session: AsyncSession = Depends(get_session),
    account: AccountRead = Depends(authorize_authenticated_account())
) -> BankAccountResponse:
    """
    Create consent and link a bank account.

    Args:
        request: Bank provider information
        session: Database session
        account: Authenticated user account

    Returns:
        Created bank account details

    Raises:
        409: If consent already exists
        400: If consent creation fails
    """
    return await bank_account_service.link_bank_account(
        session=session,
        account_id=account.account_id,
        bank_provider=request.bank_provider
    )


@router.get(
    "/{bank_account_id}/transactions",
    response_model=TransactionListResponse,
    summary="Get transactions for bank account"
)
async def get_transactions(
    bank_account_id: int,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    account: AccountRead = Depends(authorize_authenticated_account())
) -> TransactionListResponse:
    """
    Fetch and return transactions for a bank account.

    Args:
        bank_account_id: Bank account ID
        limit: Maximum number of transactions to return
        offset: Pagination offset
        session: Database session
        account: Authenticated user account

    Returns:
        List of transactions with decrypted sensitive data

    Raises:
        404: If bank account not found
    """
    return await transaction_service.get_transactions(
        session=session,
        bank_account_id=bank_account_id,
        account_id=account.account_id,
        limit=limit,
        offset=offset
    )


@router.post(
    "/{bank_account_id}/sync",
    response_model=SyncTransactionsResponse,
    summary="Sync transactions from bank"
)
async def sync_transactions(
    bank_account_id: int,
    session: AsyncSession = Depends(get_session),
    account: AccountRead = Depends(authorize_authenticated_account())
) -> SyncTransactionsResponse:
    """
    Manually sync new transactions from bank API.

    Args:
        bank_account_id: Bank account ID
        session: Database session
        account: Authenticated user account

    Returns:
        Sync results including count of new transactions

    Raises:
        404: If bank account not found
        400: If consent expired or sync fails
    """
    return await transaction_service.sync_transactions_from_bank(
        session=session,
        bank_account_id=bank_account_id,
        account_id=account.account_id
    )
