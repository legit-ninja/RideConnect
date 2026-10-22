import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from sqlalchemy import func, select

from app.models.shop import (
    FulfillmentType,
    Product,
    ShopCart,
    ShopCartItem,
    ShopCategory,
    ShopOrder,
    ShopOrderItem,
    ShopOrderStatus,
    ShopPayment,
    ShopPaymentStatus,
)
from app.models.vendor_profile import VendorProfile, VendorStatus
from tests.conftest import auth_header, create_user


def _shop_fixture(db: Session) -> tuple:
    vendor = create_user(db, email="vendor-pay@test.com")
    vendor.is_vendor = True
    buyer = create_user(db, email="buyer-pay@test.com")
    category = ShopCategory(slug="food", name="Food", sort_order=1, active=True)
    db.add(category)
    db.flush()
    profile = VendorProfile(
        user_id=vendor.id, display_name="Vendor", status=VendorStatus.APPROVED
    )
    db.add(profile)
    db.flush()
    product = Product(
        vendor_profile_id=profile.id,
        category_id=category.id,
        sku="PAY-SKU-1",
        name="Hay",
        price_cents=500,
        stock_qty=10,
        active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return buyer, product


def _add_to_cart(db: Session, buyer_id: uuid.UUID, product: Product, qty: int = 1) -> None:
    cart = ShopCart(user_id=buyer_id)
    db.add(cart)
    db.flush()
    db.add(ShopCartItem(cart_id=cart.id, product_id=product.id, qty=qty))
    db.commit()


def _clear_stripe(monkeypatch: pytest.MonkeyPatch, key: str = "", secret: str = "") -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", key)
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", secret)
    settings.stripe_secret_key = key
    settings.stripe_webhook_secret = secret
    settings.shop_dev_fake_payments = False


@pytest.mark.parametrize("stripe_key", ["", "  "])
def test_checkout_without_stripe_key_returns_503_and_keeps_stock(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    stripe_key: str,
) -> None:
    _clear_stripe(monkeypatch, key=stripe_key, secret="")
    buyer, product = _shop_fixture(db_session)
    _add_to_cart(db_session, buyer.id, product)
    stock_before = product.stock_qty
    pending_before = db_session.scalar(
        select(func.count())
        .select_from(ShopOrder)
        .where(ShopOrder.status == ShopOrderStatus.PENDING_PAYMENT)
    )

    response = client.post(
        "/shop/checkout",
        json={"fulfillment_type": FulfillmentType.PICKUP.value},
        headers=auth_header(buyer),
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()

    db_session.refresh(product)
    assert product.stock_qty == stock_before
    pending_after = db_session.scalar(
        select(func.count())
        .select_from(ShopOrder)
        .where(ShopOrder.status == ShopOrderStatus.PENDING_PAYMENT)
    )
    assert int(pending_after or 0) == int(pending_before or 0)
    paid_orders = db_session.scalar(
        select(func.count())
        .select_from(ShopOrder)
        .where(ShopOrder.status == ShopOrderStatus.PAID)
    )
    assert int(paid_orders or 0) == 0


@pytest.mark.parametrize("webhook_secret", ["", "  "])
def test_webhook_with_empty_secret_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, webhook_secret: str
) -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", webhook_secret)
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = webhook_secret

    response = client.post(
        "/shop/webhooks/stripe",
        content=b"{}",
        headers={"stripe-signature": "sig"},
    )
    assert response.status_code == 503


def test_webhook_without_secret_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "")
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = ""

    response = client.post(
        "/shop/webhooks/stripe",
        content=b"{}",
        headers={"stripe-signature": "sig"},
    )
    assert response.status_code == 503


def test_webhook_bad_signature_returns_400(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = "whsec_test"

    import stripe

    def fail(*_args, **_kwargs):
        raise ValueError("invalid signature")

    monkeypatch.setattr(stripe.Webhook, "construct_event", fail)

    response = client.post(
        "/shop/webhooks/stripe",
        content=b"{}",
        headers={"stripe-signature": "sig"},
    )
    assert response.status_code == 400


def test_webhook_unpaid_session_does_not_mark_paid(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer, product = _shop_fixture(db_session)
    order = ShopOrder(
        buyer_id=buyer.id,
        status=ShopOrderStatus.PENDING_PAYMENT,
        fulfillment_type=FulfillmentType.PICKUP,
        subtotal_cents=500,
        tax_cents=0,
        shipping_cents=0,
        total_cents=500,
    )
    db_session.add(order)
    db_session.flush()
    db_session.add(
        ShopOrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            unit_price_cents=500,
            qty=1,
        )
    )
    db_session.commit()

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = "whsec_test"

    import stripe

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "payment_status": "unpaid",
                "metadata": {"order_id": str(order.id)},
                "amount_total": 500,
                "currency": "usd",
            }
        },
    }

    monkeypatch.setattr(
        stripe.Webhook,
        "construct_event",
        lambda *_a, **_k: event,
    )

    response = client.post(
        "/shop/webhooks/stripe",
        content=json.dumps(event).encode(),
        headers={"stripe-signature": "sig"},
    )
    assert response.status_code == 200
    db_session.refresh(order)
    assert order.status == ShopOrderStatus.PENDING_PAYMENT


def test_webhook_wrong_amount_returns_400(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer, product = _shop_fixture(db_session)
    order = ShopOrder(
        buyer_id=buyer.id,
        status=ShopOrderStatus.PENDING_PAYMENT,
        fulfillment_type=FulfillmentType.PICKUP,
        subtotal_cents=500,
        tax_cents=0,
        shipping_cents=0,
        total_cents=500,
        currency="USD",
    )
    db_session.add(order)
    db_session.commit()

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = "whsec_test"

    import stripe

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "payment_status": "paid",
                "metadata": {"order_id": str(order.id)},
                "amount_total": 999,
                "currency": "usd",
            }
        },
    }
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *_a, **_k: event)

    response = client.post(
        "/shop/webhooks/stripe",
        content=b"{}",
        headers={"stripe-signature": "sig"},
    )
    assert response.status_code == 400
    db_session.refresh(order)
    assert order.status == ShopOrderStatus.PENDING_PAYMENT


def test_webhook_malformed_order_id_returns_400(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = "whsec_test"

    import stripe

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "payment_status": "paid",
                "metadata": {"order_id": "not-a-uuid"},
                "amount_total": 100,
                "currency": "usd",
            }
        },
    }
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *_a, **_k: event)

    response = client.post(
        "/shop/webhooks/stripe",
        content=b"{}",
        headers={"stripe-signature": "sig"},
    )
    assert response.status_code == 400


def test_webhook_unknown_order_returns_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = "whsec_test"

    import stripe

    missing_id = str(uuid.uuid4())
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "payment_status": "paid",
                "metadata": {"order_id": missing_id},
                "amount_total": 100,
                "currency": "usd",
            }
        },
    }
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *_a, **_k: event)

    response = client.post(
        "/shop/webhooks/stripe",
        content=b"{}",
        headers={"stripe-signature": "sig"},
    )
    assert response.status_code == 404


def test_webhook_paid_after_cancel_records_payment(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer, product = _shop_fixture(db_session)
    order = ShopOrder(
        buyer_id=buyer.id,
        status=ShopOrderStatus.CANCELLED,
        fulfillment_type=FulfillmentType.PICKUP,
        subtotal_cents=500,
        tax_cents=0,
        shipping_cents=0,
        total_cents=500,
        currency="USD",
    )
    db_session.add(order)
    db_session.flush()
    db_session.add(
        ShopOrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            unit_price_cents=500,
            qty=1,
        )
    )
    db_session.add(
        ShopPayment(order_id=order.id, amount_cents=500, status=ShopPaymentStatus.PENDING)
    )
    db_session.commit()

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = "whsec_test"

    import stripe

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "payment_status": "paid",
                "metadata": {"order_id": str(order.id)},
                "amount_total": 500,
                "currency": "usd",
                "payment_intent": "pi_test",
            }
        },
    }
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *_a, **_k: event)

    response = client.post(
        "/shop/webhooks/stripe",
        content=b"{}",
        headers={"stripe-signature": "sig"},
    )
    assert response.status_code == 200
    db_session.refresh(order)
    assert order.status == ShopOrderStatus.CANCELLED
    assert order.payment is not None
    assert order.payment.status == ShopPaymentStatus.PAID
    db_session.refresh(product)
    assert product.stock_qty == 10


def test_webhook_async_payment_succeeded_marks_paid(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer, product = _shop_fixture(db_session)
    order = ShopOrder(
        buyer_id=buyer.id,
        status=ShopOrderStatus.PENDING_PAYMENT,
        fulfillment_type=FulfillmentType.PICKUP,
        subtotal_cents=500,
        tax_cents=0,
        shipping_cents=0,
        total_cents=500,
        currency="USD",
    )
    db_session.add(order)
    db_session.flush()
    db_session.add(
        ShopOrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            unit_price_cents=500,
            qty=1,
        )
    )
    db_session.add(
        ShopPayment(order_id=order.id, amount_cents=500, status=ShopPaymentStatus.PENDING)
    )
    db_session.commit()

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = "whsec_test"

    import stripe

    event = {
        "type": "checkout.session.async_payment_succeeded",
        "data": {
            "object": {
                "payment_status": "paid",
                "metadata": {"order_id": str(order.id)},
                "amount_total": 500,
                "currency": "usd",
                "payment_intent": "pi_async",
            }
        },
    }
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *_a, **_k: event)

    response = client.post(
        "/shop/webhooks/stripe",
        content=b"{}",
        headers={"stripe-signature": "sig"},
    )
    assert response.status_code == 200
    db_session.refresh(order)
    assert order.status == ShopOrderStatus.PAID
