"""Add users.is_vendor (split from 020 for idempotent prod upgrades).

Revision ID: 021_users_is_vendor
Revises: 020_shop_vendor_funnel
Create Date: 2026-08-02

Prod may already have is_vendor from an earlier 020 revision; upgrade is a no-op
when the column exists. Fresh installs get the column here after 020 shop tables.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "021_users_is_vendor"
down_revision: Union[str, None] = "020_shop_vendor_funnel"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "users" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "is_vendor" in columns:
        return
    op.add_column(
        "users",
        sa.Column("is_vendor", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "users" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "is_vendor" not in columns:
        return
    op.drop_column("users", "is_vendor")
