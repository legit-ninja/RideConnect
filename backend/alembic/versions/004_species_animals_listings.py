"""species animals listings

Revision ID: 004_species_animals_listings
Revises: 003_admin_audit_log
Create Date: 2026-07-01

"""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_species_animals_listings"
down_revision: Union[str, None] = "003_admin_audit_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

activity_type = postgresql.ENUM(
    "lesson",
    "lease",
    "trail_ride",
    "day_rental",
    name="activity_type",
    create_type=True,
)

SPECIES_SEED = [
    ("horse", True),
    ("camel", False),
    ("elephant", False),
]


def upgrade() -> None:
    bind = op.get_bind()
    activity_type.create(bind, checkfirst=True)

    op.create_table(
        "species",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("active_in_ui", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    species_table = sa.table(
        "species",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("active_in_ui", sa.Boolean()),
    )
    op.bulk_insert(
        species_table,
        [
            {"id": uuid.uuid4(), "name": name, "active_in_ui": active}
            for name, active in SPECIES_SEED
        ],
    )

    op.create_table(
        "animals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("species_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("breed", sa.String(length=128), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("address", sa.String(length=512), nullable=False),
        sa.Column("photo_urls", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["species_id"], ["species.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_animals_owner_id", "animals", ["owner_id"], unique=False)
    op.create_index("ix_animals_species_id", "animals", ["species_id"], unique=False)

    op.create_table(
        "listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("animal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "activity_type",
            postgresql.ENUM(
                "lesson",
                "lease",
                "trail_ride",
                "day_rental",
                name="activity_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("availability", sa.Text(), nullable=True),
        sa.Column(
            "friend_only_allowed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["animal_id"], ["animals.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listings_animal_id", "listings", ["animal_id"], unique=False)
    op.create_index("ix_listings_owner_id", "listings", ["owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_listings_owner_id", table_name="listings")
    op.drop_index("ix_listings_animal_id", table_name="listings")
    op.drop_table("listings")
    op.drop_index("ix_animals_species_id", table_name="animals")
    op.drop_index("ix_animals_owner_id", table_name="animals")
    op.drop_table("animals")
    op.drop_table("species")
    activity_type.drop(op.get_bind(), checkfirst=True)
