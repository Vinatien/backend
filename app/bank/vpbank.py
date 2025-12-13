from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import requests
from app.bank.base_bank import Bank
from app.bank.utils import generate_request_id


# PISP Details (Static details for the recipient)
CREDITOR_ACCOUNT_IBAN = "DE89370400440532013000"
CREDITOR_BIC = "COBADEFF"
PAYMENT_AMOUNT = "100.50"
DEBIT_BIC = "VPBPLI22"


class VPBank(Bank):
    """Concrete implementation for the VPBank Berlin Group API."""

    BASE_URL = "https://developer.vpbank.com/psd2/berlin-group/v1"

    # --- AISP & Cleanup Methods (From user context, kept for completeness) ---

    def create_consent_and_get_iban(self) -> str:
        """Creates consent and extracts the working IBAN (target_account_id)."""
        print("1. Creating Consent...")
        self.session.headers.update({"X-Request-ID": generate_request_id('1')})
        
        consent_payload = {
            "access": ["accounts", "balances", "transactions", "confirmationOfFunds"],
            "recurringIndicator": True,
            "validUntil": (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
            "frequencyPerDay": 4
        }
        
        resp = self.session.post(f"{self.BASE_URL}/consents", json=consent_payload)
        resp.raise_for_status()
        consent_id = resp.json().get("consentId")
        self.session.headers.update({"Consent-ID": consent_id})
        print(f"✅ Consent ID: {consent_id}")

        print(f"\n2. Finding Working IBAN via Consent Status Check...")
        self.session.headers.update({"X-Request-ID": generate_request_id('2')})
        resp = self.session.get(f"{self.BASE_URL}/consents/{consent_id}")
        resp.raise_for_status()

        consent_data = resp.json()
        print(f"DEBUG: Full consent response: {consent_data}")

        target_account_list = consent_data.get("access", {}).get("transactions", [])
        if not target_account_list:
            raise ValueError("CRITICAL FAILURE: Cannot find a working IBAN.")

        print(f"DEBUG: Available accounts: {target_account_list}")

        # Try to use the first account
        target_account_id = target_account_list[0]
        print(f"✅ Success! Discovered Target IBAN: {target_account_id}")
        return target_account_id

    def get_transaction_count(self, account_id: str) -> int:
        """Fetches and counts current transactions."""
        self.session.headers.update({"X-Request-ID": generate_request_id('9')})
        date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')
        params = {"dateFrom": date_from, "dateTo": date_to, "bookingStatus": "all"}
        url = f"{self.BASE_URL}/accounts/{account_id}/transactions"

        try:
            resp = self.session.get(url, params=params)
            resp.raise_for_status()
            tx_data = resp.json()
            count = len(tx_data.get("booked", [])) + len(tx_data.get("pending", []))
            return count
        except requests.exceptions.HTTPError as e:
            print(f"Warning: Could not fetch transaction count before deletion: {e}")
            return -1

    def get_transactions_and_review(self, account_id: str, step_name: str):
            """Fetches all transactions and provides a detailed review."""
            print(f"\n[{step_name}] Fetching ALL Transactions for {account_id}...")
            self.session.headers.update({"X-Request-ID": generate_request_id('9')})

            date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            date_to = datetime.now().strftime('%Y-%m-%d')

            # Use 'all' to capture both pending (PISP) and booked (mock) transactions
            params = {"dateFrom": date_from, "dateTo": date_to, "bookingStatus": "all"}
            url = f"{self.BASE_URL}/accounts/{account_id}/transactions"

            try:
                resp = self.session.get(url, params=params)
                resp.raise_for_status()

                tx_data = resp.json()
                booked = tx_data.get("booked", [])
                pending = tx_data.get("pending", [])

                print(f"✅ Success! Found {len(booked)} booked and {len(pending)} pending transactions.")

                all_transactions = booked + pending

                if all_transactions:
                    print("\n--- Review of Transactions (Incoming/Outgoing) ---")

                    # Count the types of transactions
                    incoming_count = 0
                    outgoing_count = 0

                    for tx in all_transactions:
                        tx_amount = tx.get('transactionAmount', {})
                        # Check if the transaction's debtor (sender) is YOUR account ID
                        if tx.get('debtorAccount', {}).get('iban') == account_id:
                            direction = "**OUTGOING PAYMENT (DEBIT)**"
                            outgoing_count += 1
                        else:
                            direction = "INCOMING PAYMENT (CREDIT)"
                            incoming_count += 1

                        print(f"  > {direction}: {tx_amount.get('amount')} {tx_amount.get('currency')} (Date: {tx.get('bookingDate', 'N/A')})")

                    print(f"\nSummary: {incoming_count} incoming (CREDIT), {outgoing_count} outgoing (DEBIT).")

                return True, tx_data

            except requests.exceptions.HTTPError as e:
                print(f"\n❌ FAILED at {step_name} (Transactions): {e}")
                print(f"Response Body: {resp.text}")
                return False, None

    def get_balance(self, account_id: str, step_name: str):
        """Fetches the balance for an account."""
        print(f"\n[{step_name}] Fetching Balance for {account_id}...")
        self.session.headers.update({"X-Request-ID": generate_request_id('4')})

        url = f"{self.BASE_URL}/accounts/{account_id}/balances"

        try:
            resp = self.session.get(url)
            resp.raise_for_status()

            balance_data = resp.json()
            # Extract the current balance amount
            current_balance = balance_data.get("balances", [{}])[0].get("balanceAmount", {})

            print(f"✅ Success! Current Balance: {current_balance.get('amount')} {current_balance.get('currency')}")
            return True, current_balance

        except requests.exceptions.HTTPError as e:
            print(f"\n❌ FAILED at {step_name} (Balance): {e}")
            print(f"Response Body: {resp.text}")
            return False, None

    def delete_all_transactions(self, account_id: str) -> bool:
        """
        Attempts to delete ALL transactions for the given mock account using 
        a non-standard sandbox cleanup endpoint.
        """
        print(f"\n3. Attempting to DELETE ALL transactions for {account_id}...")
        
        # Sandbox cleanup pattern
        delete_url = f"{self.BASE_URL}/sandbox/accounts/{account_id}/transactions"
        
        self.session.headers.update({"X-Request-ID": generate_request_id('5')}) 
        if "Consent-ID" in self.session.headers:
            del self.session.headers["Consent-ID"]

        try:
            resp = self.session.delete(delete_url)
            
            if resp.status_code == 200 or resp.status_code == 204:
                print(f"✅ SUCCESS! Sandbox cleanup request accepted (Status: {resp.status_code}).")
                return True
            elif resp.status_code == 404:
                print(f"❌ FAILED (Status: 404 Not Found). The sandbox does not use the expected cleanup endpoint: {delete_url}")
                return False
            else:
                resp.raise_for_status()
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ FAILED to delete transactions: {e}")
            print("Response Body:", resp.text)
            return False

    # --- PISP Methods (Implemented) ---

    def make_payment(self, debtor_iban: str, amount: str, creditor_iban: str = CREDITOR_ACCOUNT_IBAN, creditor_bic: str = CREDITOR_BIC) -> str:
        """
        Initiates a SEPA Credit Transfer payment (PISP) and returns the payment ID.
        Uses static defaults for the creditor for sandbox convenience.
        """
        print("\n[PISP] 4. Initiating SEPA Credit Transfer Payment...")

        payment_request_id = generate_request_id('8')  # '8' for mock success status
        self.session.headers.update({"X-Request-ID": payment_request_id})

        payment_payload = {
            # Debtor IBAN uses the discovered target_account_id
            "debtorAccount": {"iban": debtor_iban, "bic": DEBIT_BIC},
            "instructedAmount": {"currency": "EUR", "amount": amount},
            "creditorAccount": {"iban": creditor_iban, "bic": creditor_bic},
            "creditorName": "Test Recipient GmbH",
            "remittanceInformationUnstructured": "Payment for services rendered",
            "requestedExecutionDate": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        }

        url_init = f"{self.BASE_URL}/payments/sepa-credit-transfers"

        resp = self.session.post(url_init, json=payment_payload)
        resp.raise_for_status()

        payment_data = resp.json()
        payment_id = payment_data.get("paymentId")

        print(f"✅ Success! Payment ID Created: {payment_id}")
        return payment_id
    
    def create_mock_deposit(self, account_id: str, amount: str) -> bool:
        """
        Attempts to create a mock credit/deposit transaction on the account 
        using a common, NON-STANDARD sandbox endpoint.
        """
        print(f"\n4. Attempting to CREATE MOCK DEPOSIT of EUR {amount} for {account_id}...")
        
        # NOTE: This endpoint is an *educated guess* based on common sandbox patterns.
        deposit_url = f"{self.BASE_URL}/sandbox/accounts/{account_id}/transactions" 
        
        # Payload for an incoming Credit transaction
        mock_transaction_payload = {
            "transactionAmount": {"currency": "EUR", "amount": amount},
            "bookingDate": datetime.now().strftime('%Y-%m-%d'),
            "valueDate": datetime.now().strftime('%Y-%m-%d'),
            "creditorAccount": {"iban": account_id}, # Target is the Creditor
            "debtorName": "MockDeposit Source",
            "debtorAccount": {"iban": "DE99111111112222222233"},
            "remittanceInformationUnstructured": "Sandbox Deposit"
        }
        
        # Must ensure Consent-ID is NOT sent for this non-standard call.
        if "Consent-ID" in self.session.headers:
            del self.session.headers["Consent-ID"]
            
        self.session.headers.update({"X-Request-ID": generate_request_id('6')})

        try:
            # We use POST assuming it creates a new mock transaction resource
            resp = self.session.post(deposit_url, json=mock_transaction_payload)
            
            if resp.status_code == 201:
                print(f"✅ SUCCESS! Mock deposit request accepted (Status: {resp.status_code}).")
                return True
            elif resp.status_code == 404:
                print(f"❌ FAILED (Status: 404 Not Found). The sandbox does not use the expected mock deposit endpoint: {deposit_url}")
                return False
            else:
                resp.raise_for_status()
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ FAILED to create mock deposit: {e}")
            print("Response Body:", resp.text)
            return False
    
    def check_payment_status(self, payment_id: str) -> str:
        """
        Checks the transaction status of a previously initiated payment.
        """
        print(f"\n[PISP] 5. Fetching Payment Status for {payment_id}...")

        self.session.headers.update({"X-Request-ID": generate_request_id('2')})
        # Use the proven SHORTENED URL path for status check
        status_url = f"{self.BASE_URL}/payments/{payment_id}/status"

        resp = self.session.get(status_url)
        resp.raise_for_status()

        status_data = resp.json()
        final_status = status_data.get("transactionStatus")

        print(f"🎉 PISP Status Check Complete. Status: {final_status} 🎉")
        return final_status