from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import OrderCreate, OrderResponse, OrderItemResponse
from app import crud

router = APIRouter()

def build_order_response(order) -> OrderResponse:
    if not order:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve order details.")
    items = []
    for item in (order.items or []):
        prod_name = f"Product #{item.product_id}"
        if "product" in item.__dict__ and item.__dict__["product"] is not None:
            prod_name = item.__dict__["product"].name
        items.append(
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=prod_name,
                quantity=item.quantity,
                unit_price=item.unit_price
            )
        )
    return OrderResponse(
        id=order.id,
        status=order.status,
        total_amount=order.total_amount,
        reservation_expires_at=order.reservation_expires_at,
        items=items,
        created_at=order.created_at,
        updated_at=order.updated_at
    )

@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order_endpoint(order_in: OrderCreate, db: AsyncSession = Depends(get_db)):
    """
    Create an order with instant 5-minute stock reservation.
    Uses concurrency-safe pessimistic row locking (SELECT ... FOR UPDATE) inside an ACID transaction.
    """
    order = await crud.create_order_with_reservation(db, order_in)
    return build_order_response(order)

@router.get("/orders", response_model=List[OrderResponse])
async def list_orders_endpoint(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List all orders with status, expiration times, and item details."""
    orders = await crud.list_orders(db, skip=skip, limit=limit)
    return [build_order_response(o) for o in orders]

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_endpoint(order_id: int, db: AsyncSession = Depends(get_db)):
    """Get details of a specific order."""
    order = await crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order ID {order_id} not found.")
    return build_order_response(order)

@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order_endpoint(order_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel an active reserved order and restore its stock to the available inventory pool."""
    order = await crud.cancel_order(db, order_id)
    return build_order_response(order)
