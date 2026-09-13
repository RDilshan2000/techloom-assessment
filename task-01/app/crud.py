from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models import Product, Order, OrderItem, PaymentRecord
from app.schemas import ProductCreate, ProductUpdate, OrderCreate, PaymentRequest
from app.config import settings

# Product Operations
async def create_product(db: AsyncSession, product_in: ProductCreate) -> Product:
    product = Product(
        name=product_in.name,
        price=product_in.price,
        stock_quantity=product_in.stock_quantity,
        reserved_quantity=0
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

async def get_product(db: AsyncSession, product_id: int) -> Optional[Product]:
    stmt = select(Product).where(Product.id == product_id).execution_options(populate_existing=True)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def list_products(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Product]:
    stmt = select(Product).execution_options(populate_existing=True).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def update_product(db: AsyncSession, product_id: int, product_in: ProductUpdate) -> Optional[Product]:
    stmt = select(Product).where(Product.id == product_id).with_for_update()
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        return None
    
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await db.commit()
    await db.refresh(product)
    return product

async def delete_product(db: AsyncSession, product_id: int) -> bool:
    stmt = select(Product).where(Product.id == product_id).with_for_update()
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        return False
    await db.delete(product)
    await db.commit()
    return True

# Order Operations with Pessimistic Locking
async def create_order_with_reservation(db: AsyncSession, order_in: OrderCreate) -> Order:
    """
    Creates an order and reserves product stock atomically inside an ACID transaction.
    Uses SELECT FOR UPDATE pessimistic locking and atomic CAS updates to guarantee zero overselling.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.RESERVATION_EXPIRATION_MINUTES)
    
    total_amount = 0.0
    order_items = []

    # Lock and validate all requested products
    for item_in in order_in.items:
        stmt = select(Product).where(Product.id == item_in.product_id).with_for_update()
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product ID {item_in.product_id} not found."
            )

        # Atomic conditional stock deduction to guarantee concurrency safety under high parallel load
        update_stmt = (
            update(Product)
            .where(Product.id == item_in.product_id, Product.stock_quantity >= item_in.quantity)
            .values(
                stock_quantity=Product.stock_quantity - item_in.quantity,
                reserved_quantity=Product.reserved_quantity + item_in.quantity
            )
        )
        update_res = await db.execute(update_stmt)

        if update_res.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}, requested: {item_in.quantity}."
            )

        await db.refresh(product)

        item_total = round(product.price * item_in.quantity, 2)
        total_amount += item_total

        order_items.append(OrderItem(
            product=product,
            product_id=product.id,
            quantity=item_in.quantity,
            unit_price=product.price
        ))

    order = Order(
        status="RESERVED",
        total_amount=round(total_amount, 2),
        reservation_expires_at=expires_at,
        items=order_items
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order

async def get_order(db: AsyncSession, order_id: int) -> Optional[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .where(Order.id == order_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def list_orders(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def cancel_order(db: AsyncSession, order_id: int) -> Order:
    stmt = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .where(Order.id == order_id)
        .with_for_update()
    )
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order ID {order_id} not found."
        )

    if order.status not in ["RESERVED", "PENDING"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order #{order_id} in status '{order.status}'."
        )

    order.status = "CANCELLED"

    # Restore product stock
    for item in order.items:
        prod_stmt = select(Product).where(Product.id == item.product_id).with_for_update()
        prod_res = await db.execute(prod_stmt)
        product = prod_res.scalar_one_or_none()
        if product:
            product.stock_quantity += item.quantity
            product.reserved_quantity = max(0, product.reserved_quantity - item.quantity)

    await db.commit()
    await db.refresh(order)
    return order


def ensure_utc(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

# Payment Operations with Idempotency
async def process_payment(db: AsyncSession, order_id: int, payment_in: PaymentRequest) -> PaymentRecord:
    # 1. Check idempotency key first inside transaction
    existing_stmt = select(PaymentRecord).where(PaymentRecord.idempotency_key == payment_in.idempotency_key)
    existing_res = await db.execute(existing_stmt)
    existing_payment = existing_res.scalar_one_or_none()

    if existing_payment:
        if existing_payment.order_id != order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Idempotency key '{payment_in.idempotency_key}' was already used for order #{existing_payment.order_id}."
            )
        return existing_payment

    now = datetime.now(timezone.utc)
    order_stmt = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .where(Order.id == order_id)
        .with_for_update()
    )
    order_res = await db.execute(order_stmt)
    order = order_res.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order ID {order_id} not found."
        )

    if order.status == "PAID":
        # Order is already paid, record duplicate idempotent payment attempt as success
        payment_record = PaymentRecord(
            order_id=order.id,
            idempotency_key=payment_in.idempotency_key,
            status="SUCCESS"
        )
        db.add(payment_record)
        await db.commit()
        return payment_record

    if order.status in ["CANCELLED", "EXPIRED", "FAILED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot process payment for order #{order_id} in status '{order.status}'."
        )

    # Check if reservation expired
    if ensure_utc(order.reservation_expires_at) <= now:
        order.status = "EXPIRED"
        for item in order.items:
            prod_stmt = select(Product).where(Product.id == item.product_id).with_for_update()
            prod_res = await db.execute(prod_stmt)
            product = prod_res.scalar_one_or_none()
            if product:
                product.stock_quantity += item.quantity
                product.reserved_quantity = max(0, product.reserved_quantity - item.quantity)
        
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reservation for order #{order_id} has expired."
        )

    # Process payment state transition based on mock_status
    if payment_in.mock_status == "SUCCESS":
        order.status = "PAID"
        for item in order.items:
            prod_stmt = select(Product).where(Product.id == item.product_id).with_for_update()
            prod_res = await db.execute(prod_stmt)
            product = prod_res.scalar_one_or_none()
            if product:
                product.reserved_quantity = max(0, product.reserved_quantity - item.quantity)

    elif payment_in.mock_status == "FAILURE":
        order.status = "FAILED"
        for item in order.items:
            prod_stmt = select(Product).where(Product.id == item.product_id).with_for_update()
            prod_res = await db.execute(prod_stmt)
            product = prod_res.scalar_one_or_none()
            if product:
                product.stock_quantity += item.quantity
                product.reserved_quantity = max(0, product.reserved_quantity - item.quantity)

    elif payment_in.mock_status == "TIMEOUT":
        order.status = "EXPIRED"
        for item in order.items:
            prod_stmt = select(Product).where(Product.id == item.product_id).with_for_update()
            prod_res = await db.execute(prod_stmt)
            product = prod_res.scalar_one_or_none()
            if product:
                product.stock_quantity += item.quantity
                product.reserved_quantity = max(0, product.reserved_quantity - item.quantity)

    payment_record = PaymentRecord(
        order_id=order.id,
        idempotency_key=payment_in.idempotency_key,
        status=payment_in.mock_status
    )
    db.add(payment_record)
    await db.commit()
    await db.refresh(payment_record)
    return payment_record
