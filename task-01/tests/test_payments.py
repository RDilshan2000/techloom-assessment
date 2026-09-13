import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Order

@pytest.mark.asyncio
async def test_payment_success(async_client: AsyncClient):
    prod = (await async_client.post("/api/products", json={"name": "PayItem", "price": 40.0, "stock_quantity": 10})).json()
    order = (await async_client.post("/api/orders", json={"items": [{"product_id": prod["id"], "quantity": 3}]})).json()

    pay_res = await async_client.post(f"/api/orders/{order['id']}/pay", json={
        "mock_status": "SUCCESS",
        "idempotency_key": "IDEM-T117-SUCCESS"
    })
    assert pay_res.status_code == 200
    assert pay_res.json()["order_status"] == "PAID"

    # Stock check: available remains 7, reserved becomes 0
    stock = (await async_client.get(f"/api/products/{prod['id']}/stock")).json()
    assert stock["available_stock"] == 7
    assert stock["reserved_stock"] == 0

@pytest.mark.asyncio
async def test_payment_failure(async_client: AsyncClient):
    prod = (await async_client.post("/api/products", json={"name": "FailItem", "price": 40.0, "stock_quantity": 10})).json()
    order = (await async_client.post("/api/orders", json={"items": [{"product_id": prod["id"], "quantity": 3}]})).json()

    pay_res = await async_client.post(f"/api/orders/{order['id']}/pay", json={
        "mock_status": "FAILURE",
        "idempotency_key": "IDEM-T118-FAILURE"
    })
    assert pay_res.status_code == 200
    assert pay_res.json()["order_status"] == "FAILED"

    # Stock check: restored to 10
    stock = (await async_client.get(f"/api/products/{prod['id']}/stock")).json()
    assert stock["available_stock"] == 10
    assert stock["reserved_stock"] == 0

@pytest.mark.asyncio
async def test_payment_timeout(async_client: AsyncClient):
    prod = (await async_client.post("/api/products", json={"name": "TimeoutItem", "price": 40.0, "stock_quantity": 10})).json()
    order = (await async_client.post("/api/orders", json={"items": [{"product_id": prod["id"], "quantity": 2}]})).json()

    pay_res = await async_client.post(f"/api/orders/{order['id']}/pay", json={
        "mock_status": "TIMEOUT",
        "idempotency_key": "IDEM-T119-TIMEOUT"
    })
    assert pay_res.status_code == 200
    assert pay_res.json()["order_status"] == "EXPIRED"

    # Stock check: restored
    stock = (await async_client.get(f"/api/products/{prod['id']}/stock")).json()
    assert stock["available_stock"] == 10
    assert stock["reserved_stock"] == 0

@pytest.mark.asyncio
async def test_payment_idempotency_caching(async_client: AsyncClient):
    prod = (await async_client.post("/api/products", json={"name": "IdemItem", "price": 20.0, "stock_quantity": 10})).json()
    order = (await async_client.post("/api/orders", json={"items": [{"product_id": prod["id"], "quantity": 1}]})).json()

    idem_key = "IDEM-SAME-KEY-001"
    res1 = await async_client.post(f"/api/orders/{order['id']}/pay", json={
        "mock_status": "SUCCESS",
        "idempotency_key": idem_key
    })
    assert res1.status_code == 200

    res2 = await async_client.post(f"/api/orders/{order['id']}/pay", json={
        "mock_status": "SUCCESS",
        "idempotency_key": idem_key
    })
    assert res2.status_code == 200
    assert res2.json()["idempotency_key"] == idem_key

@pytest.mark.asyncio
async def test_idempotency_key_reuse_different_order(async_client: AsyncClient):
    prod = (await async_client.post("/api/products", json={"name": "ShareItem", "price": 20.0, "stock_quantity": 10})).json()
    order1 = (await async_client.post("/api/orders", json={"items": [{"product_id": prod["id"], "quantity": 1}]})).json()
    order2 = (await async_client.post("/api/orders", json={"items": [{"product_id": prod["id"], "quantity": 1}]})).json()

    idem_key = "SHARED-IDEM-KEY"
    await async_client.post(f"/api/orders/{order1['id']}/pay", json={"mock_status": "SUCCESS", "idempotency_key": idem_key})

    # Try reusing same key for order2
    res2 = await async_client.post(f"/api/orders/{order2['id']}/pay", json={"mock_status": "SUCCESS", "idempotency_key": idem_key})
    assert res2.status_code == 400
    assert "already used for order" in res2.json()["detail"]

@pytest.mark.asyncio
async def test_payment_attempt_on_expired_order(async_client: AsyncClient, db_session: AsyncSession):
    prod = (await async_client.post("/api/products", json={"name": "ExpItem", "price": 50.0, "stock_quantity": 10})).json()
    order_data = (await async_client.post("/api/orders", json={"items": [{"product_id": prod["id"], "quantity": 2}]})).json()

    # Manually backdate reservation_expires_at in database
    result = await db_session.execute(select(Order).where(Order.id == order_data["id"]))
    order = result.scalar_one()
    order.reservation_expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    await db_session.commit()

    # Try paying
    pay_res = await async_client.post(f"/api/orders/{order_data['id']}/pay", json={
        "mock_status": "SUCCESS",
        "idempotency_key": "EXP-PAY-KEY"
    })
    assert pay_res.status_code == 400
    assert "expired" in pay_res.json()["detail"].lower()
