from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base_model import Base


class Transaction(Base):
    __tablename__ = "transactions"

    # --- Primary Key and Foreign Key ---
    id = Column(Integer, primary_key=True, index=True)
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Fields directly from tx_data ---
    
    # Dates
    booking_date = Column(DateTime(timezone=True), nullable=False, index=True) # Source: 'bookingDate'
    value_date = Column(DateTime(timezone=True), nullable=True)               # Source: 'valueDate'

    # Amount & Currency
    amount = Column(Numeric(15, 2), nullable=False)                          # Source: 'transactionAmount.amount'
    currency = Column(String(3), nullable=False)                             # Source: 'transactionAmount.currency'

    # Counterparty Details (using the source names directly)
    creditor_name = Column(String(255), nullable=True)                       # Source: 'creditorName'
    debtor_name = Column(String(255), nullable=True)                         # Source: 'debtorName'
    
    # Account Identifiers (Last 4 derived from IBANs)
    creditor_account_last4 = Column(String(4), nullable=True)                # Derived from 'creditorAccount.iban'
    debtor_account_last4 = Column(String(4), nullable=True)                  # Derived from 'debtorAccount.iban'
    
    # Status (Inferred from list position, but needed)
    booking_status = Column(String(50), nullable=False)                      # Inferred: "booked" or "pending"

    # --- Audit & Relationships ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    bank_account = relationship("BankAccount", back_populates="transactions")
