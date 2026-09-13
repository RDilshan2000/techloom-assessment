from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import OrderStatus
from app.schemas import CheckoutRequest, OrderRead, OrderCancelRequest
from app.services import order_service

router = APIRouter(prefix="/api/orders", tags=["Orders"])

def prepare_order_response(order) -> OrderRead:
    order_dict = OrderRead.model_validate(order)
    if order.status == OrderStatus.RESERVED:
        order_dict.seconds_remaining = order_service.calculate_seconds_remaining(order.expires_at)
    else:
        order_dict.seconds_remaining = 0
    return order_dict

@router.post("/checkout", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def checkout(
    checkout_data: CheckoutRequest,
    db: AsyncSession = Depends(get_db)
):
    order = await order_service.create_order(db, checkout_data)
    return prepare_order_response(order)

@router.get("", response_model=List[OrderRead])
async def list_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status", description="Filter by order status"),
    email_filter: Optional[str] = Query(None, alias="email", description="Filter by customer email"),
    db: AsyncSession = Depends(get_db)
):
    orders = await order_service.get_orders(db, order_status=status_filter, customer_email=email_filter)
    return [prepare_order_response(order) for order in orders]

@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    order = await order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found."
        )
    return prepare_order_response(order)

@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    order = await order_service.cancel_order(db, order_id)
    return prepare_order_response(order)

@router.post("/{order_id}/refund", response_model=OrderRead)
async def refund_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    order = await order_service.refund_order(db, order_id)
    return prepare_order_response(order)
