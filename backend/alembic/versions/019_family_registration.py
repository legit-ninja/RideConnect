"""Family rider profile, roster, and grouped bookings.

Revision ID: 019_family_registration
Revises: 018_location_backfill
Create Date: 2026-07-05
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "019_family_registration"
down_revision: Union[str, None] = "018_location_backfill"
branch_labels: Union[str, tuple[str, ...], None] = None
depends_on: Union[str, tuple[str, ...], None] = None

rider_type = sa.Enum("individual", "family", name="rider_type")


def upgrade() -> None:
    rider_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column(
            "rider_type",
            rider_type,
            nullable=False,
            server_default="individual",
        ),
    )
    op.add_column("users", sa.Column("family_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("family_size", sa.SmallInteger(), nullable=True))

    op.create_table(
        "family_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("rider_skill_level", sa.SmallInteger(), nullable=True),
        sa.Column("is_minor", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_family_members_user_id"), "family_members", ["user_id"], unique=False)

    op.add_column(
        "booking_requests",
        sa.Column("family_booking_group_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "booking_requests",
        sa.Column("family_member_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "booking_requests",
        sa.Column("participant_display_name", sa.String(length=100), nullable=True),
    )
    op.create_index(
        op.f("ix_booking_requests_family_booking_group_id"),
        "booking_requests",
        ["family_booking_group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_booking_requests_family_member_id"),
        "booking_requests",
        ["family_member_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_booking_requests_family_member_id",
        "booking_requests",
        "family_members",
        ["family_member_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_booking_requests_family_member_id", "booking_requests", type_="foreignkey")
    op.drop_index(op.f("ix_booking_requests_family_member_id"), table_name="booking_requests")
    op.drop_index(
        op.f("ix_booking_requests_family_booking_group_id"),
        table_name="booking_requests",
    )
    op.drop_column("booking_requests", "participant_display_name")
    op.drop_column("booking_requests", "family_member_id")
    op.drop_column("booking_requests", "family_booking_group_id")
    op.drop_index(op.f("ix_family_members_user_id"), table_name="family_members")
    op.drop_table("family_members")
    op.drop_column("users", "family_size")
    op.drop_column("users", "family_name")
    op.drop_column("users", "rider_type")
    rider_type.drop(op.get_bind(), checkfirst=True)
