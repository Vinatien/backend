"""Bank Account service for business logic."""

import requests
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import bank_account_repository
from app.bank.vpbank import VPBank
from app.types.bank_account_dtos import (
    BankAccountResponse,
    BankProviderEnum,
    BalanceResponse
)
from app.types.exceptions import (
    BusinessRuleException,
    ConflictException,
    NotFoundException
)


async def get_user_bank_account(
    session: AsyncSession,
    account_id: int
) -> Optional[BankAccountResponse]:
    """
    Get the bank account associated with a user.

    Args:
        session: Database session
        account_id: User account ID

    Returns:
        Bank account details if exists, None otherwise
    """
    bank_account = await bank_account_repository.get_bank_account_by_account_id(
        session, account_id
    )

    if not bank_account:
        return None

    return BankAccountResponse.model_validate(bank_account)


async def get_balance(
    session: AsyncSession,
    bank_account_id: int,
    account_id: int
) -> BalanceResponse:
    """
    Get the current balance for a bank account.

    Args:
        session: Database session
        bank_account_id: Bank account ID
        account_id: User account ID (for ownership validation)

    Returns:
        Current balance with amount and currency

    Raises:
        NotFoundException: If bank account not found
        BusinessRuleException: If consent expired or balance fetch fails
    """
    # Get and validate bank account ownership
    bank_account = await bank_account_repository.get_bank_account_by_id(
        session, bank_account_id, account_id
    )
    if not bank_account:
        raise NotFoundException("Bank account not found")

    # Validate consent is still valid
    if bank_account.consent_status != "valid":
        raise BusinessRuleException(f"Consent is {bank_account.consent_status}")

    # Initialize bank client
    bank_session = requests.Session()
    bank_session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "TPP-Redirect-URI": "https://www.google.ch",
        "PSU-IP-Address": "192.0.0.12",
        "Consent-ID": bank_account.consent_id
    })

    bank_client = VPBank(bank_session)

    try:
        # Fetch balance from bank
        success, balance_data = bank_client.get_balance(
            bank_account.iban,
            f"Balance check for bank_account_id {bank_account_id}"
        )

        if not success or not balance_data:
            raise BusinessRuleException("Failed to fetch balance from bank")

        return BalanceResponse(
            amount=balance_data.get("amount", "0"),
            currency=balance_data.get("currency", "EUR")
        )

    except requests.exceptions.HTTPError as e:
        raise BusinessRuleException(f"Bank API error: {str(e)}")
    except Exception as e:
        raise BusinessRuleException(f"Failed to get balance: {str(e)}")


async def link_bank_account(
    session: AsyncSession,
    account_id: int,
    bank_provider: BankProviderEnum
) -> BankAccountResponse:
    """
    Create consent and link bank account.

    Args:
        session: Database session
        account_id: User account ID
        bank_provider: Bank provider enum

    Returns:
        Created bank account

    Raises:
        ConflictException: If user already has a bank account or consent creation fails
        BusinessRuleException: If IBAN cannot be retrieved
    """
    # Check if user already has a bank account
    existing_account = await bank_account_repository.get_bank_account_by_account_id(
        session, account_id
    )
    if existing_account:
        raise ConflictException("User already has a bank account linked")

    # Initialize bank client (currently only VPBank)
    if bank_provider != BankProviderEnum.VPBANK:
        raise BusinessRuleException("Only VPBank is currently supported")

    # Create requests session with required headers
    bank_session = requests.Session()
    bank_session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "TPP-Redirect-URI": "https://www.google.ch",
        "PSU-IP-Address": "192.0.0.12"
    })

    bank_client = VPBank(bank_session)

    try:
        # Create consent and get IBAN
        iban = bank_client.create_consent_and_get_iban()

        # Extract consent ID from session headers
        consent_id = bank_session.headers.get("Consent-ID")
        if not consent_id:
            raise BusinessRuleException("Failed to retrieve consent ID from bank")

        # Validate IBAN by attempting to fetch balance
        print(f"Validating IBAN {iban} by fetching balance...")
        success, balance_data = bank_client.get_balance(
            iban,
            f"IBAN validation for account_id {account_id}"
        )

        if not success:
            raise BusinessRuleException(
                f"IBAN {iban} is not accessible or invalid. "
                "The bank API returned an error when trying to access this account."
            )

        # Set consent validity (90 days as per VPBank implementation)
        consent_valid_until = datetime.now() + timedelta(days=90)

        # Check if consent already exists
        existing = await bank_account_repository.get_bank_account_by_consent_id(
            session, consent_id
        )
        if existing:
            raise ConflictException("This bank account is already linked")

        # Create bank account record
        bank_account = await bank_account_repository.create_bank_account(
            session=session,
            account_id=account_id,
            bank_provider="vpbank",
            consent_id=consent_id,
            iban=iban,
            consent_valid_until=consent_valid_until
        )

        return BankAccountResponse.model_validate(bank_account)

    except requests.exceptions.HTTPError as e:
        raise BusinessRuleException(f"Bank API error: {str(e)}")
    except Exception as e:
        raise BusinessRuleException(f"Failed to link bank account: {str(e)}")
