import asyncio
import os
import sys
import pytest
from httpx import AsyncClient

# Ensure app package is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.mark.asyncio
async def test_concurrency_zero_overselling(async_client: AsyncClient):
    """
    Simulates 20 parallel requests attempting to buy 5 items each (total requested = 100 units)
    from a product with only 20 units in stock.
    Verifies that pessimistic row locking guarantees zero overselling (exactly 4 success, 16 failure).
    """
    # 1. Seed product with stock = 20
    create_res = await async_client.post(
        "/api/products",
        json={"name": "Limited Edition Watch", "price": 199.99, "stock_quantity": 20}
    )
    assert create_res.status_code == 201, f"Failed to create product: {create_res.text}"
    product_data = create_res.json()
    product_id = product_data["id"]
    assert product_data["stock_quantity"] == 20

    # 2. Simulate 20 concurrent order placement requests
    async def place_order(client: AsyncClient, prod_id: int, qty: int):
        return await client.post(
            "/api/orders",
            json={"items": [{"product_id": prod_id, "quantity": qty}]}
        )

    print("\n[TEST] Launching 20 parallel purchase requests (5 units each)...")
    tasks = [place_order(async_client, product_id, 5) for _ in range(20)]
    responses = await asyncio.gather(*tasks)

    # 3. Count success and failure responses
    successful_orders = [r for r in responses if r.status_code == 201]
    failed_orders = [r for r in responses if r.status_code == 400]

    print(f"[TEST] Successful orders created: {len(successful_orders)}")
    print(f"[TEST] Failed orders (insufficient stock): {len(failed_orders)}")

    # 4. Assertions for zero overselling
    assert len(successful_orders) == 4, f"Expected 4 successful orders, got {len(successful_orders)}"
    assert len(failed_orders) == 16, f"Expected 16 failed orders, got {len(failed_orders)}"

    # 5. Verify real-time stock levels
    stock_res = await async_client.get(f"/api/products/{product_id}/stock")
    assert stock_res.status_code == 200
    stock_data = stock_res.json()

    print(f"[TEST] Real-time Stock: Available={stock_data['available_stock']}, Reserved={stock_data['reserved_stock']}, Total={stock_data['total_stock']}")
    assert stock_data["available_stock"] == 0
    assert stock_data["reserved_stock"] == 20
    assert stock_data["total_stock"] == 20

    # 6. Test Payment SUCCESS on first order
    first_order_id = successful_orders[0].json()["id"]
    pay_res = await async_client.post(
        f"/api/orders/{first_order_id}/pay",
        json={"mock_status": "SUCCESS", "idempotency_key": f"test_key_{first_order_id}"}
    )
    assert pay_res.status_code == 200
    assert pay_res.json()["order_status"] == "PAID"

    # Verify idempotency retry with same key
    retry_pay = await async_client.post(
        f"/api/orders/{first_order_id}/pay",
        json={"mock_status": "SUCCESS", "idempotency_key": f"test_key_{first_order_id}"}
    )
    assert retry_pay.status_code == 200
    assert retry_pay.json()["idempotency_key"] == f"test_key_{first_order_id}"

    # 7. Test Order Cancellation on second order to verify stock release
    second_order_id = successful_orders[1].json()["id"]
    cancel_res = await async_client.post(f"/api/orders/{second_order_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Check stock after cancellation: 5 units should return to available stock
    stock_after_cancel = await async_client.get(f"/api/products/{product_id}/stock")
    assert stock_after_cancel.json()["available_stock"] == 5
    assert stock_after_cancel.json()["reserved_stock"] == 10

    print("[TEST] SUCCESS: All concurrency, locking, payment, and stock restoration tests passed!")
