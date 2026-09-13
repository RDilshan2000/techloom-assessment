import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_order_reserves_stock(async_client: AsyncClient):
    prod_res = await async_client.post("/api/products", json={"name": "Item A", "price": 50.0, "stock_quantity": 10})
    prod_id = prod_res.json()["id"]

    order_res = await async_client.post("/api/orders", json={
        "items": [{"product_id": prod_id, "quantity": 3}]
    })
    assert order_res.status_code == 201
    order_data = order_res.json()
    assert order_data["status"] == "RESERVED"
    assert order_data["total_amount"] == 150.0

    # Stock verification
    stock_res = await async_client.get(f"/api/products/{prod_id}/stock")
    stock_data = stock_res.json()
    assert stock_data["available_stock"] == 7
    assert stock_data["reserved_stock"] == 3

@pytest.mark.asyncio
async def test_create_order_insufficient_stock(async_client: AsyncClient):
    prod_res = await async_client.post("/api/products", json={"name": "Low Stock Item", "price": 10.0, "stock_quantity": 4})
    prod_id = prod_res.json()["id"]

    order_res = await async_client.post("/api/orders", json={
        "items": [{"product_id": prod_id, "quantity": 10}]
    })
    assert order_res.status_code == 400
    assert "Insufficient stock" in order_res.json()["detail"]

    # Stock unchanged
    stock_data = (await async_client.get(f"/api/products/{prod_id}/stock")).json()
    assert stock_data["available_stock"] == 4
    assert stock_data["reserved_stock"] == 0

@pytest.mark.asyncio
async def test_multi_product_atomic_order_failure(async_client: AsyncClient):
    p1 = (await async_client.post("/api/products", json={"name": "P1", "price": 10.0, "stock_quantity": 10})).json()
    p2 = (await async_client.post("/api/products", json={"name": "P2", "price": 20.0, "stock_quantity": 2})).json()

    order_res = await async_client.post("/api/orders", json={
        "items": [
            {"product_id": p1["id"], "quantity": 2},
            {"product_id": p2["id"], "quantity": 5} # Exceeds P2 stock (2)
        ]
    })
    assert order_res.status_code == 400

    # Rollback verification: P1 stock should NOT be partially reserved
    s1 = (await async_client.get(f"/api/products/{p1['id']}/stock")).json()
    assert s1["available_stock"] == 10
    assert s1["reserved_stock"] == 0

@pytest.mark.asyncio
async def test_cancel_reserved_order(async_client: AsyncClient):
    prod = (await async_client.post("/api/products", json={"name": "Cancelable", "price": 30.0, "stock_quantity": 10})).json()

    co_res = await async_client.post("/api/orders", json={"items": [{"product_id": prod["id"], "quantity": 4}]})
    order_id = co_res.json()["id"]

    cancel_res = await async_client.post(f"/api/orders/{order_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Stock restored
    s_after = (await async_client.get(f"/api/products/{prod['id']}/stock")).json()
    assert s_after["available_stock"] == 10
    assert s_after["reserved_stock"] == 0

@pytest.mark.asyncio
async def test_cancel_order_invalid_status(async_client: AsyncClient):
    prod = (await async_client.post("/api/products", json={"name": "PaidItem", "price": 30.0, "stock_quantity": 10})).json()

    co_res = await async_client.post("/api/orders", json={"items": [{"product_id": prod["id"], "quantity": 2}]})
    order_id = co_res.json()["id"]

    # Pay first
    await async_client.post(f"/api/orders/{order_id}/pay", json={"mock_status": "SUCCESS", "idempotency_key": "IDEM-PAID-01"})

    # Attempt to cancel paid order
    cancel_res = await async_client.post(f"/api/orders/{order_id}/cancel")
    assert cancel_res.status_code == 400
    assert "Cannot cancel order" in cancel_res.json()["detail"]
