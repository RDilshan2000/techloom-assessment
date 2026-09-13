import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models import Order, OrderItem, Product, OrderStatus, utc_now
from app.schemas import CheckoutRequest
from app.config import settings

def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def calculate_seconds_remaining(expires_at: datetime) -> int:
    now = utc_now()
    expires_utc = ensure_utc(expires_at)
    diff = (expires_utc - now).total_seconds()
    return max(0, int(diff))

async def create_order(db: AsyncSession, checkout_data: CheckoutRequest) -> Order:
    if not checkout_data.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty."
        )

    # Consolidate duplicate products in request if any
    item_quantities = {}
    for item in checkout_data.items:
        item_quantities[item.product_id] = item_quantities.get(item.product_id, 0) + item.quantity

    total_amount = 0.0
    order_items_to_create = []

    # Process items and reserve stock
    for product_id, qty in item_quantities.items():
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found."
            )

        if product.stock < qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'. Available: {product.stock}, Requested: {qty}."
            )

        # Deduct available stock and reserve
        product.stock -= qty
        product.reserved_stock += qty

        subtotal = round(product.price * qty, 2)
        total_amount += subtotal

        order_items_to_create.append({
            "product_id": product.id,
            "product_name": product.name,
            "unit_price": product.price,
            "quantity": qty,
            "subtotal": subtotal,
            "product_ref": product
        })

    total_amount = round(total_amount, 2)
    order_num = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    expiry_time = utc_now() + timedelta(minutes=settings.RESERVATION_EXPIRY_MINUTES)

    order = Order(
        order_number=order_num,
        customer_name=checkout_data.customer_name.strip(),
        customer_email=checkout_data.customer_email.strip(),
        total_amount=total_amount,
        status=OrderStatus.RESERVED,
        expires_at=expiry_time
    )

    db.add(order)
    await db.flush()  # assign order.id

    for item_data in order_items_to_create:
        item = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            product_name=item_data["product_name"],
            unit_price=item_data["unit_price"],
            quantity=item_data["quantity"],
            subtotal=item_data["subtotal"]
        )
        db.add(item)

    await db.commit()
    await db.refresh(order)
    return order

async def get_order_by_id(db: AsyncSession, order_id: int) -> Optional[Order]:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        return None

    # Check for lazy expiration
    if order.status == OrderStatus.RESERVED and calculate_seconds_remaining(order.expires_at) <= 0:
        await expire_single_order(db, order)

    return order

async def get_orders(
    db: AsyncSession,
    order_status: Optional[OrderStatus] = None,
    customer_email: Optional[str] = None
) -> List[Order]:
    query = select(Order)
    
    if order_status:
        query = query.where(Order.status == order_status)
    if customer_email and customer_email.strip():
        query = query.where(Order.customer_email.ilike(f"%{customer_email.strip()}%"))

    query = query.order_by(Order.created_at.desc())
    result = await db.execute(query)
    orders = result.scalars().all()

    # Perform expiration check on RESERVED orders
    for order in orders:
        if order.status == OrderStatus.RESERVED and calculate_seconds_remaining(order.expires_at) <= 0:
            await expire_single_order(db, order)

    return list(orders)

async def expire_single_order(db: AsyncSession, order: Order):
    if order.status != OrderStatus.RESERVED:
        return

    order.status = OrderStatus.EXPIRED
    for item in order.items:
        if item.product_id:
            res = await db.execute(select(Product).where(Product.id == item.product_id))
            product = res.scalar_one_or_none()
            if product:
                product.stock += item.quantity
                product.reserved_stock = max(0, product.reserved_stock - item.quantity)

    await db.commit()

async def cancel_order(db: AsyncSession, order_id: int) -> Order:
    order = await get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} not found."
        )

    if order.status != OrderStatus.RESERVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in status '{order.status.value}'. Only RESERVED orders can be cancelled."
        )

    order.status = OrderStatus.CANCELLED
    for item in order.items:
        if item.product_id:
            res = await db.execute(select(Product).where(Product.id == item.product_id))
            product = res.scalar_one_or_none()
            if product:
                product.stock += item.quantity
                product.reserved_stock = max(0, product.reserved_stock - item.quantity)

    await db.commit()
    await db.refresh(order)
    return order

async def refund_order(db: AsyncSession, order_id: int) -> Order:
    order = await get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} not found."
        )

    if order.status != OrderStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot refund order in status '{order.status.value}'. Only PAID orders can be refunded."
        )

    order.status = OrderStatus.REFUNDED
    for item in order.items:
        if item.product_id:
            res = await db.execute(select(Product).where(Product.id == item.product_id))
            product = res.scalar_one_or_none()
            if product:
                product.stock += item.quantity

    await db.commit()
    await db.refresh(order)
    return order

async def cleanup_expired_orders(db: AsyncSession) -> int:
    now = utc_now()
    result = await db.execute(
        select(Order).where(
            Order.status == OrderStatus.RESERVED,
            Order.expires_at <= now
        )
    )
    expired_orders = result.scalars().all()
    count = 0

    for order in expired_orders:
        order.status = OrderStatus.EXPIRED
        for item in order.items:
            if item.product_id:
                res = await db.execute(select(Product).where(Product.id == item.product_id))
                product = res.scalar_one_or_none()
                if product:
                    product.stock += item.quantity
                    product.reserved_stock = max(0, product.reserved_stock - item.quantity)
        count += 1

    if count > 0:
        await db.commit()

    return count
