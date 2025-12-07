"""Add menu_item_options table and make orders.combo_id nullable

Revision ID: 004
Revises: 003
Create Date: 2025-12-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create menu_item_options table
    op.create_table(
        'menu_item_options',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('menu_item_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('values', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on menu_item_id for performance
    op.create_index('idx_menu_item_options_menu_item_id', 'menu_item_options', ['menu_item_id'])

    # Make orders.combo_id nullable to support standalone orders
    op.alter_column('orders', 'combo_id',
                    existing_type=sa.Integer(),
                    nullable=True)


def downgrade() -> None:
    # Revert orders.combo_id to NOT NULL (requires all orders to have combo_id)
    op.alter_column('orders', 'combo_id',
                    existing_type=sa.Integer(),
                    nullable=False)

    # Drop index
    op.drop_index('idx_menu_item_options_menu_item_id', table_name='menu_item_options')

    # Drop menu_item_options table
    op.drop_table('menu_item_options')
