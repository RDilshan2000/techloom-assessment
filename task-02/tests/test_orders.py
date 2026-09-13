import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_checkout_reserves_stock(async_client: AsyncClient):
    # Fetch first product
    prod_res = await async_client.get("/api/products")
    product = prod_res.json()[0]
    initial_stock = product["stock"]
    initial_reserved = product["reserved_stock"]

    checkout_payload = {
        "customer_name": "Alice Tester",
        "customer_email": "alice@example.com",
        "items": [
            {"product_id": product["id"], "quantity": 2}
        ]
    }

    res = await async_client.post("/api/orders/checkout", json=checkout_payload)
    assert res.status_code == 201
    order = res.json()
    assert order["status"] == "RESERVED"
    assert order["seconds_remaining"] > 0
    assert order["total_amount"] == round(product["price"] * 2, 2)

    # Verify inventory was updated
    prod_res_after = await async_client.get(f"/api/products/{product['id']}")
    product_after = prod_res_after.json()
    assert product_after["stock"] == initial_stock - 2
    assert product_after["reserved_stock"] == initial_reserved + 2

@pytest.mark.asyncio
async def test_checkout_insufficient_stock(async_client: AsyncClient):
    prod_res = await async_client.get("/api/products")
    product = prod_res.json()[0]

    checkout_payload = {
        "customer_name": "Bob Tester",
        "customer_email": "bob@example.com",
        "items": [
            {"product_id": product["id"], "quantity": 9999}
        ]
    }

    res = await async_client.post("/api/orders/checkout", json=checkout_payload)
    assert res.status_code == 400
    assert "Insufficient stock" in res.json()["detail"]

@pytest.mark.asyncio
async def test_cancel_reserved_order(async_client: AsyncClient):
    prod_res = await async_client.get("/api/products")
    product = prod_res.json()[0]
    initial_stock = product["stock"]

    # Checkout 1 item
    checkout_res = await async_client.post("/api/orders/checkout", json={
        "customer_name": "Charlie",
        "customer_email": "charlie@example.com",
        "items": [{"product_id": product["id"], "quantity": 1}]
    })
    order_id = checkout_res.json()["id"]

    # Cancel order
    cancel_res = await async_client.post(f"/api/orders/{order_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Verify stock restored
    prod_after = (await async_client.get(f"/api/products/{product['id']}")).json()
    assert prod_after["stock"] == initial_stock
