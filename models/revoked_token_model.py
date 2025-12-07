"""Revoked tokens model for token blacklisting."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class RevokedToken(Base):
    """Model for tracking revoked tokens."""
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(Text, unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    token_type = Column(String(50), nullable=False)  # 'access', 'refresh'
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_expired = Column(Boolean, default=False)