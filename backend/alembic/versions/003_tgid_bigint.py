"""Change tgid to BIGINT for large Telegram user IDs

Revision ID: 003
Revises: 002
Create Date: 2025-12-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change orders.user_tgid first (FK references users.tgid)
    op.alter_column('orders', 'user_tgid',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)

    # Then change users.tgid (PK)
    op.alter_column('users', 'tgid',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)


def downgrade() -> None:
    # Reverse order for downgrade: PK first, then FK
    op.alter_column('users', 'tgid',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False)

    op.alter_column('orders', 'user_tgid',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False)
