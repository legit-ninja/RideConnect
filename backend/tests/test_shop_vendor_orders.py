import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.shop import (
    FulfillmentType,
    Product,
    ShopCategory,
    ShopOrder,
    ShopOrderItem,
    ShopOrderStatus,
    ShopPayment,
    ShopPaymentStatus,
)
from app.models.vendor_profile import VendorProfile, VendorStatus
from tests.conftest import auth_header, create_user


def _vendor_with_product(
    db: Session, email: str, sku: str, profile_name: str
) -> tuple:
    user = create_user(db, email=email)
    user.is_vendor = True
    category = db.query(ShopCategory).first()
    if category is None:
        category = ShopCategory(slug="gear", name="Gear", sort_order=1, active=True)
        db.add(category)
        db.flush()
    profile = VendorProfile(
        user_id=user.id, display_name=profile_name, status=VendorStatus.APPROVED
    )
    db.add(profile)
    db.flush()
    product = Product(
        vendor_profile_id=profile.id,
        category_id=category.id,
        sku=sku,
        name=f"Product {sku}",
        price_cents=1000,
        stock_qty=5,
        active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(user)
    db.refresh(product)
    return user, product


def _paid_order(
    db: Session, buyer_id: uuid.UUID, items: list[tuple[Product, int]]
) -> ShopOrder:
    subtotal = sum(p.price_cents * qty for p, qty in items)
    order = ShopOrder(
        buyer_id=buyer_id,
        status=ShopOrderStatus.PAID,
        fulfillment_type=FulfillmentType.PICKUP,
        subtotal_cents=subtotal,
        tax_cents=0,
        shipping_cents=0,
        total_cents=subtotal,
    )
    db.add(order)
    db.flush()
    for product, qty in items:
        db.add(
            ShopOrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                unit_price_cents=product.price_cents,
                qty=qty,
            )
        )
    db.add(
        ShopPayment(
            order_id=order.id, amount_cents=subtotal, status=ShopPaymentStatus.PAID
        )
    )
    db.commit()
    db.refresh(order)
    return order


def test_vendor_cannot_fulfill_order_with_other_vendor_items(
    client: TestClient, db_session: Session
) -> None:
    buyer = create_user(db_session, email="buyer-vendor@test.com")
    vendor_a, product_a = _vendor_with_product(
        db_session, "vendor-a@test.com", "SKU-A", "A"
    )
    _, product_b = _vendor_with_product(
        db_session, "vendor-b@test.com", "SKU-B", "B"
    )
    order = _paid_order(db_session, buyer.id, [(product_a, 1), (product_b, 1)])

    response = client.patch(
        f"/shop/vendor/orders/{order.id}",
        json={"status": ShopOrderStatus.FULFILLING.value},
        headers=auth_header(vendor_a),
    )
    assert response.status_code == 403


def test_invalid_transition_pending_to_shipped_returns_409(
    client: TestClient, db_session: Session
) -> None:
    buyer = create_user(db_session, email="buyer-trans@test.com")
    vendor, product = _vendor_with_product(
        db_session, "vendor-trans@test.com", "SKU-T", "T"
    )
    order = ShopOrder(
        buyer_id=buyer.id,
        status=ShopOrderStatus.PENDING_PAYMENT,
        fulfillment_type=FulfillmentType.PICKUP,
        subtotal_cents=1000,
        tax_cents=0,
        shipping_cents=0,
        total_cents=1000,
    )
    db_session.add(order)
    db_session.flush()
    db_session.add(
        ShopOrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            unit_price_cents=1000,
            qty=1,
        )
    )
    db_session.commit()

    response = client.patch(
        f"/shop/vendor/orders/{order.id}",
        json={"status": ShopOrderStatus.SHIPPED.value},
        headers=auth_header(vendor),
    )
    assert response.status_code == 409


def test_invalid_transition_refunded_to_fulfilling_returns_409(
    client: TestClient, db_session: Session
) -> None:
    buyer = create_user(db_session, email="buyer-ref@test.com")
    vendor, product = _vendor_with_product(
        db_session, "vendor-ref@test.com", "SKU-R", "R"
    )
    order = ShopOrder(
        buyer_id=buyer.id,
        status=ShopOrderStatus.REFUNDED,
        fulfillment_type=FulfillmentType.PICKUP,
        subtotal_cents=1000,
        tax_cents=0,
        shipping_cents=0,
        total_cents=1000,
    )
    db_session.add(order)
    db_session.flush()
    db_session.add(
        ShopOrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            unit_price_cents=1000,
            qty=1,
        )
    )
    db_session.commit()

    response = client.patch(
        f"/shop/vendor/orders/{order.id}",
        json={"status": ShopOrderStatus.FULFILLING.value},
        headers=auth_header(vendor),
    )
    assert response.status_code == 409


def test_vendor_cannot_cancel_while_payment_pending(
    client: TestClient, db_session: Session
) -> None:
    buyer = create_user(db_session, email="buyer-cancel@test.com")
    vendor, product = _vendor_with_product(
        db_session, "vendor-cancel@test.com", "SKU-C", "C"
    )
    order = ShopOrder(
        buyer_id=buyer.id,
        status=ShopOrderStatus.PENDING_PAYMENT,
        fulfillment_type=FulfillmentType.PICKUP,
        subtotal_cents=1000,
        tax_cents=0,
        shipping_cents=0,
        total_cents=1000,
    )
    db_session.add(order)
    db_session.flush()
    db_session.add(
        ShopOrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            unit_price_cents=1000,
            qty=1,
        )
    )
    db_session.commit()

    response = client.patch(
        f"/shop/vendor/orders/{order.id}",
        json={"status": ShopOrderStatus.CANCELLED.value},
        headers=auth_header(vendor),
    )
    assert response.status_code == 409
