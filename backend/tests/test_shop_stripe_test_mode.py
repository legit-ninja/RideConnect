import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.shop import (
    FulfillmentType,
    ShopOrder,
    ShopOrderStatus,
    ShopPaymentStatus,
)
from tests.test_shop_payments import (
    _add_to_cart,
    _clear_stripe,
    _shop_fixture,
)
from tests.conftest import auth_header


def _production_stripe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    settings.environment = "production"
    settings.shop_dev_fake_payments = False


def test_shop_config_reports_test_mode_for_test_key(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = "whsec_supersecret"
    settings.stripe_publishable_key = ""

    response = client.get("/shop/config")
    assert response.status_code == 200
    body = response.json()
    assert body["stripe_test_mode"] is True
    assert body["payments_enabled"] is True
    raw = response.text
    assert "whsec" not in raw
    assert "sk_test" not in raw


def test_shop_config_hides_test_mode_for_live_key(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings.stripe_secret_key = "sk_live_fake"
    settings.stripe_publishable_key = "pk_live_fake"
    settings.stripe_webhook_secret = "whsec_live"

    response = client.get("/shop/config")
    assert response.status_code == 200
    body = response.json()
    assert body["stripe_test_mode"] is False
    raw = response.text.lower()
    assert "whsec" not in raw
    assert "sk_live" not in raw


def test_checkout_with_test_key_in_production_creates_session(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _production_stripe(monkeypatch)
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = "whsec_test"
    buyer, product = _shop_fixture(db_session)
    _add_to_cart(db_session, buyer.id, product)

    import stripe

    class FakeSession:
        url = "https://checkout.stripe.test/session"
        id = "cs_test_123"

    monkeypatch.setattr(
        stripe.checkout.Session,
        "create",
        lambda **_kwargs: FakeSession(),
    )

    response = client.post(
        "/shop/checkout",
        json={"fulfillment_type": FulfillmentType.PICKUP.value},
        headers=auth_header(buyer),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == ShopOrderStatus.PENDING_PAYMENT.value
    assert payload["checkout_url"] == FakeSession.url

    order = db_session.get(ShopOrder, uuid.UUID(payload["order_id"]))
    assert order is not None
    assert order.status == ShopOrderStatus.PENDING_PAYMENT
    paid_count = db_session.scalar(
        select(func.count())
        .select_from(ShopOrder)
        .where(ShopOrder.status == ShopOrderStatus.PAID)
    )
    assert int(paid_count or 0) == 0


def test_webhook_with_test_secret_in_production_marks_paid(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.models.shop import ShopOrderItem, ShopPayment

    _production_stripe(monkeypatch)
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = "whsec_test"

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

    import stripe

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "payment_status": "paid",
                "metadata": {"order_id": str(order.id)},
                "amount_total": 500,
                "currency": "usd",
                "payment_intent": "pi_test_prod",
            }
        },
    }
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *_a, **_k: event)

    response = client.post(
        "/shop/webhooks/stripe",
        content=json.dumps(event).encode(),
        headers={"stripe-signature": "sig"},
    )
    assert response.status_code == 200
    db_session.refresh(order)
    assert order.status == ShopOrderStatus.PAID
    assert order.payment is not None
    assert order.payment.status == ShopPaymentStatus.PAID


def test_dev_fake_payments_refused_in_production(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _production_stripe(monkeypatch)
    settings.shop_dev_fake_payments = True
    _clear_stripe(monkeypatch, key="", secret="")
    buyer, product = _shop_fixture(db_session)
    _add_to_cart(db_session, buyer.id, product)

    response = client.post(
        "/shop/checkout",
        json={"fulfillment_type": FulfillmentType.PICKUP.value},
        headers=auth_header(buyer),
    )
    assert response.status_code == 503
