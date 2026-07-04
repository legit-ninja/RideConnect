"""user names, booking completed, platform flags, notifications

Revision ID: 008_user_names_flags
Revises: 007_booking_requests
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_user_names_flags"
down_revision: Union[str, None] = "007_booking_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "users",
        sa.Column("first_name", sa.String(length=100), server_default="Member", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("last_name", sa.String(length=100), server_default="", nullable=False),
    )
    op.alter_column("users", "first_name", server_default=None)
    op.alter_column("users", "last_name", server_default=None)

    op.execute("ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'completed'")
    op.add_column(
        "booking_requests",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    flag_type = postgresql.ENUM(
        "invite_redemption_rate",
        "minor_invite_skew",
        "off_platform_contact",
        name="platform_flag_type",
        create_type=True,
    )
    flag_type.create(bind, checkfirst=True)

    op.create_table(
        "platform_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "flag_type",
            postgresql.ENUM(
                "invite_redemption_rate",
                "minor_invite_skew",
                "off_platform_contact",
                name="platform_flag_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_platform_flags_user_id", "platform_flags", ["user_id"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_platform_flags_user_id", table_name="platform_flags")
    op.drop_table("platform_flags")
    op.execute("DROP TYPE IF EXISTS platform_flag_type")
    op.drop_column("booking_requests", "completed_at")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
