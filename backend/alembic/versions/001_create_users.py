"""create users table

Revision ID: 001_create_users
Revises:
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_create_users"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

verification_status = postgresql.ENUM(
    "unverified",
    "pending",
    "verified",
    "rejected",
    name="verification_status",
    create_type=True,
)


def upgrade() -> None:
    bind = op.get_bind()
    verification_status.create(bind, checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_rider", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_owner", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "verification_status",
            postgresql.ENUM(
                "unverified",
                "pending",
                "verified",
                "rejected",
                name="verification_status",
                create_type=False,
            ),
            nullable=False,
            server_default="unverified",
        ),
        sa.Column("is_minor", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("guardian_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["guardian_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    verification_status.drop(op.get_bind(), checkfirst=True)
