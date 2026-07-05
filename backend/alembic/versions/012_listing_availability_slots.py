"""listing availability slots

Revision ID: 012_listing_availability_slots
Revises: 011_user_profile_photo
Create Date: 2026-07-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_listing_availability_slots"
down_revision: Union[str, None] = "011_user_profile_photo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    slot_status = postgresql.ENUM(
        "open", "held", "booked", "blocked", name="slot_status", create_type=True
    )
    slot_status.create(bind, checkfirst=True)

    op.create_table(
        "listing_availability_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "open",
                "held",
                "booked",
                "blocked",
                name="slot_status",
                create_type=False,
            ),
            nullable=False,
            server_default="open",
        ),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_listing_availability_slots_listing_id",
        "listing_availability_slots",
        ["listing_id"],
    )
    op.create_index(
        "ix_listing_availability_slots_start_at",
        "listing_availability_slots",
        ["start_at"],
    )

    op.add_column(
        "booking_requests",
        sa.Column("availability_slot_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_booking_requests_availability_slot_id",
        "booking_requests",
        "listing_availability_slots",
        ["availability_slot_id"],
        ["id"],
    )
    op.create_index(
        "ix_booking_requests_availability_slot_id",
        "booking_requests",
        ["availability_slot_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_booking_requests_availability_slot_id", table_name="booking_requests")
    op.drop_constraint(
        "fk_booking_requests_availability_slot_id", "booking_requests", type_="foreignkey"
    )
    op.drop_column("booking_requests", "availability_slot_id")
    op.drop_index("ix_listing_availability_slots_start_at", table_name="listing_availability_slots")
    op.drop_index(
        "ix_listing_availability_slots_listing_id", table_name="listing_availability_slots"
    )
    op.drop_table("listing_availability_slots")
    op.execute("DROP TYPE IF EXISTS slot_status")
