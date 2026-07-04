"""user profile photo storage key

Revision ID: 011_user_profile_photo
Revises: 010_public_invite_tokens
Create Date: 2026-07-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_user_profile_photo"
down_revision: Union[str, None] = "010_public_invite_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("profile_photo_storage_key", sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "profile_photo_storage_key")
