"""add is_trainer to users

Revision ID: 014_user_is_trainer
Revises: 013_animal_riding_styles
Create Date: 2026-07-05

"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_user_is_trainer"
down_revision: Union[str, None] = "013_animal_riding_styles"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_trainer", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("users", "is_trainer")
