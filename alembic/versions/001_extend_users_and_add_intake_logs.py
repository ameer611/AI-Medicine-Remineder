"""Extend users table and add intake_logs and web_sessions tables.

Revision ID: 001_extend_users_and_add_intake_logs
Revises: 
Create Date: 2026-04-28 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "001_extend_users_and_add_intake_logs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column(
        "users",
        sa.Column("full_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("phone_number", sa.String(length=20), nullable=True),
    )
    # role enum
    user_role_enum = sa.Enum("user", "supervisor", name="user_role")
    user_role_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column("role", user_role_enum, nullable=False, server_default="user"),
    )
    # supervisor_id with SET NULL on delete
    op.add_column(
        "users",
        sa.Column("supervisor_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_supervisor_id",
        "users",
        "users",
        ["supervisor_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "users",
        sa.Column("web_session_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("web_session_expires_at", sa.DateTime(), nullable=True),
    )

    # Indexes
    op.create_index(op.f("ix_users_phone_number"), "users", ["phone_number"], unique=False)
    op.create_index(op.f("ix_users_supervisor_id"), "users", ["supervisor_id"], unique=False)
    op.create_index(op.f("ix_users_web_session_id"), "users", ["web_session_id"], unique=False)

    # Add unique constraint on phone_number and web_session_id
    op.create_unique_constraint(op.f("uq_users_phone_number"), "users", ["phone_number"])
    op.create_unique_constraint(op.f("uq_users_web_session_id"), "users", ["web_session_id"])

    # Create intake_logs table
    op.create_table(
        "intake_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("medication_id", sa.Integer(), sa.ForeignKey("medications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scheduled_time", sa.String(length=5), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("consumed", "not_consumed", "felt_bad", name="intake_status"),
            nullable=False,
        ),
        sa.Column("logged_at", sa.DateTime(), server_default=sa.func.utc_timestamp(), nullable=False),
    )

    op.create_index(op.f("ix_intake_logs_user_date"), "intake_logs", ["user_id", "scheduled_date"], unique=False)
    op.create_index(op.f("ix_intake_logs_med_date"), "intake_logs", ["medication_id", "scheduled_date"], unique=False)

    # Create web_sessions table
    op.create_table(
        "web_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(length=255), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.utc_timestamp(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_web_sessions_session_id"), "web_sessions", ["session_id"], unique=True)


def downgrade() -> None:
    # Drop web_sessions
    op.drop_index(op.f("ix_web_sessions_session_id"), table_name="web_sessions")
    op.drop_table("web_sessions")

    # Drop intake_logs
    op.drop_index(op.f("ix_intake_logs_med_date"), table_name="intake_logs")
    op.drop_index(op.f("ix_intake_logs_user_date"), table_name="intake_logs")
    op.drop_table("intake_logs")
    # Drop enum intake_status
    sa.Enum(name="intake_status").drop(op.get_bind(), checkfirst=True)

    # Drop users added columns and constraints
    op.drop_constraint(op.f("uq_users_web_session_id"), "users", type_="unique")
    op.drop_constraint(op.f("uq_users_phone_number"), "users", type_="unique")
    op.drop_index(op.f("ix_users_web_session_id"), table_name="users")
    op.drop_index(op.f("ix_users_supervisor_id"), table_name="users")
    op.drop_index(op.f("ix_users_phone_number"), table_name="users")
    op.drop_column("users", "web_session_expires_at")
    op.drop_column("users", "web_session_id")
    op.drop_constraint("fk_users_supervisor_id", "users", type_="foreignkey")
    op.drop_column("users", "supervisor_id")
    op.drop_column("users", "role")
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
    op.drop_column("users", "phone_number")
    op.drop_column("users", "full_name")
