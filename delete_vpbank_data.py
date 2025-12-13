import requests
import json
import uuid
from datetime import datetime, timedelta
import time

# --- CONFIGURATION ---
BASE_URL = "https://developer.vpbank.com/psd2/berlin-group/v1"

def print_step(title, data):
    print(f"\n--- {title} ---")
    print(json.dumps(data, indent=2))

def generate_request_id(last_digit='1'):
    """Generates a random UUID, allowing the last digit to be controlled for mock status."""
    base_uuid = str(uuid.uuid4())
    return base_uuid[:-1] + last_digit

# --- AISP Functions (to get the working IBAN) ---

def create_consent_and_get_iban(session):
    """Creates consent and extracts the working IBAN (target_account_id)."""
    print("1. Creating Consent...")
    session.headers.update({"X-Request-ID": generate_request_id('1')})
    
    consent_payload = {
        "access": ["accounts", "balances", "transactions", "confirmationOfFunds"],
        "recurringIndicator": True,
        "validUntil": (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
        "frequencyPerDay": 4
    }
    
    resp = session.post(f"{BASE_URL}/consents", json=consent_payload)
    resp.raise_for_status()
    consent_id = resp.json().get("consentId")
    session.headers.update({"Consent-ID": consent_id})
    print(f"✅ Consent ID: {consent_id}")

    print(f"\n2. Finding Working IBAN via Consent Status Check...")
    session.headers.update({"X-Request-ID": generate_request_id('2')}) 
    resp = session.get(f"{BASE_URL}/consents/{consent_id}")
    resp.raise_for_status()
    
    target_account_list = resp.json().get("access", {}).get("transactions", [])
    if not target_account_list:
        raise ValueError("CRITICAL FAILURE: Cannot find a working IBAN.")
        
    target_account_id = target_account_list[0]
    print(f"✅ Success! Discovered Target IBAN: {target_account_id}")
    return target_account_id

def get_transaction_count(session, account_id):
    """Fetches and counts current transactions."""
    session.headers.update({"X-Request-ID": generate_request_id('9')})
    date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    date_to = datetime.now().strftime('%Y-%m-%d')
    params = {"dateFrom": date_from, "dateTo": date_to, "bookingStatus": "all"}
    url = f"{BASE_URL}/accounts/{account_id}/transactions"
    
    try:
        resp = session.get(url, params=params)
        resp.raise_for_status()
        tx_data = resp.json()
        count = len(tx_data.get("booked", [])) + len(tx_data.get("pending", []))
        return count
    except requests.exceptions.HTTPError as e:
        print(f"Warning: Could not fetch transaction count before deletion: {e}")
        return -1

# --- SANDBOX DELETE FUNCTION ---

def delete_all_transactions(session, account_id):
    """
    Attempts to delete ALL transactions for the given mock account using 
    a non-standard sandbox cleanup endpoint.
    """
    print(f"\n3. Attempting to DELETE ALL transactions for {account_id}...")
    
    # This is a common pattern for sandbox cleanup. 
    # It is highly likely this specific endpoint will return 404/403 
    # if VPBank did not implement it.
    delete_url = f"{BASE_URL}/sandbox/accounts/{account_id}/transactions"
    
    # We must use a separate, non-AISP X-Request-ID for this call
    session.headers.update({"X-Request-ID": generate_request_id('5')}) 
    # NOTE: We must NOT send the Consent-ID header for this non-standard call.
    if "Consent-ID" in session.headers:
        del session.headers["Consent-ID"]

    try:
        resp = session.delete(delete_url)
        
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

# --- Main Flow ---
def main():
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "TPP-Redirect-URI": "https://www.google.ch",
        "PSU-IP-Address": "192.0.0.12"
    })

    try:
        # Get the working IBAN first
        target_account_id = create_consent_and_get_iban(session)
        
        # Check transaction count BEFORE deletion
        count_before = get_transaction_count(session, target_account_id)
        if count_before != -1:
            print(f"Current Transaction Count BEFORE Deletion: {count_before}")

        # Attempt Deletion
        if delete_all_transactions(session, target_account_id):
            time.sleep(2) # Wait for sandbox update

            # Check transaction count AFTER deletion
            # Note: We must recreate consent headers for this check
            target_account_id = create_consent_and_get_iban(session) 
            count_after = get_transaction_count(session, target_account_id)
            if count_after != -1:
                 print(f"\nTransaction Count AFTER Deletion: {count_after}")
                 if count_after < count_before:
                     print("🎉 Sandbox cleanup confirmed: Transaction count reduced!")
                 else:
                     print("⚠️ Cleanup inconclusive: Transaction count did not change.")

    except requests.exceptions.RequestException as e:
        print(f"\nFATAL ERROR: A critical request error occurred: {e}")
    except ValueError as e:
        print(f"\nFATAL ERROR: {e}")

if __name__ == "__main__":
    main()