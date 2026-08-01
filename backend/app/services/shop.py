from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.shop import (
    FulfillmentType,
    Product,
    ProductSpecies,
    ShopCart,
    ShopOrder,
    ShopOrderEvent,
    ShopOrderStatus,
    ShopPaymentStatus,
)
from app.models.user import User
from app.models.vendor_profile import VendorProfile, VendorStatus
from app.schemas.shop import (
    CartItemResponse,
    CartResponse,
    OrderEventResponse,
    OrderItemResponse,
    OrderResponse,
    ProductImageResponse,
    ProductResponse,
    ProductSpeciesTag,
)
from app.services.storage import get_public_url


def get_or_create_cart(db: Session, user_id: UUID) -> ShopCart:
    cart = db.scalar(select(ShopCart).where(ShopCart.user_id == user_id))
    if cart is None:
        cart = ShopCart(user_id=user_id)
        db.add(cart)
        db.flush()
    return cart


def get_vendor_profile_for_user(db: Session, user: User) -> VendorProfile | None:
    return db.scalar(select(VendorProfile).where(VendorProfile.user_id == user.id))


def ensure_platform_vendor(db: Session, user: User) -> VendorProfile:
    """Admin/platform seller: approved vendor profile for catalog management."""
    profile = get_vendor_profile_for_user(db, user)
    if profile is None:
        profile = VendorProfile(
            user_id=user.id,
            display_name="Phantom Equestrian",
            status=VendorStatus.APPROVED,
        )
        db.add(profile)
        user.is_vendor = True
        db.flush()
    elif profile.status != VendorStatus.APPROVED:
        profile.status = VendorStatus.APPROVED
        user.is_vendor = True
        db.flush()
    return profile


def resolve_vendor_profile_for_writes(db: Session, user: User) -> VendorProfile:
    if user.is_admin:
        return ensure_platform_vendor(db, user)
    profile = get_vendor_profile_for_user(db, user)
    if profile is None or profile.status != VendorStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approved vendor profile required",
        )
    return profile


def product_to_response(product: Product) -> ProductResponse:
    images = sorted(product.images or [], key=lambda i: i.sort_order)
    species = []
    for tag in product.species_tags or []:
        if tag.species is not None:
            species.append(ProductSpeciesTag(id=tag.species.id, name=tag.species.name))
    return ProductResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        price_cents=product.price_cents,
        currency=product.currency,
        stock_qty=product.stock_qty,
        active=product.active,
        category_id=product.category_id,
        category_slug=product.category.slug if product.category else None,
        category_name=product.category.name if product.category else None,
        vendor_profile_id=product.vendor_profile_id,
        species=species,
        images=[
            ProductImageResponse(
                id=img.id, url=get_public_url(img.storage_key), sort_order=img.sort_order
            )
            for img in images
        ],
        created_at=product.created_at,
    )


def load_product(db: Session, product_id: UUID) -> Product | None:
    return db.scalar(
        select(Product)
        .options(
            joinedload(Product.category),
            joinedload(Product.images),
            joinedload(Product.species_tags).joinedload(ProductSpecies.species),
        )
        .where(Product.id == product_id)
    )


def cart_to_response(db: Session, cart: ShopCart) -> CartResponse:
    items_out: list[CartItemResponse] = []
    subtotal = 0
    for item in cart.items:
        product = item.product
        if product is None:
            product = db.get(Product, item.product_id)
        if product is None:
            continue
        line = product.price_cents * item.qty
        subtotal += line
        items_out.append(
            CartItemResponse(
                id=item.id,
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                unit_price_cents=product.price_cents,
                qty=item.qty,
                line_total_cents=line,
                stock_qty=product.stock_qty,
            )
        )
    return CartResponse(id=cart.id, items=items_out, subtotal_cents=subtotal)


def order_to_response(order: ShopOrder) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        status=order.status,
        fulfillment_type=order.fulfillment_type,
        ship_name=order.ship_name,
        ship_line1=order.ship_line1,
        ship_line2=order.ship_line2,
        ship_city=order.ship_city,
        ship_state=order.ship_state,
        ship_postal=order.ship_postal,
        ship_country=order.ship_country,
        subtotal_cents=order.subtotal_cents,
        tax_cents=order.tax_cents,
        shipping_cents=order.shipping_cents,
        total_cents=order.total_cents,
        currency=order.currency,
        items=[
            OrderItemResponse(
                id=i.id,
                product_id=i.product_id,
                product_name=i.product_name,
                product_sku=i.product_sku,
                unit_price_cents=i.unit_price_cents,
                qty=i.qty,
            )
            for i in order.items
        ],
        events=[
            OrderEventResponse(
                id=e.id,
                from_status=e.from_status,
                to_status=e.to_status,
                note=e.note,
                created_at=e.created_at,
            )
            for e in sorted(order.events, key=lambda x: x.created_at)
        ],
        payment_status=order.payment.status if order.payment else None,
        created_at=order.created_at,
    )


def append_order_event(
    db: Session,
    order: ShopOrder,
    *,
    to_status: ShopOrderStatus,
    actor_id: UUID | None,
    from_status: ShopOrderStatus | None = None,
    note: str | None = None,
) -> None:
    db.add(
        ShopOrderEvent(
            order_id=order.id,
            actor_id=actor_id,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value,
            note=note,
        )
    )


def validate_checkout_address(fulfillment: FulfillmentType, payload: object) -> None:
    if fulfillment != FulfillmentType.SHIP:
        return
    required = ["ship_name", "ship_line1", "ship_city", "ship_state", "ship_postal"]
    for field in required:
        if not getattr(payload, field, None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field} is required for shipping",
            )


def mark_order_paid(db: Session, order: ShopOrder, *, payment_intent_id: str | None) -> None:
    if order.status != ShopOrderStatus.PENDING_PAYMENT:
        return
    prev = order.status
    order.status = ShopOrderStatus.PAID
    if order.payment:
        order.payment.status = ShopPaymentStatus.PAID
        if payment_intent_id:
            order.payment.stripe_payment_intent_id = payment_intent_id
    for item in order.items:
        if item.product_id is None:
            continue
        product = db.get(Product, item.product_id)
        if product is not None:
            product.stock_qty = max(0, product.stock_qty - item.qty)
    append_order_event(
        db, order, to_status=ShopOrderStatus.PAID, actor_id=None, from_status=prev, note="stripe"
    )


def create_stripe_checkout_session(order: ShopOrder) -> tuple[str | None, str | None]:
    """Returns (checkout_url, session_id). Both None when Stripe is not configured."""
    if not settings.stripe_secret_key:
        return None, None
    import stripe

    stripe.api_key = settings.stripe_secret_key
    line_items = [
        {
            "price_data": {
                "currency": order.currency.lower(),
                "unit_amount": item.unit_price_cents,
                "product_data": {"name": item.product_name},
            },
            "quantity": item.qty,
        }
        for item in order.items
    ]
    if order.shipping_cents > 0:
        line_items.append(
            {
                "price_data": {
                    "currency": order.currency.lower(),
                    "unit_amount": order.shipping_cents,
                    "product_data": {"name": "Shipping"},
                },
                "quantity": 1,
            }
        )
    success = f"{settings.frontend_base_url.rstrip('/')}/shop/orders/{order.id}?paid=1"
    cancel = f"{settings.frontend_base_url.rstrip('/')}/shop/checkout?cancelled=1"
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url=success,
        cancel_url=cancel,
        client_reference_id=str(order.id),
        metadata={"order_id": str(order.id), "business_unit": "shop"},
    )
    return session.url, session.id

