"""threads, messages, reviews, listing photos, events

Revision ID: 009_threads_reviews
Revises: 008_user_names_flags
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_threads_reviews"
down_revision: Union[str, None] = "008_user_names_flags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    moderation_status = postgresql.ENUM(
        "pending", "approved", "rejected", name="moderation_status", create_type=True
    )
    moderation_status.create(bind, checkfirst=True)

    op.create_table(
        "threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("friend_invite_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(booking_request_id IS NULL) <> (friend_invite_id IS NULL)",
            name="ck_threads_exactly_one_parent",
        ),
        sa.ForeignKeyConstraint(["booking_request_id"], ["booking_requests.id"]),
        sa.ForeignKeyConstraint(["friend_invite_id"], ["friend_invites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_threads_booking_request_id",
        "threads",
        ["booking_request_id"],
        unique=True,
        postgresql_where=sa.text("booking_request_id IS NOT NULL"),
    )
    op.create_index(
        "uq_threads_friend_invite_id",
        "threads",
        ["friend_invite_id"],
        unique=True,
        postgresql_where=sa.text("friend_invite_id IS NOT NULL"),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["thread_id"], ["threads.id"]),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_thread_id", "messages", ["thread_id"])

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "moderation_status",
            postgresql.ENUM(
                "pending", "approved", "rejected", name="moderation_status", create_type=False
            ),
            server_default="approved",
            nullable=False,
        ),
        sa.Column("is_friend_ride", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["booking_request_id"], ["booking_requests.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewee_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "booking_request_id", "reviewer_id", name="uq_review_booking_reviewer"
        ),
    )

    op.create_table(
        "listing_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("thumbnail_key", sa.String(length=512), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "moderation_status",
            postgresql.ENUM(
                "pending", "approved", "rejected", name="moderation_status", create_type=False
            ),
            server_default="approved",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listing_photos_listing_id", "listing_photos", ["listing_id"])

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("src", sa.String(length=64), nullable=True),
        sa.Column("listing_slug", sa.String(length=128), nullable=True),
        sa.Column("invite_token", sa.String(length=64), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_event_type", "events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_listing_photos_listing_id", table_name="listing_photos")
    op.drop_table("listing_photos")
    op.drop_table("reviews")
    op.drop_index("ix_messages_thread_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("uq_threads_friend_invite_id", table_name="threads")
    op.drop_index("uq_threads_booking_request_id", table_name="threads")
    op.drop_table("threads")
    op.execute("DROP TYPE IF EXISTS moderation_status")
