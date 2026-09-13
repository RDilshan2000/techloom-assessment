from datetime import timedelta
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from app.models import Order, Product, OrderStatus, utc_now
from app.services.order_service import cleanup_expired_orders

@pytest.mark.asyncio
async def test_cleanup_expired_orders(async_client: AsyncClient, db_session: AsyncSession):
    # Get a product
    prod_res = await async_client.get("/api/products")
    product = prod_res.json()[0]
    initial_stock = product["stock"]

    # Checkout
    co_res = await async_client.post("/api/orders/checkout", json={
        "customer_name": "Timer Test",
        "customer_email": "timer@example.com",
        "items": [{"product_id": product["id"], "quantity": 2}]
    })
    order_id = co_res.json()["id"]

    # Manually backdate expires_at in DB to simulate 5-minute timeout elapsed
    order_res = await db_session.execute(select(Order).where(Order.id == order_id))
    order = order_res.scalar_one()
    order.expires_at = utc_now() - timedelta(minutes=10)
    await db_session.commit()

    # Run cleanup service function
    cleaned_count = await cleanup_expired_orders(db_session)
    assert cleaned_count == 1

    # Verify order is EXPIRED
    await db_session.refresh(order)
    assert order.status == OrderStatus.EXPIRED

    # Verify stock restored
    prod_after = (await async_client.get(f"/api/products/{product['id']}")).json()
    assert prod_after["stock"] == initial_stock
    assert prod_after["reserved_stock"] == 0
