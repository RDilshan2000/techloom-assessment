from datetime import datetime, timezone
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, computed_field

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, json_schema_extra={"example": "Wireless Mouse"})
    price: float = Field(..., gt=0, json_schema_extra={"example": 29.99})
    stock_quantity: int = Field(..., ge=0, json_schema_extra={"example": 100})

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)

class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reserved_quantity: int
    created_at: datetime
    updated_at: datetime

    @computed_field
    def total_stock(self) -> int:
        return self.stock_quantity + self.reserved_quantity

class RealtimeStockResponse(BaseModel):
    product_id: int
    name: str
    available_stock: int
    reserved_stock: int
    total_stock: int

class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float

    @computed_field
    def subtotal(self) -> float:
        return round(self.quantity * self.unit_price, 2)

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    total_amount: float
    reservation_expires_at: datetime
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    @computed_field
    def is_expired(self) -> bool:
        if self.status in ["PAID", "CANCELLED"]:
            return False
        expires_at = self.reservation_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= expires_at

class PaymentRequest(BaseModel):
    mock_status: Literal["SUCCESS", "FAILURE", "TIMEOUT"] = Field(..., json_schema_extra={"example": "SUCCESS"})
    idempotency_key: str = Field(..., min_length=1, max_length=255, json_schema_extra={"example": "idemp_123456789"})

class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    idempotency_key: str
    status: str
    created_at: datetime
    order_status: str
