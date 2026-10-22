"""Shop catalog, vendor profiles, funnel events.

Revision ID: 020_shop_vendor_funnel
Revises: 019_family_registration
Create Date: 2026-08-01

users.is_vendor moved to 021_users_is_vendor (idempotent) so prod DBs that already
applied 020 with the column can upgrade cleanly.
"""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "020_shop_vendor_funnel"
down_revision: Union[str, None] = "019_family_registration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False: upgrade() creates these explicitly with checkfirst=True; letting
# op.create_table create them again fails on Postgres ("type already exists").
vendor_status = postgresql.ENUM(
    "pending", "approved", "suspended", name="vendor_status", create_type=False
)
shop_order_status = postgresql.ENUM(
    "pending_payment",
    "paid",
    "fulfilling",
    "shipped",
    "picked_up",
    "cancelled",
    "refunded",
    name="shop_order_status",
    create_type=False,
)
fulfillment_type = postgresql.ENUM(
    "ship", "pickup", name="fulfillment_type", create_type=False
)
shop_payment_status = postgresql.ENUM(
    "pending", "paid", "failed", "refunded", name="shop_payment_status", create_type=False
)
business_unit = postgresql.ENUM(
    "rides", "shop", name="business_unit", create_type=False
)

CATEGORY_SEED = [
    ("food", "Food", 10, True),
    ("supplements", "Supplements", 20, True),
    ("tack_gear", "Tack & Gear", 30, True),
    ("grooming", "Grooming", 40, True),
    ("health", "Health", 50, True),
    ("habitat", "Habitat", 60, False),
]

SPECIES_SEED = [
    ("dog", True),
    ("bird", False),
    ("fish", False),
]


def upgrade() -> None:
    bind = op.get_bind()
    vendor_status.create(bind, checkfirst=True)
    shop_order_status.create(bind, checkfirst=True)
    fulfillment_type.create(bind, checkfirst=True)
    shop_payment_status.create(bind, checkfirst=True)
    business_unit.create(bind, checkfirst=True)

    species_table = sa.table(
        "species",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("active_in_ui", sa.Boolean),
    )
    for name, active in SPECIES_SEED:
        exists = bind.execute(
            sa.text("SELECT 1 FROM species WHERE name = :name"), {"name": name}
        ).first()
        if not exists:
            op.bulk_insert(
                species_table,
                [{"id": uuid.uuid4(), "name": name, "active_in_ui": active}],
            )

    op.create_table(
        "vendor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("status", vendor_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_vendor_profiles_user_id", "vendor_profiles", ["user_id"])

    op.create_table(
        "shop_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_shop_categories_slug", "shop_categories", ["slug"])

    categories_table = sa.table(
        "shop_categories",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("sort_order", sa.SmallInteger),
        sa.column("active", sa.Boolean),
    )
    op.bulk_insert(
        categories_table,
        [
            {
                "id": uuid.uuid4(),
                "slug": slug,
                "name": name,
                "sort_order": sort,
                "active": active,
            }
            for slug, name, sort, active in CATEGORY_SEED
        ],
    )

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vendor_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("stock_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vendor_profile_id"], ["vendor_profiles.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["shop_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )
    op.create_index("ix_products_vendor_profile_id", "products", ["vendor_profile_id"])
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_sku", "products", ["sku"])

    op.create_table(
        "product_species",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("species_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["species_id"], ["species.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "species_id", name="uq_product_species"),
    )
    op.create_index("ix_product_species_species_id", "product_species", ["species_id"])

    op.create_table(
        "product_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"])

    op.create_table(
        "shop_carts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_shop_carts_user_id", "shop_carts", ["user_id"])

    op.create_table(
        "shop_cart_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cart_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cart_id"], ["shop_carts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
    )

    op.create_table(
        "shop_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", shop_order_status, nullable=False),
        sa.Column("fulfillment_type", fulfillment_type, nullable=False),
        sa.Column("ship_name", sa.String(length=200), nullable=True),
        sa.Column("ship_line1", sa.String(length=200), nullable=True),
        sa.Column("ship_line2", sa.String(length=200), nullable=True),
        sa.Column("ship_city", sa.String(length=100), nullable=True),
        sa.Column("ship_state", sa.String(length=64), nullable=True),
        sa.Column("ship_postal", sa.String(length=32), nullable=True),
        sa.Column("ship_country", sa.String(length=2), nullable=True),
        sa.Column("subtotal_cents", sa.Integer(), nullable=False),
        sa.Column("tax_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shipping_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shop_orders_buyer_id", "shop_orders", ["buyer_id"])

    op.create_table(
        "shop_order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("product_sku", sa.String(length=64), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["shop_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shop_order_items_order_id", "shop_order_items", ["order_id"])

    op.create_table(
        "shop_order_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["shop_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shop_order_events_order_id", "shop_order_events", ["order_id"])

    op.create_table(
        "shop_payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("status", shop_payment_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["shop_orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )
    op.create_index(
        "ix_shop_payments_stripe_checkout_session_id",
        "shop_payments",
        ["stripe_checkout_session_id"],
    )
    op.create_index(
        "ix_shop_payments_stripe_payment_intent_id",
        "shop_payments",
        ["stripe_payment_intent_id"],
    )

    op.create_table(
        "funnel_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_unit", business_unit, nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("anon_id", sa.String(length=64), nullable=True),
        sa.Column("src", sa.String(length=64), nullable=True),
        sa.Column("ref", sa.String(length=128), nullable=True),
        sa.Column("path", sa.String(length=512), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_funnel_events_business_unit", "funnel_events", ["business_unit"])
    op.create_index("ix_funnel_events_stage", "funnel_events", ["stage"])
    op.create_index("ix_funnel_events_user_id", "funnel_events", ["user_id"])
    op.create_index("ix_funnel_events_anon_id", "funnel_events", ["anon_id"])
    op.create_index("ix_funnel_events_created_at", "funnel_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("funnel_events")
    op.drop_table("shop_payments")
    op.drop_table("shop_order_events")
    op.drop_table("shop_order_items")
    op.drop_table("shop_orders")
    op.drop_table("shop_cart_items")
    op.drop_table("shop_carts")
    op.drop_table("product_images")
    op.drop_table("product_species")
    op.drop_table("products")
    op.drop_table("shop_categories")
    op.drop_table("vendor_profiles")
    # is_vendor is dropped in 021_users_is_vendor downgrade, not here.

    bind = op.get_bind()
    business_unit.drop(bind, checkfirst=True)
    shop_payment_status.drop(bind, checkfirst=True)
    fulfillment_type.drop(bind, checkfirst=True)
    shop_order_status.drop(bind, checkfirst=True)
    vendor_status.drop(bind, checkfirst=True)
