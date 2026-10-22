from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.db import get_db
from app.dependencies import get_current_user, require_admin, require_vendor
from app.models.shop import (
    FulfillmentType,
    Product,
    ProductSpecies,
    ShopCart,
    ShopCartItem,
    ShopCategory,
    ShopOrder,
    ShopOrderItem,
    ShopOrderStatus,
    ShopPayment,
    ShopPaymentStatus,
)
from app.models.user import User
from app.models.vendor_profile import VendorProfile, VendorStatus
from app.schemas.shop import (
    CartAddRequest,
    CartResponse,
    CartUpdateItemRequest,
    CheckoutRequest,
    CheckoutResponse,
    OrderListResponse,
    OrderResponse,
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
    ShopCategoryResponse,
    VendorApplyRequest,
    VendorOrderFulfillRequest,
    VendorProfileResponse,
    VendorStatusUpdateRequest,
)
from app.services.shop import (
    append_order_event,
    cart_to_response,
    create_stripe_checkout_session,
    get_or_create_cart,
    get_vendor_profile_for_user,
    load_product,
    mark_order_paid,
    order_to_response,
    product_to_response,
    resolve_vendor_profile_for_writes,
    validate_checkout_address,
)

router = APIRouter(prefix="/shop", tags=["shop"])

_VENDOR_FULFILL_STATUSES = {
    ShopOrderStatus.FULFILLING,
    ShopOrderStatus.SHIPPED,
    ShopOrderStatus.PICKED_UP,
    ShopOrderStatus.CANCELLED,
}


@router.get("/categories", response_model=list[ShopCategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    active_only: bool = Query(default=True),
) -> list[ShopCategory]:
    # Authz: public catalog metadata.
    stmt = select(ShopCategory).order_by(ShopCategory.sort_order, ShopCategory.name)
    if active_only:
        stmt = stmt.where(ShopCategory.active.is_(True))
    return list(db.scalars(stmt).all())


@router.get("/products", response_model=ProductListResponse)
def list_products(
    db: Session = Depends(get_db),
    category: str | None = Query(default=None, description="Category slug"),
    species_id: UUID | None = None,
    q: str | None = None,
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ProductListResponse:
    # Authz: public catalog of active products only.
    stmt = (
        select(Product)
        .options(
            joinedload(Product.category),
            joinedload(Product.images),
            joinedload(Product.species_tags).joinedload(ProductSpecies.species),
        )
        .where(Product.active.is_(True))
        .order_by(Product.created_at.desc())
    )
    if category:
        stmt = stmt.join(ShopCategory).where(ShopCategory.slug == category)
    if species_id is not None:
        stmt = stmt.join(ProductSpecies).where(ProductSpecies.species_id == species_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Product.name.ilike(like), Product.description.ilike(like)))

    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = int(db.scalar(count_stmt) or 0)
    products = list(db.scalars(stmt.limit(limit).offset(offset)).unique().all())
    return ProductListResponse(
        items=[product_to_response(p) for p in products],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_db)) -> ProductResponse:
    # Authz: public product detail for active SKUs.
    product = load_product(db, product_id)
    if product is None or not product.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product_to_response(product)


@router.get("/cart", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    # Authz: buyer may read own cart (no KYC).
    cart = get_or_create_cart(db, current_user.id)
    cart = db.scalar(
        select(ShopCart)
        .options(joinedload(ShopCart.items).joinedload(ShopCartItem.product))
        .where(ShopCart.id == cart.id)
    )
    assert cart is not None
    db.commit()
    return cart_to_response(db, cart)


@router.post("/cart", response_model=CartResponse)
def add_to_cart(
    payload: CartAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    # Authz: authenticated buyer; shop purchase does not require verification.
    product = db.get(Product, payload.product_id)
    if product is None or not product.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.stock_qty < payload.qty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")

    cart = get_or_create_cart(db, current_user.id)
    existing = db.scalar(
        select(ShopCartItem).where(
            ShopCartItem.cart_id == cart.id,
            ShopCartItem.product_id == product.id,
        )
    )
    if existing:
        new_qty = existing.qty + payload.qty
        if product.stock_qty < new_qty:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
        existing.qty = new_qty
    else:
        db.add(ShopCartItem(cart_id=cart.id, product_id=product.id, qty=payload.qty))
    db.commit()
    return get_cart(db=db, current_user=current_user)


@router.patch("/cart/items/{item_id}", response_model=CartResponse)
def update_cart_item(
    item_id: UUID,
    payload: CartUpdateItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    # Authz: buyer may modify own cart lines only.
    cart = get_or_create_cart(db, current_user.id)
    item = db.scalar(
        select(ShopCartItem).where(ShopCartItem.id == item_id, ShopCartItem.cart_id == cart.id)
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    if payload.qty == 0:
        db.delete(item)
    else:
        product = db.get(Product, item.product_id)
        if product is None or product.stock_qty < payload.qty:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
        item.qty = payload.qty
    db.commit()
    return get_cart(db=db, current_user=current_user)


@router.post("/checkout", response_model=CheckoutResponse)
def checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CheckoutResponse:
    # Authz: authenticated buyer; KYC not required for shop checkout.
    validate_checkout_address(payload.fulfillment_type, payload)
    cart = db.scalar(
        select(ShopCart)
        .options(joinedload(ShopCart.items).joinedload(ShopCartItem.product))
        .where(ShopCart.user_id == current_user.id)
    )
    if cart is None or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    subtotal = 0
    order_items: list[ShopOrderItem] = []
    for item in cart.items:
        product = item.product
        if product is None or not product.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product unavailable: {item.product_id}",
            )
        if product.stock_qty < item.qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product.name}",
            )
        subtotal += product.price_cents * item.qty
        order_items.append(
            ShopOrderItem(
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                unit_price_cents=product.price_cents,
                qty=item.qty,
            )
        )

    shipping_cents = 0
    if payload.fulfillment_type == FulfillmentType.SHIP:
        shipping_cents = 799 if subtotal < 7500 else 0

    order = ShopOrder(
        buyer_id=current_user.id,
        status=ShopOrderStatus.PENDING_PAYMENT,
        fulfillment_type=payload.fulfillment_type,
        ship_name=payload.ship_name,
        ship_line1=payload.ship_line1,
        ship_line2=payload.ship_line2,
        ship_city=payload.ship_city,
        ship_state=payload.ship_state,
        ship_postal=payload.ship_postal,
        ship_country=payload.ship_country or "US",
        subtotal_cents=subtotal,
        tax_cents=0,
        shipping_cents=shipping_cents,
        total_cents=subtotal + shipping_cents,
    )
    db.add(order)
    db.flush()
    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)
    append_order_event(
        db,
        order,
        to_status=ShopOrderStatus.PENDING_PAYMENT,
        actor_id=current_user.id,
        note="checkout_created",
    )
    payment = ShopPayment(
        order_id=order.id,
        amount_cents=order.total_cents,
        status=ShopPaymentStatus.PENDING,
    )
    db.add(payment)
    db.flush()

    checkout_url, session_id = create_stripe_checkout_session(order)
    if session_id:
        payment.stripe_checkout_session_id = session_id
    elif not settings.stripe_secret_key:
        # Dev stub: mark paid immediately when Stripe keys are absent.
        mark_order_paid(db, order, payment_intent_id=None)
        checkout_url = f"{settings.frontend_base_url.rstrip('/')}/shop/orders/{order.id}?paid=1"

    for item in list(cart.items):
        db.delete(item)
    db.commit()
    db.refresh(order)
    return CheckoutResponse(
        order_id=order.id,
        checkout_url=checkout_url,
        status=order.status,
        total_cents=order.total_cents,
    )


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, bool]:
    # Authz: Stripe signature verification (or open in dev when secret unset — still no user auth).
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe not configured")

    import stripe

    stripe.api_key = settings.stripe_secret_key
    event = None
    if settings.stripe_webhook_secret:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig, settings.stripe_webhook_secret
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
            ) from exc
    else:
        import json

        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session.get("metadata", {}).get("order_id") or session.get(
            "client_reference_id"
        )
        if order_id:
            order = db.scalar(
                select(ShopOrder)
                .options(joinedload(ShopOrder.items), joinedload(ShopOrder.payment))
                .where(ShopOrder.id == UUID(order_id))
            )
            if order is not None:
                mark_order_paid(
                    db,
                    order,
                    payment_intent_id=session.get("payment_intent"),
                )
                db.commit()
    return {"ok": True}


@router.get("/orders", response_model=OrderListResponse)
def list_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderListResponse:
    # Authz: buyer sees own orders only.
    orders = list(
        db.scalars(
            select(ShopOrder)
            .options(
                joinedload(ShopOrder.items),
                joinedload(ShopOrder.events),
                joinedload(ShopOrder.payment),
            )
            .where(ShopOrder.buyer_id == current_user.id)
            .order_by(ShopOrder.created_at.desc())
        )
        .unique()
        .all()
    )
    return OrderListResponse(items=[order_to_response(o) for o in orders], total=len(orders))


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_my_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    # Authz: buyer or admin or vendor with SKUs on the order.
    order = db.scalar(
        select(ShopOrder)
        .options(
            joinedload(ShopOrder.items),
            joinedload(ShopOrder.events),
            joinedload(ShopOrder.payment),
        )
        .where(ShopOrder.id == order_id)
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.buyer_id != current_user.id and not current_user.is_admin:
        profile = get_vendor_profile_for_user(db, current_user)
        if profile is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        product_ids = [i.product_id for i in order.items if i.product_id]
        if product_ids:
            owned = db.scalar(
                select(func.count())
                .select_from(Product)
                .where(
                    Product.id.in_(product_ids),
                    Product.vendor_profile_id == profile.id,
                )
            )
            if not owned:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return order_to_response(order)


@router.get("/vendor/products", response_model=ProductListResponse)
def vendor_list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ProductListResponse:
    # Authz: require_vendor — own products (admin sees all via platform vendor + all).
    profile = resolve_vendor_profile_for_writes(db, current_user)
    stmt = (
        select(Product)
        .options(
            joinedload(Product.category),
            joinedload(Product.images),
            joinedload(Product.species_tags).joinedload(ProductSpecies.species),
        )
        .order_by(Product.created_at.desc())
    )
    if not current_user.is_admin:
        stmt = stmt.where(Product.vendor_profile_id == profile.id)
    total = int(
        db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    )
    products = list(db.scalars(stmt.limit(limit).offset(offset)).unique().all())
    return ProductListResponse(
        items=[product_to_response(p) for p in products],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/vendor/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def vendor_create_product(
    payload: ProductCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor),
) -> ProductResponse:
    # Authz: require_vendor — create SKU under own (or platform) vendor profile.
    profile = resolve_vendor_profile_for_writes(db, current_user)
    category = db.get(ShopCategory, payload.category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category")
    existing_sku = db.scalar(select(Product).where(Product.sku == payload.sku.strip()))
    if existing_sku is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")

    product = Product(
        vendor_profile_id=profile.id,
        category_id=payload.category_id,
        sku=payload.sku.strip(),
        name=payload.name.strip(),
        description=payload.description,
        price_cents=payload.price_cents,
        stock_qty=payload.stock_qty,
        active=payload.active,
    )
    db.add(product)
    db.flush()
    for sid in payload.species_ids:
        db.add(ProductSpecies(product_id=product.id, species_id=sid))
    db.commit()
    loaded = load_product(db, product.id)
    assert loaded is not None
    return product_to_response(loaded)


@router.patch("/vendor/products/{product_id}", response_model=ProductResponse)
def vendor_update_product(
    product_id: UUID,
    payload: ProductUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor),
) -> ProductResponse:
    # Authz: vendor may edit own products; admin any.
    profile = resolve_vendor_profile_for_writes(db, current_user)
    product = load_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if not current_user.is_admin and product.vendor_profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your product")

    if payload.category_id is not None:
        product.category_id = payload.category_id
    if payload.name is not None:
        product.name = payload.name.strip()
    if payload.description is not None:
        product.description = payload.description
    if payload.price_cents is not None:
        product.price_cents = payload.price_cents
    if payload.stock_qty is not None:
        product.stock_qty = payload.stock_qty
    if payload.active is not None:
        product.active = payload.active
    if payload.species_ids is not None:
        for tag in list(product.species_tags):
            db.delete(tag)
        db.flush()
        for sid in payload.species_ids:
            db.add(ProductSpecies(product_id=product.id, species_id=sid))
    db.commit()
    loaded = load_product(db, product.id)
    assert loaded is not None
    return product_to_response(loaded)


@router.get("/vendor/orders", response_model=OrderListResponse)
def vendor_list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor),
) -> OrderListResponse:
    # Authz: vendor sees orders containing their SKUs; admin sees all shop orders.
    if current_user.is_admin:
        orders = list(
            db.scalars(
                select(ShopOrder)
                .options(
                    joinedload(ShopOrder.items),
                    joinedload(ShopOrder.events),
                    joinedload(ShopOrder.payment),
                )
                .order_by(ShopOrder.created_at.desc())
            )
            .unique()
            .all()
        )
    else:
        profile = resolve_vendor_profile_for_writes(db, current_user)
        product_ids = list(
            db.scalars(
                select(Product.id).where(Product.vendor_profile_id == profile.id)
            ).all()
        )
        if not product_ids:
            return OrderListResponse(items=[], total=0)
        orders = list(
            db.scalars(
                select(ShopOrder)
                .join(ShopOrderItem)
                .options(
                    joinedload(ShopOrder.items),
                    joinedload(ShopOrder.events),
                    joinedload(ShopOrder.payment),
                )
                .where(ShopOrderItem.product_id.in_(product_ids))
                .order_by(ShopOrder.created_at.desc())
            )
            .unique()
            .all()
        )
    return OrderListResponse(items=[order_to_response(o) for o in orders], total=len(orders))


@router.patch("/vendor/orders/{order_id}", response_model=OrderResponse)
def vendor_fulfill_order(
    order_id: UUID,
    payload: VendorOrderFulfillRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_vendor),
) -> OrderResponse:
    # Authz: vendor/admin may advance fulfillment status on relevant orders.
    if payload.status not in _VENDOR_FULFILL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid fulfillment status transition",
        )
    order = db.scalar(
        select(ShopOrder)
        .options(
            joinedload(ShopOrder.items),
            joinedload(ShopOrder.events),
            joinedload(ShopOrder.payment),
        )
        .where(ShopOrder.id == order_id)
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not current_user.is_admin:
        profile = resolve_vendor_profile_for_writes(db, current_user)
        product_ids = [i.product_id for i in order.items if i.product_id]
        owned = db.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.id.in_(product_ids), Product.vendor_profile_id == profile.id)
        )
        if not owned:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    prev = order.status
    order.status = payload.status
    append_order_event(
        db,
        order,
        to_status=payload.status,
        actor_id=current_user.id,
        from_status=prev,
        note=payload.note,
    )
    db.commit()
    db.refresh(order)
    return order_to_response(order)


@router.post("/vendor/apply", response_model=VendorProfileResponse, status_code=status.HTTP_201_CREATED)
def apply_vendor(
    payload: VendorApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VendorProfile:
    # Authz: any authenticated user may request vendor capability (pending until admin approval).
    existing = get_vendor_profile_for_user(db, current_user)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vendor profile exists")
    current_user.is_vendor = True
    profile = VendorProfile(
        user_id=current_user.id,
        display_name=payload.display_name.strip(),
        bio=payload.bio,
        status=VendorStatus.PENDING,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/admin/vendors", response_model=list[VendorProfileResponse])
def admin_list_vendors(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[VendorProfile]:
    # Authz: require_admin — vendor moderation queue.
    return list(
        db.scalars(select(VendorProfile).order_by(VendorProfile.created_at.desc())).all()
    )


@router.patch("/admin/vendors/{vendor_id}", response_model=VendorProfileResponse)
def admin_update_vendor(
    vendor_id: UUID,
    payload: VendorStatusUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> VendorProfile:
    # Authz: require_admin — approve/suspend vendors.
    _ = admin
    profile = db.get(VendorProfile, vendor_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    profile.status = payload.status
    user = db.get(User, profile.user_id)
    if user is not None:
        user.is_vendor = payload.status != VendorStatus.SUSPENDED
    db.commit()
    db.refresh(profile)
    return profile
