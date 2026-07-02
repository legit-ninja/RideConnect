"""friend invites

Revision ID: 006_friend_invites
Revises: 005_admin_audit_listing
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_friend_invites"
down_revision: Union[str, None] = "005_admin_audit_listing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

friend_invite_status = postgresql.ENUM(
    "pending",
    "accepted",
    "declined",
    "cancelled",
    name="friend_invite_status",
    create_type=True,
)


def upgrade() -> None:
    bind = op.get_bind()
    friend_invite_status.create(bind, checkfirst=True)

    op.create_table(
        "friend_invites",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rider_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("invitee_email", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "accepted",
                "declined",
                "cancelled",
                name="friend_invite_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "invited_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["rider_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_friend_invites_owner_id", "friend_invites", ["owner_id"])
    op.create_index("ix_friend_invites_rider_id", "friend_invites", ["rider_id"])
    op.create_index(
        "ix_friend_invites_invitee_email", "friend_invites", ["invitee_email"]
    )


def downgrade() -> None:
    op.drop_index("ix_friend_invites_invitee_email", table_name="friend_invites")
    op.drop_index("ix_friend_invites_rider_id", table_name="friend_invites")
    op.drop_index("ix_friend_invites_owner_id", table_name="friend_invites")
    op.drop_table("friend_invites")
    op.execute("DROP TYPE IF EXISTS friend_invite_status")
