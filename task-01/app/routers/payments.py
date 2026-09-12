from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import PaymentRequest, PaymentResponse
from app import crud

router = APIRouter()

@router.post("/orders/{order_id}/pay", response_model=PaymentResponse)
async def process_payment_endpoint(
    order_id: int,
    payment_in: PaymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Process mock payment for an order with strict idempotency support.
    
    Accepts:
    - mock_status: 'SUCCESS' | 'FAILURE' | 'TIMEOUT'
    - idempotency_key: Unique identifier to prevent duplicate submissions.
    """
    payment_record = await crud.process_payment(db, order_id, payment_in)
    order = await crud.get_order(db, order_id)
    order_status = order.status if order else "UNKNOWN"

    return PaymentResponse(
        id=payment_record.id,
        order_id=payment_record.order_id,
        idempotency_key=payment_record.idempotency_key,
        status=payment_record.status,
        created_at=payment_record.created_at,
        order_status=order_status
    )
