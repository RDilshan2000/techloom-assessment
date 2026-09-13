from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import PaymentRequest, PaymentResponse
from app.services import payment_service

router = APIRouter(prefix="/api/orders", tags=["Payments"])

@router.post("/{order_id}/pay", response_model=PaymentResponse)
async def process_payment(
    order_id: int,
    payment_req: PaymentRequest,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    db: AsyncSession = Depends(get_db)
):
    if x_idempotency_key and x_idempotency_key.strip():
        payment_req.idempotency_key = x_idempotency_key.strip()

    return await payment_service.process_payment(db, order_id, payment_req)
