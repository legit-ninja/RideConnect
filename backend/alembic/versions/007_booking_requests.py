"""booking requests

Revision ID: 007_booking_requests
Revises: 006_friend_invites
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_booking_requests"
down_revision: Union[str, None] = "006_friend_invites"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    payment_type = postgresql.ENUM("paid", "free", name="payment_type", create_type=True)
    booking_status = postgresql.ENUM(
        "pending_payment",
        "pending_owner",
        "approved",
        "declined",
        "cancelled",
        name="booking_status",
        create_type=True,
    )
    payment_type.create(bind, checkfirst=True)
    booking_status.create(bind, checkfirst=True)

    op.create_table(
        "booking_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("friend_invite_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "payment_type",
            postgresql.ENUM("paid", "free", name="payment_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending_payment",
                "pending_owner",
                "approved",
                "declined",
                "cancelled",
                name="booking_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["rider_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["friend_invite_id"], ["friend_invites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_booking_requests_listing_id", "booking_requests", ["listing_id"])
    op.create_index("ix_booking_requests_rider_id", "booking_requests", ["rider_id"])
    op.create_index("ix_booking_requests_owner_id", "booking_requests", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_booking_requests_owner_id", table_name="booking_requests")
    op.drop_index("ix_booking_requests_rider_id", table_name="booking_requests")
    op.drop_index("ix_booking_requests_listing_id", table_name="booking_requests")
    op.drop_table("booking_requests")
    op.execute("DROP TYPE IF EXISTS booking_status")
    op.execute("DROP TYPE IF EXISTS payment_type")
