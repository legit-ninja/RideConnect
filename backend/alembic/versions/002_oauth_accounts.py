"""oauth accounts table and nullable password_hash

Revision ID: 002_oauth_accounts
Revises: 001_create_users
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_oauth_accounts"
down_revision: Union[str, None] = "001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

oauth_provider = postgresql.ENUM(
    "google",
    "facebook",
    name="oauth_provider",
    create_type=True,
)


def upgrade() -> None:
    bind = op.get_bind()
    oauth_provider.create(bind, checkfirst=True)

    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=True,
    )

    op.create_table(
        "oauth_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "provider",
            postgresql.ENUM(
                "google",
                "facebook",
                name="oauth_provider",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("provider_email", sa.String(length=255), nullable=True),
        sa.Column("provider_email_verified", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_subject"),
        sa.UniqueConstraint("user_id", "provider", name="uq_oauth_user_provider"),
    )
    op.create_index("ix_oauth_accounts_user_id", "oauth_accounts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_oauth_accounts_user_id", table_name="oauth_accounts")
    op.drop_table("oauth_accounts")
    oauth_provider.drop(op.get_bind(), checkfirst=True)

    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False,
    )
