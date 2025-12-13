import requests
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import bank_account_repository, transaction_repository
from app.utils.encryption import encryption_service
from app.bank.vpbank import VPBank
from app.types.transaction_dtos import (
    TransactionResponse,
    TransactionListResponse,
    SyncTransactionsResponse
)
from app.types.exceptions import NotFoundException, BusinessRuleException
from models.transaction_model import Transaction


def _decrypt_transaction(transaction: Transaction) -> TransactionResponse:
    """
    Map fields from the new Transaction model to the DTO.
    
    NOTE: Decryption logic is removed because the new model stores 
    creditor_name and debtor_name directly (unencrypted).

    Args:
        transaction: Transaction model 

    Returns:
        TransactionResponse with mapped fields
    """
    return TransactionResponse(
        id=transaction.id,
        booking_date=transaction.booking_date,
        value_date=transaction.value_date,
        amount=transaction.amount,
        currency=transaction.currency,
        
        booking_status=transaction.booking_status,
        creditor_name=transaction.creditor_name, 
        debtor_name=transaction.debtor_name,
        creditor_account_last4=transaction.creditor_account_last4,
        debtor_account_last4=transaction.debtor_account_last4,
        created_at=transaction.created_at
    )


async def get_transactions(
    session: AsyncSession,
    bank_account_id: int,
    account_id: int,
    limit: int = 100,
    offset: int = 0
) -> TransactionListResponse:
    """
    Get transactions for a bank account with decryption.

    Args:
        session: Database session
        bank_account_id: Bank account ID
        account_id: User account ID (for ownership validation)
        limit: Pagination limit
        offset: Pagination offset

    Returns:
        List of decrypted transactions

    Raises:
        NotFoundException: If bank account not found
    """
    # Validate ownership
    bank_account = await bank_account_repository.get_bank_account_by_id(
        session, bank_account_id, account_id
    )
    if not bank_account:
        raise NotFoundException("Bank account not found")

    # Get transactions
    transactions = await transaction_repository.get_transactions_by_bank_account(
        session, bank_account_id, limit, offset
    )

    # Decrypt and convert to DTOs
    decrypted_transactions = [_decrypt_transaction(tx) for tx in transactions]

    # Get total count
    total = await transaction_repository.count_transactions_by_bank_account(
        session, bank_account_id
    )

    return TransactionListResponse(
        transactions=decrypted_transactions,
        total=total,
        bank_account_id=bank_account_id
    )


def _extract_last4(iban: Optional[str]) -> Optional[str]:
    """Extract last 4 characters from IBAN."""
    if not iban:
        return None
    return iban[-4:] if len(iban) >= 4 else iban


async def sync_transactions_from_bank(
    session: AsyncSession,
    bank_account_id: int,
    account_id: int
) -> SyncTransactionsResponse:
    """
    Sync transactions from bank API.

    Args:
        session: Database session
        bank_account_id: Bank account ID
        account_id: User account ID

    Returns:
        Sync results

    Raises:
        NotFoundException: If bank account not found
        BusinessRuleException: If consent expired or sync fails
    """
    # Get bank account
    bank_account = await bank_account_repository.get_bank_account_by_id(
        session, bank_account_id, account_id
    )
    if not bank_account:
        raise NotFoundException("Bank account not found")

    # Validate consent is still valid
    if bank_account.consent_status != "valid":
        raise BusinessRuleException(f"Consent is {bank_account.consent_status}")

    # FIX: Use datetime.now(timezone.utc) to compare offset-aware datetimes
    if bank_account.consent_valid_until < datetime.now(timezone.utc): 
        raise BusinessRuleException("Consent has expired")

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
        # Fetch transactions from bank
        success, tx_data = bank_client.get_transactions_and_review(
            bank_account.iban,
            f"Sync for bank_account_id {bank_account_id}"
        )

        if not success:
            raise BusinessRuleException("Failed to fetch transactions from bank")
        print("tx_data:", tx_data)
        # Process booked and pending transactions
        booked = tx_data.get("booked", [])
        pending = tx_data.get("pending", [])
        all_transactions = booked + pending
        new_count = 0
        transactions_to_create = []

        for tx in all_transactions:
            # --- 1. Extract and Calculate Fields for Compound Unique Key ---

            # Parse booking date (Required for unique key)
            booking_date_str = tx.get("bookingDate")
            # Default to UTC now if date is missing (though it should be present for uniqueness)
            booking_date = datetime.fromisoformat(booking_date_str) if booking_date_str else datetime.now(timezone.utc)

            # Extract and convert amount (Required for unique key)
            amount_value = Decimal(str(tx.get("transactionAmount", {}).get("amount", "0")))

            # Extract account info (Required for unique key)
            creditor_iban = tx.get("creditorAccount", {}).get("iban")
            debtor_iban = tx.get("debtorAccount", {}).get("iban")
            
            creditor_last4 = _extract_last4(creditor_iban)
            debtor_last4 = _extract_last4(debtor_iban)
        

            # --- 3. Extract Remaining Fields for Insertion ---

            # Parse value date (Optional field)
            value_date_str = tx.get("valueDate")
            value_date = datetime.fromisoformat(value_date_str) if value_date_str else None

            # Extract names directly (since encryption fields were removed)
            creditor_name = tx.get("creditorName")
            debtor_name = tx.get("debtorName")
            
            # NOTE: remittanceInformationUnstructured is NOT in your model, so we skip extraction

            # 4. Create Transaction Object
            transaction = Transaction(
                bank_account_id=bank_account_id,
                
                # --- Unique Key Fields ---
                booking_date=booking_date,
                amount=amount_value,
                creditor_account_last4=creditor_last4,
                debtor_account_last4=debtor_last4,
                
                # --- Other Fields ---
                value_date=value_date,
                currency=tx.get("transactionAmount", {}).get("currency", "EUR"),
                
                # We are removing transaction_type because it wasn't in the model and wasn't in the input data.
                # If you need it, you must add a column to the model and infer the value here (e.g., based on amount sign).
                # transaction_type=tx.get("creditDebitIndicator"), 
                
                booking_status="booked" if tx in booked else "pending",

                # Direct names (Encryption fields removed from model)
                creditor_name=creditor_name,
                debtor_name=debtor_name,
            )
            transactions_to_create.append(transaction)
            new_count += 1

        # Bulk insert new transactions
        if transactions_to_create:
            await transaction_repository.bulk_create_transactions(
                session, transactions_to_create
            )

        # FIX: Use datetime.now(timezone.utc) to store an offset-aware time
        sync_time = datetime.now(timezone.utc)
        await bank_account_repository.update_bank_account_sync_time(
            session, bank_account_id, sync_time
        )

        return SyncTransactionsResponse(
            synced_count=len(all_transactions),
            new_transactions=new_count,
            last_synced_at=sync_time,
            message=f"Successfully synced {new_count} new transactions"
        )

    except requests.exceptions.HTTPError as e:
        raise BusinessRuleException(f"Bank API error: {str(e)}")
    except Exception as e:
        raise BusinessRuleException(f"Failed to sync transactions: {str(e)}")