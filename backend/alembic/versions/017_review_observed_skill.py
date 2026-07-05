"""Owner-observed rider skill on reviews.

Revision ID: 017_review_observed_skill
Revises: 016_listing_community_fields
Create Date: 2026-07-05
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "017_review_observed_skill"
down_revision: Union[str, None] = "016_listing_community_fields"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("observed_rider_skill", sa.SmallInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "observed_rider_skill")
