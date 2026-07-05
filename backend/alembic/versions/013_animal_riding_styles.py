"""animal riding styles

Revision ID: 013_animal_riding_styles
Revises: 012_listing_availability_slots
Create Date: 2026-07-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013_animal_riding_styles"
down_revision: Union[str, None] = "012_listing_availability_slots"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "animals",
        sa.Column(
            "riding_styles",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("animals", "riding_styles")
