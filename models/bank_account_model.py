from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base_model import Base

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_provider = Column(String, nullable=False)
    consent_id = Column(String(255), nullable=False, unique=True, index=True)
    iban = Column(String(34), nullable=False)  # Max IBAN length is 34
    consent_valid_until = Column(DateTime(timezone=True), nullable=False)
    consent_status = Column(String(50), default="valid")  # valid, expired, revoked
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to Account
    account = relationship("Account", back_populates="bank_accounts")
    # Relationship to Transactions
    transactions = relationship("Transaction", back_populates="bank_account", cascade="all, delete-orphan")
