import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_product_valid(async_client: AsyncClient):
    payload = {
        "name": "Barcode Scanner Terminal",
        "price": 249.99,
        "stock_quantity": 50
    }
    response = await async_client.post("/api/products", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Barcode Scanner Terminal"
    assert data["price"] == 249.99
    assert data["stock_quantity"] == 50
    assert data["reserved_quantity"] == 0
    assert "id" in data

@pytest.mark.asyncio
async def test_create_product_invalid_validation(async_client: AsyncClient):
    # Negative price
    res1 = await async_client.post("/api/products", json={"name": "Bad Price", "price": -10.0, "stock_quantity": 5})
    assert res1.status_code == 422

    # Negative stock
    res2 = await async_client.post("/api/products", json={"name": "Bad Stock", "price": 10.0, "stock_quantity": -5})
    assert res2.status_code == 422

@pytest.mark.asyncio
async def test_list_products(async_client: AsyncClient):
    await async_client.post("/api/products", json={"name": "P1", "price": 10.0, "stock_quantity": 5})
    await async_client.post("/api/products", json={"name": "P2", "price": 20.0, "stock_quantity": 15})

    response = await async_client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

@pytest.mark.asyncio
async def test_get_product_by_id(async_client: AsyncClient):
    create_res = await async_client.post("/api/products", json={"name": "Target Product", "price": 99.0, "stock_quantity": 30})
    prod_id = create_res.json()["id"]

    response = await async_client.get(f"/api/products/{prod_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Target Product"

@pytest.mark.asyncio
async def test_get_product_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/products/999999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_product(async_client: AsyncClient):
    create_res = await async_client.post("/api/products", json={"name": "Old Name", "price": 50.0, "stock_quantity": 10})
    prod_id = create_res.json()["id"]

    update_res = await async_client.put(f"/api/products/{prod_id}", json={"name": "New Name", "price": 75.0, "stock_quantity": 25})
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["name"] == "New Name"
    assert data["price"] == 75.0
    assert data["stock_quantity"] == 25

@pytest.mark.asyncio
async def test_update_product_not_found(async_client: AsyncClient):
    response = await async_client.put("/api/products/999999", json={"price": 50.0})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_product(async_client: AsyncClient):
    create_res = await async_client.post("/api/products", json={"name": "ToDelete", "price": 10.0, "stock_quantity": 5})
    prod_id = create_res.json()["id"]

    del_res = await async_client.delete(f"/api/products/{prod_id}")
    assert del_res.status_code == 204

    get_res = await async_client.get(f"/api/products/{prod_id}")
    assert get_res.status_code == 404

@pytest.mark.asyncio
async def test_get_product_stock_metrics(async_client: AsyncClient):
    create_res = await async_client.post("/api/products", json={"name": "StockTest", "price": 100.0, "stock_quantity": 30})
    prod_id = create_res.json()["id"]

    # Reserve 5 units via order
    await async_client.post("/api/orders", json={"items": [{"product_id": prod_id, "quantity": 5}]})

    response = await async_client.get(f"/api/products/{prod_id}/stock")
    assert response.status_code == 200
    stock_data = response.json()
    assert stock_data["available_stock"] == 25
    assert stock_data["reserved_stock"] == 5
    assert stock_data["total_stock"] == 30

@pytest.mark.asyncio
async def test_stock_summary_across_catalog(async_client: AsyncClient):
    await async_client.post("/api/products", json={"name": "Cat1", "price": 10.0, "stock_quantity": 10})
    await async_client.post("/api/products", json={"name": "Cat2", "price": 20.0, "stock_quantity": 20})

    response = await async_client.get("/api/stock")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    for item in data:
        assert "available_stock" in item
        assert "reserved_stock" in item
        assert "total_stock" in item
