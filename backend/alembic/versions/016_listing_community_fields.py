"""Listing community fields: min rider skill, weight limit, gear expectations.

Revision ID: 016_listing_community_fields
Revises: 015_trainer_rider_skill
Create Date: 2026-07-05
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_listing_community_fields"
down_revision: Union[str, None] = "015_trainer_rider_skill"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None

tack_provided = sa.Enum("provided", "bring_own", "either", name="tack_provided")


def upgrade() -> None:
    tack_provided.create(op.get_bind(), checkfirst=True)
    op.add_column("listings", sa.Column("min_rider_skill", sa.SmallInteger(), nullable=True))
    op.add_column("listings", sa.Column("max_rider_weight_lbs", sa.Integer(), nullable=True))
    op.add_column(
        "listings",
        sa.Column(
            "helmet_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "listings",
        sa.Column(
            "tack_provided",
            tack_provided,
            nullable=False,
            server_default="either",
        ),
    )
    op.alter_column("listings", "helmet_required", server_default=None)
    op.alter_column("listings", "tack_provided", server_default=None)


def downgrade() -> None:
    op.drop_column("listings", "tack_provided")
    op.drop_column("listings", "helmet_required")
    op.drop_column("listings", "max_rider_weight_lbs")
    op.drop_column("listings", "min_rider_skill")
    tack_provided.drop(op.get_bind(), checkfirst=True)
