"""Alter users.telegram_id to BIGINT.

Revision ID: 002_alter_telegram_id_to_bigint
Revises: 001_extend_users_and_add_intake_logs
Create Date: 2026-04-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "002_alter_telegram_id_to_bigint"
down_revision = "001_extend_users_and_add_intake_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alter telegram_id to BIGINT to support large Telegram IDs
    op.alter_column(
        "users",
        "telegram_id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
        existing_server_default=None,
    )


def downgrade() -> None:
    # Revert telegram_id back to Integer (may fail if values out of range)
    op.alter_column(
        "users",
        "telegram_id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
        existing_server_default=None,
    )
