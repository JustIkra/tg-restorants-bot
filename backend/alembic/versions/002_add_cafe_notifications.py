"""Add cafe notifications support

Revision ID: 002
Revises: 001
Create Date: 2025-12-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Telegram notification fields to cafes table
    op.add_column(
        "cafes",
        sa.Column("tg_chat_id", sa.BigInteger(), nullable=True)
    )
    op.add_column(
        "cafes",
        sa.Column("tg_username", sa.String(255), nullable=True)
    )
    op.add_column(
        "cafes",
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default="true")
    )
    op.add_column(
        "cafes",
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=True)
    )

    # Create cafe_link_requests table
    op.create_table(
        "cafe_link_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cafe_id", sa.Integer(), nullable=False),
        sa.Column("tg_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("tg_username", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["cafe_id"], ["cafes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create CHECK constraint for status field
    op.create_check_constraint(
        "ck_cafe_link_requests_status",
        "cafe_link_requests",
        "status IN ('pending', 'approved', 'rejected')"
    )

    # Create indexes for better query performance
    op.create_index(
        "ix_cafe_link_requests_cafe_id",
        "cafe_link_requests",
        ["cafe_id"]
    )
    op.create_index(
        "ix_cafe_link_requests_status",
        "cafe_link_requests",
        ["status"]
    )
    op.create_index(
        "ix_cafe_link_requests_cafe_id_status",
        "cafe_link_requests",
        ["cafe_id", "status"]
    )
    op.create_index(
        "ix_cafe_link_requests_created_at",
        "cafe_link_requests",
        ["created_at"]
    )


def downgrade() -> None:
    # Drop cafe_link_requests table and its indexes
    op.drop_index("ix_cafe_link_requests_created_at", "cafe_link_requests")
    op.drop_index("ix_cafe_link_requests_cafe_id_status", "cafe_link_requests")
    op.drop_index("ix_cafe_link_requests_status", "cafe_link_requests")
    op.drop_index("ix_cafe_link_requests_cafe_id", "cafe_link_requests")
    op.drop_constraint("ck_cafe_link_requests_status", "cafe_link_requests", type_="check")
    op.drop_table("cafe_link_requests")

    # Remove Telegram notification fields from cafes table
    op.drop_column("cafes", "linked_at")
    op.drop_column("cafes", "notifications_enabled")
    op.drop_column("cafes", "tg_username")
    op.drop_column("cafes", "tg_chat_id")
