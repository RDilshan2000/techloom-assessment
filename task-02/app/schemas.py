from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from app.models import OrderStatus, PaymentStatus

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field("", max_length=2000)
    category: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    image_url: str = Field("", max_length=500)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)

class AddStockRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity of stock to add")

class ProductRead(ProductBase):
    id: int
    reserved_stock: int
    total_stock: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CartItemInput(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: str = Field(..., min_length=3, max_length=255)
    items: List[CartItemInput] = Field(..., min_length=1)

class OrderItemRead(BaseModel):
    id: int
    product_id: Optional[int] = None
    product_name: str
    unit_price: float
    quantity: int
    subtotal: float

    model_config = ConfigDict(from_attributes=True)

class OrderRead(BaseModel):
    id: int
    order_number: str
    customer_name: str
    customer_email: str
    total_amount: float
    status: OrderStatus
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemRead] = []
    seconds_remaining: int = 0

    model_config = ConfigDict(from_attributes=True)

class PaymentRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=1, max_length=128)
    payment_action: PaymentStatus = Field(..., description="Action to simulate: SUCCESS, FAILED, TIMEOUT")
    payment_method: str = Field("Credit Card", min_length=1, max_length=100)

class PaymentResponse(BaseModel):
    transaction_id: int
    order_id: int
    order_number: str
    order_status: OrderStatus
    payment_status: PaymentStatus
    idempotency_key: str
    amount: float
    message: str
    cached: bool = False

class OrderCancelRequest(BaseModel):
    reason: Optional[str] = None

class SeedResponse(BaseModel):
    message: str
    product_count: int
