from typing import Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models import Order, PaymentTransaction, Product, OrderStatus, PaymentStatus
from app.schemas import PaymentRequest, PaymentResponse
from app.services.order_service import calculate_seconds_remaining, expire_single_order

async def process_payment(
    db: AsyncSession,
    order_id: int,
    payment_req: PaymentRequest
) -> PaymentResponse:
    # 1. Idempotency Check
    existing_tx_res = await db.execute(
        select(PaymentTransaction).where(PaymentTransaction.idempotency_key == payment_req.idempotency_key)
    )
    existing_tx = existing_tx_res.scalar_one_or_none()

    if existing_tx:
        # Idempotent response: return cached result
        order_res = await db.execute(select(Order).where(Order.id == existing_tx.order_id))
        order = order_res.scalar_one()
        return PaymentResponse(
            transaction_id=existing_tx.id,
            order_id=order.id,
            order_number=order.order_number,
            order_status=order.status,
            payment_status=existing_tx.status,
            idempotency_key=existing_tx.idempotency_key,
            amount=existing_tx.amount,
            message=f"Duplicate request detected. Returning cached response: {existing_tx.error_message or 'Transaction processed'}.",
            cached=True
        )

    # 2. Retrieve Order
    order_res = await db.execute(select(Order).where(Order.id == order_id))
    order = order_res.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} not found."
        )

    # Check for order state validity
    if order.status != OrderStatus.RESERVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is in '{order.status.value}' state and cannot be processed for payment."
        )

    # Check expiration
    if calculate_seconds_remaining(order.expires_at) <= 0:
        await expire_single_order(db, order)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order reservation expired before payment completed. Items have been released back to stock."
        )

    # 3. Process Payment Action
    action = payment_req.payment_action

    if action == PaymentStatus.SUCCESS:
        order.status = OrderStatus.PAID
        # Finalize deduction: reserved_stock was already held, now convert reservation to final sale
        for item in order.items:
            if item.product_id:
                prod_res = await db.execute(select(Product).where(Product.id == item.product_id))
                product = prod_res.scalar_one_or_none()
                if product:
                    product.reserved_stock = max(0, product.reserved_stock - item.quantity)

        tx = PaymentTransaction(
            order_id=order.id,
            idempotency_key=payment_req.idempotency_key,
            status=PaymentStatus.SUCCESS,
            payment_method=payment_req.payment_method,
            amount=order.total_amount,
            error_message="Payment processed successfully."
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)
        await db.refresh(order)

        return PaymentResponse(
            transaction_id=tx.id,
            order_id=order.id,
            order_number=order.order_number,
            order_status=order.status,
            payment_status=tx.status,
            idempotency_key=tx.idempotency_key,
            amount=tx.amount,
            message="Payment completed successfully! Order status set to PAID.",
            cached=False
        )

    elif action == PaymentStatus.FAILED:
        order.status = OrderStatus.FAILED
        # Restore reserved stock back to available stock
        for item in order.items:
            if item.product_id:
                prod_res = await db.execute(select(Product).where(Product.id == item.product_id))
                product = prod_res.scalar_one_or_none()
                if product:
                    product.stock += item.quantity
                    product.reserved_stock = max(0, product.reserved_stock - item.quantity)

        tx = PaymentTransaction(
            order_id=order.id,
            idempotency_key=payment_req.idempotency_key,
            status=PaymentStatus.FAILED,
            payment_method=payment_req.payment_method,
            amount=order.total_amount,
            error_message="Payment declined by bank / card authorization failed."
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)
        await db.refresh(order)

        return PaymentResponse(
            transaction_id=tx.id,
            order_id=order.id,
            order_number=order.order_number,
            order_status=order.status,
            payment_status=tx.status,
            idempotency_key=tx.idempotency_key,
            amount=tx.amount,
            message="Payment failed! Reservation released back to inventory.",
            cached=False
        )

    elif action == PaymentStatus.TIMEOUT:
        # Timeout scenario: order remains RESERVED, transaction recorded as TIMEOUT
        tx = PaymentTransaction(
            order_id=order.id,
            idempotency_key=payment_req.idempotency_key,
            status=PaymentStatus.TIMEOUT,
            payment_method=payment_req.payment_method,
            amount=order.total_amount,
            error_message="Gateway timeout waiting for response. Order remains reserved until 5-minute expiry."
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)

        return PaymentResponse(
            transaction_id=tx.id,
            order_id=order.id,
            order_number=order.order_number,
            order_status=order.status,
            payment_status=tx.status,
            idempotency_key=tx.idempotency_key,
            amount=tx.amount,
            message="Gateway timed out! Order remains reserved until 5-minute expiry cleanup.",
            cached=False
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment action: {action}"
        )
