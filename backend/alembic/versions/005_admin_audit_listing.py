"""extend admin_audit_action for listing moderation

Revision ID: 005_admin_audit_listing
Revises: 004_species_animals_listings
Create Date: 2026-07-01

"""

from typing import Sequence, Union

from alembic import op

revision: str = "005_admin_audit_listing"
down_revision: Union[str, None] = "004_species_animals_listings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE admin_audit_action ADD VALUE IF NOT EXISTS 'listing_deactivated'"
    )
    op.execute(
        "ALTER TYPE admin_audit_action ADD VALUE IF NOT EXISTS 'listing_reactivated'"
    )


def downgrade() -> None:
    pass
