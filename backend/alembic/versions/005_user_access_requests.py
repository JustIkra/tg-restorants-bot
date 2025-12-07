"""Add user_access_requests table

Revision ID: 005
Revises: 004
Create Date: 2025-12-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_access_requests table
    op.create_table(
        'user_access_requests',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tgid', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('office', sa.String(255), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tgid'),
    )

    # Create index on status for filtering
    op.create_index('idx_user_access_requests_status', 'user_access_requests', ['status'])


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_user_access_requests_status', table_name='user_access_requests')

    # Drop user_access_requests table
    op.drop_table('user_access_requests')
