from abc import ABC, abstractmethod

import requests


class Bank(ABC):
    """Abstract Base Class defining the standard interface for a TPP connection."""
    
    def __init__(self, session: requests.Session):
        self.session = session

    @abstractmethod
    def create_consent_and_get_iban(self) -> str:
        """Creates an AISP consent and returns the working IBAN/Resource ID."""
        pass

    @abstractmethod
    def get_transaction_count(self, account_id: str) -> int:
        """Fetches and counts current transactions for an account."""
        pass

    @abstractmethod
    def delete_all_transactions(self, account_id: str) -> bool:
        """Attempts to delete all transactions for cleanup (Sandbox-only)."""
        pass

    @abstractmethod
    def create_mock_deposit(self, account_id: str, amount: str) -> bool:
        """
        Attempts to create a mock deposit/credit on the account (Sandbox-only). 
        This is NOT a PSD2 standard method.
        """
        pass

    @abstractmethod
    def make_payment(self, debtor_iban: str, amount: str, creditor_iban: str, creditor_bic: str) -> str:
        """Initiates a payment (PISP) and returns the payment ID."""
        pass

    @abstractmethod
    def check_payment_status(self, payment_id: str) -> str:
        """Checks the status of a pending payment."""
        pass