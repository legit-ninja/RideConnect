"""public listings slug/location, invite tokens, friend invite status expansion

Revision ID: 010_public_invite_tokens
Revises: 009_threads_reviews
Create Date: 2026-07-01

"""

import math
import random
import re
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_public_invite_tokens"
down_revision: Union[str, None] = "009_threads_reviews"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BASE32 = "abcdefghijklmnopqrstuvwxyz234567"


def _kebab(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "listing"


def _random_suffix() -> str:
    return "".join(random.choice(BASE32) for _ in range(6))


def _jitter(lat: float, lng: float) -> tuple[float, float]:
    distance_km = random.uniform(5.0, 8.0)
    bearing = random.uniform(0, 2 * math.pi)
    delta_lat = (distance_km / 111.0) * math.cos(bearing)
    delta_lng = (distance_km / (111.0 * math.cos(math.radians(lat)))) * math.sin(bearing)
    return lat + delta_lat, lng + delta_lng


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column("listings", sa.Column("slug", sa.String(length=128), nullable=True))
    op.add_column(
        "listings", sa.Column("display_location", sa.String(length=256), nullable=True)
    )
    op.add_column("listings", sa.Column("public_lat", sa.Float(), nullable=True))
    op.add_column("listings", sa.Column("public_lng", sa.Float(), nullable=True))

    rows = bind.execute(
        sa.text(
            """
            SELECT l.id, a.name, a.lat, a.lng
            FROM listings l
            JOIN animals a ON a.id = l.animal_id
            """
        )
    ).fetchall()
    used_slugs: set[str] = set()
    for row in rows:
        listing_id, animal_name, lat, lng = row
        base = _kebab(animal_name or "listing")
        slug = f"{base}-{_random_suffix()}"
        while slug in used_slugs:
            slug = f"{base}-{_random_suffix()}"
        used_slugs.add(slug)
        pub_lat, pub_lng = _jitter(float(lat), float(lng))
        bind.execute(
            sa.text(
                """
                UPDATE listings
                SET slug = :slug,
                    display_location = :display_location,
                    public_lat = :public_lat,
                    public_lng = :public_lng
                WHERE id = :id
                """
            ),
            {
                "slug": slug,
                "display_location": "Appalachian NC",
                "public_lat": pub_lat,
                "public_lng": pub_lng,
                "id": listing_id,
            },
        )

    op.alter_column("listings", "slug", nullable=False)
    op.alter_column("listings", "display_location", nullable=False)
    op.alter_column("listings", "public_lat", nullable=False)
    op.alter_column("listings", "public_lng", nullable=False)
    op.create_index("ix_listings_slug", "listings", ["slug"], unique=True)

    op.create_table(
        "invite_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("animal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("max_uses", sa.Integer(), server_default="1", nullable=False),
        sa.Column("use_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["animal_id"], ["animals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_invite_tokens_owner_id", "invite_tokens", ["owner_id"])
    op.create_index("ix_invite_tokens_token", "invite_tokens", ["token"])

    op.add_column(
        "friend_invites",
        sa.Column("invite_token_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "friend_invites",
        sa.Column("owner_confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "friend_invites",
        sa.Column("guardian_approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_friend_invites_invite_token_id",
        "friend_invites",
        "invite_tokens",
        ["invite_token_id"],
        ["id"],
    )

    op.execute("ALTER TYPE friend_invite_status RENAME TO friend_invite_status_old")
    new_status = postgresql.ENUM(
        "pending_owner_confirm",
        "pending_guardian",
        "active",
        "declined",
        "revoked",
        name="friend_invite_status",
        create_type=True,
    )
    new_status.create(bind, checkfirst=True)
    op.execute("ALTER TABLE friend_invites ALTER COLUMN status DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE friend_invites
        ALTER COLUMN status TYPE friend_invite_status
        USING (
            CASE status::text
                WHEN 'pending' THEN 'pending_owner_confirm'
                WHEN 'accepted' THEN 'active'
                WHEN 'cancelled' THEN 'revoked'
                WHEN 'declined' THEN 'declined'
                ELSE 'pending_owner_confirm'
            END
        )::friend_invite_status
        """
    )
    op.execute(
        "ALTER TABLE friend_invites ALTER COLUMN status SET DEFAULT 'pending_owner_confirm'"
    )
    op.execute("DROP TYPE friend_invite_status_old")


def downgrade() -> None:
    op.execute("ALTER TYPE friend_invite_status RENAME TO friend_invite_status_old")
    old_status = postgresql.ENUM(
        "pending", "accepted", "declined", "cancelled", name="friend_invite_status"
    )
    old_status.create(op.get_bind(), checkfirst=True)
    op.execute(
        """
        ALTER TABLE friend_invites
        ALTER COLUMN status TYPE friend_invite_status
        USING (
            CASE status::text
                WHEN 'pending_owner_confirm' THEN 'pending'
                WHEN 'pending_guardian' THEN 'pending'
                WHEN 'active' THEN 'accepted'
                WHEN 'revoked' THEN 'cancelled'
                ELSE 'declined'
            END
        )::friend_invite_status
        """
    )
    op.execute("DROP TYPE friend_invite_status_old")

    op.drop_constraint("fk_friend_invites_invite_token_id", "friend_invites", type_="foreignkey")
    op.drop_column("friend_invites", "guardian_approved_at")
    op.drop_column("friend_invites", "owner_confirmed_at")
    op.drop_column("friend_invites", "invite_token_id")

    op.drop_index("ix_invite_tokens_token", table_name="invite_tokens")
    op.drop_index("ix_invite_tokens_owner_id", table_name="invite_tokens")
    op.drop_table("invite_tokens")

    op.drop_index("ix_listings_slug", table_name="listings")
    op.drop_column("listings", "public_lng")
    op.drop_column("listings", "public_lat")
    op.drop_column("listings", "display_location")
    op.drop_column("listings", "slug")
