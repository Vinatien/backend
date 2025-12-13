"""add bank accounts and transactions tables

Revision ID: 17d3af435f87
Revises: 00e118b062b5
Create Date: 2025-12-12 22:18:39.438630

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17d3af435f87'
down_revision: Union[str, Sequence[str], None] = '00e118b062b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create bank_accounts table
    op.create_table(
        'bank_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('bank_provider', sa.Enum('vpbank', name='bankprovider'), nullable=False),
        sa.Column('consent_id', sa.String(length=255), nullable=False),
        sa.Column('iban', sa.String(length=34), nullable=False),
        sa.Column('consent_valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consent_status', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_accounts_id'), 'bank_accounts', ['id'], unique=False)
    op.create_index(op.f('ix_bank_accounts_account_id'), 'bank_accounts', ['account_id'], unique=False)
    op.create_index(op.f('ix_bank_accounts_consent_id'), 'bank_accounts', ['consent_id'], unique=True)

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bank_account_id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(length=255), nullable=False),
        sa.Column('booking_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('value_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=True),
        sa.Column('booking_status', sa.String(length=50), nullable=False),
        sa.Column('encrypted_description', sa.Text(), nullable=True),
        sa.Column('encrypted_creditor_name', sa.Text(), nullable=True),
        sa.Column('encrypted_debtor_name', sa.Text(), nullable=True),
        sa.Column('creditor_account_last4', sa.String(length=4), nullable=True),
        sa.Column('debtor_account_last4', sa.String(length=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bank_account_id', 'transaction_id', name='uq_bank_account_transaction')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_bank_account_id'), 'transactions', ['bank_account_id'], unique=False)
    op.create_index(op.f('ix_transactions_booking_date'), 'transactions', ['booking_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_transactions_booking_date'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_bank_account_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')

    op.drop_index(op.f('ix_bank_accounts_consent_id'), table_name='bank_accounts')
    op.drop_index(op.f('ix_bank_accounts_account_id'), table_name='bank_accounts')
    op.drop_index(op.f('ix_bank_accounts_id'), table_name='bank_accounts')
    op.drop_table('bank_accounts')

    op.execute('DROP TYPE bankprovider')
