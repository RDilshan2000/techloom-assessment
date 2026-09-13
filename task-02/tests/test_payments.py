import uuid
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_payment_success(async_client: AsyncClient):
    prod_res = await async_client.get("/api/products")
    product = prod_res.json()[0]
    initial_stock = product["stock"]

    # Checkout
    co_res = await async_client.post("/api/orders/checkout", json={
        "customer_name": "Dave",
        "customer_email": "dave@example.com",
        "items": [{"product_id": product["id"], "quantity": 1}]
    })
    order = co_res.json()

    # Pay Success
    idem_key = f"IDEM-TEST-{uuid.uuid4().hex}"
    pay_res = await async_client.post(f"/api/orders/{order['id']}/pay", json={
        "idempotency_key": idem_key,
        "payment_action": "SUCCESS",
        "payment_method": "Credit Card"
    })
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["order_status"] == "PAID"
    assert pay_data["payment_status"] == "SUCCESS"
    assert pay_data["cached"] is False

    # Check inventory: reserved_stock should be 0, available stock should remain initial_stock - 1
    prod_after = (await async_client.get(f"/api/products/{product['id']}")).json()
    assert prod_after["stock"] == initial_stock - 1
    assert prod_after["reserved_stock"] == 0

@pytest.mark.asyncio
async def test_payment_failure(async_client: AsyncClient):
    prod_res = await async_client.get("/api/products")
    product = prod_res.json()[0]
    initial_stock = product["stock"]

    # Checkout
    co_res = await async_client.post("/api/orders/checkout", json={
        "customer_name": "Eve",
        "customer_email": "eve@example.com",
        "items": [{"product_id": product["id"], "quantity": 2}]
    })
    order = co_res.json()

    # Pay Failure
    idem_key = f"IDEM-FAIL-{uuid.uuid4().hex}"
    pay_res = await async_client.post(f"/api/orders/{order['id']}/pay", json={
        "idempotency_key": idem_key,
        "payment_action": "FAILED",
        "payment_method": "Credit Card"
    })
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["order_status"] == "FAILED"
    assert pay_data["payment_status"] == "FAILED"

    # Inventory should be restored to initial_stock
    prod_after = (await async_client.get(f"/api/products/{product['id']}")).json()
    assert prod_after["stock"] == initial_stock
    assert prod_after["reserved_stock"] == 0

@pytest.mark.asyncio
async def test_payment_idempotency_caching(async_client: AsyncClient):
    prod_res = await async_client.get("/api/products")
    product = prod_res.json()[0]

    # Checkout
    co_res = await async_client.post("/api/orders/checkout", json={
        "customer_name": "Frank",
        "customer_email": "frank@example.com",
        "items": [{"product_id": product["id"], "quantity": 1}]
    })
    order = co_res.json()
    idem_key = f"IDEM-SAME-{uuid.uuid4().hex}"

    # First request
    pay1 = await async_client.post(f"/api/orders/{order['id']}/pay", json={
        "idempotency_key": idem_key,
        "payment_action": "SUCCESS",
        "payment_method": "Credit Card"
    })
    assert pay1.status_code == 200
    assert pay1.json()["cached"] is False

    # Second request with SAME idempotency key
    pay2 = await async_client.post(f"/api/orders/{order['id']}/pay", json={
        "idempotency_key": idem_key,
        "payment_action": "SUCCESS",
        "payment_method": "Credit Card"
    })
    assert pay2.status_code == 200
    data2 = pay2.json()
    assert data2["cached"] is True
    assert "Duplicate request" in data2["message"]

@pytest.mark.asyncio
async def test_refund_paid_order(async_client: AsyncClient):
    prod_res = await async_client.get("/api/products")
    product = prod_res.json()[0]
    initial_stock = product["stock"]

    # Checkout & Pay
    co_res = await async_client.post("/api/orders/checkout", json={
        "customer_name": "Grace",
        "customer_email": "grace@example.com",
        "items": [{"product_id": product["id"], "quantity": 3}]
    })
    order = co_res.json()

    idem_key = f"IDEM-REFUND-{uuid.uuid4().hex}"
    await async_client.post(f"/api/orders/{order['id']}/pay", json={
        "idempotency_key": idem_key,
        "payment_action": "SUCCESS",
        "payment_method": "Credit Card"
    })

    # Refund
    ref_res = await async_client.post(f"/api/orders/{order['id']}/refund")
    assert ref_res.status_code == 200
    assert ref_res.json()["status"] == "REFUNDED"

    # Stock should be fully restored
    prod_after = (await async_client.get(f"/api/products/{product['id']}")).json()
    assert prod_after["stock"] == initial_stock
