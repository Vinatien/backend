import requests
import time
from app.bank.vpbank import VPBank, PAYMENT_AMOUNT


def main():
    """
    Main test script for VPBank API using the VPBank class.
    Replicates the working script flow exactly.
    """
    # Initialize session with required headers
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "TPP-Redirect-URI": "https://www.google.ch",
        "PSU-IP-Address": "192.0.0.12"
    })

    # Initialize VPBank instance
    vpbank = VPBank(session)

    # =========================================================================
    # STEP 1: Create Consent (AISP)
    # =========================================================================
    try:
        target_account_id = vpbank.create_consent_and_get_iban()
    except Exception as e:
        print(f"\n❌ Consent creation FAILED: {e}")
        return

    # =========================================================================
    # STEP 3: Get Transactions (Test AISP read with target_account_id)
    # =========================================================================
    vpbank.get_transactions_and_review(target_account_id, "AISP-Initial")

    # =========================================================================
    # STEP 4 & 5: Make Payment (PISP write with target_account_id)
    # =========================================================================
    # print("\n\n--- INITIATING PISP FLOW ---")
    # try:
    #     # STEP 4: Create payment using the discovered IBAN as the DEBTOR
    #     payment_id = vpbank.make_payment(
    #         debtor_iban=target_account_id,
    #         amount=PAYMENT_AMOUNT
    #     )
    #     time.sleep(1)

    #     # STEP 5: Check Status
    #     payment_status = vpbank.check_payment_status(payment_id)

    # except requests.exceptions.HTTPError as e:
    #     print(f"\n❌ PISP Flow FAILED: {e}")
    #     return


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as e:
        print(f"\nFATAL ERROR: A network or critical request error occurred: {e}")
