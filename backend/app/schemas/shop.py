from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.shop import FulfillmentType, ShopOrderStatus, ShopPaymentStatus
from app.models.vendor_profile import VendorStatus


class ShopPublicConfigResponse(BaseModel):
    payments_enabled: bool
    stripe_test_mode: bool


class ShopCategoryResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    sort_order: int
    active: bool

    model_config = {"from_attributes": True}


class ProductSpeciesTag(BaseModel):
    id: UUID
    name: str


class ProductImageResponse(BaseModel):
    id: UUID
    url: str
    sort_order: int


class ProductResponse(BaseModel):
    id: UUID
    sku: str
    name: str
    description: str | None
    price_cents: int
    currency: str
    stock_qty: int
    active: bool
    category_id: UUID
    category_slug: str | None = None
    category_name: str | None = None
    vendor_profile_id: UUID
    species: list[ProductSpeciesTag] = []
    images: list[ProductImageResponse] = []
    created_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    limit: int
    offset: int


class ProductCreateRequest(BaseModel):
    category_id: UUID
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    price_cents: int = Field(ge=0)
    stock_qty: int = Field(ge=0, default=0)
    active: bool = True
    species_ids: list[UUID] = Field(default_factory=list)


class ProductUpdateRequest(BaseModel):
    category_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    price_cents: int | None = Field(default=None, ge=0)
    stock_qty: int | None = Field(default=None, ge=0)
    active: bool | None = None
    species_ids: list[UUID] | None = None


class CartItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    product_sku: str
    unit_price_cents: int
    qty: int
    line_total_cents: int
    stock_qty: int


class CartResponse(BaseModel):
    id: UUID
    items: list[CartItemResponse]
    subtotal_cents: int


class CartAddRequest(BaseModel):
    product_id: UUID
    qty: int = Field(ge=1, default=1)


class CartUpdateItemRequest(BaseModel):
    qty: int = Field(ge=0)


class CheckoutRequest(BaseModel):
    fulfillment_type: FulfillmentType
    ship_name: str | None = Field(default=None, max_length=200)
    ship_line1: str | None = Field(default=None, max_length=200)
    ship_line2: str | None = Field(default=None, max_length=200)
    ship_city: str | None = Field(default=None, max_length=100)
    ship_state: str | None = Field(default=None, max_length=64)
    ship_postal: str | None = Field(default=None, max_length=32)
    ship_country: str | None = Field(default="US", max_length=2)


class CheckoutResponse(BaseModel):
    order_id: UUID
    checkout_url: str | None
    status: ShopOrderStatus
    total_cents: int


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID | None
    product_name: str
    product_sku: str
    unit_price_cents: int
    qty: int


class OrderEventResponse(BaseModel):
    id: UUID
    from_status: str | None
    to_status: str
    note: str | None
    created_at: datetime


class OrderResponse(BaseModel):
    id: UUID
    status: ShopOrderStatus
    fulfillment_type: FulfillmentType
    ship_name: str | None
    ship_line1: str | None
    ship_line2: str | None
    ship_city: str | None
    ship_state: str | None
    ship_postal: str | None
    ship_country: str | None
    subtotal_cents: int
    tax_cents: int
    shipping_cents: int
    total_cents: int
    currency: str
    items: list[OrderItemResponse]
    events: list[OrderEventResponse] = []
    payment_status: ShopPaymentStatus | None = None
    created_at: datetime


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int


class VendorOrderFulfillRequest(BaseModel):
    status: ShopOrderStatus
    note: str | None = Field(default=None, max_length=500)


class VendorProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    display_name: str
    bio: str | None
    status: VendorStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class VendorApplyRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    bio: str | None = None


class VendorStatusUpdateRequest(BaseModel):
    status: VendorStatus
    note: str | None = Field(default=None, max_length=500)


class EnableVendorRequest(BaseModel):
    is_vendor: bool
    display_name: str | None = Field(default=None, max_length=120)
