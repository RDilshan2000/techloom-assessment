import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_products(async_client: AsyncClient):
    response = await async_client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.asyncio
async def test_search_products(async_client: AsyncClient):
    response = await async_client.get("/api/products?search=Headphones")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Headphones" in data[0]["name"]

@pytest.mark.asyncio
async def test_category_filter(async_client: AsyncClient):
    response = await async_client.get("/api/products?category=Electronics")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for product in data:
        assert product["category"].lower() == "electronics"

@pytest.mark.asyncio
async def test_price_filter(async_client: AsyncClient):
    response = await async_client.get("/api/products?min_price=50&max_price=150")
    assert response.status_code == 200
    data = response.json()
    for product in data:
        assert 50 <= product["price"] <= 150

@pytest.mark.asyncio
async def test_get_product_by_id(async_client: AsyncClient):
    # First get product list to grab valid ID
    list_res = await async_client.get("/api/products")
    prod_id = list_res.json()[0]["id"]

    res = await async_client.get(f"/api/products/{prod_id}")
    assert res.status_code == 200
    assert res.json()["id"] == prod_id

@pytest.mark.asyncio
async def test_get_product_not_found(async_client: AsyncClient):
    res = await async_client.get("/api/products/999999")
    assert res.status_code == 404

@pytest.mark.asyncio
async def test_root_endpoint_get_and_head(async_client: AsyncClient):
    res_get = await async_client.get("/")
    assert res_get.status_code == 200

    res_head = await async_client.head("/")
    assert res_head.status_code == 200

@pytest.mark.asyncio
async def test_health_endpoint_get_and_head(async_client: AsyncClient):
    res_get = await async_client.get("/health")
    assert res_get.status_code == 200
    assert res_get.json()["status"] == "ok"

    res_head = await async_client.head("/health")
    assert res_head.status_code == 200

@pytest.mark.asyncio
async def test_create_product_admin(async_client: AsyncClient):
    payload = {
        "name": "Admin Gaming Mouse",
        "description": "Ergonomic wireless gaming mouse with 20K DPI sensor",
        "category": "Electronics",
        "price": 79.99,
        "stock": 30,
        "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&q=80"
    }
    res = await async_client.post("/api/products", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Admin Gaming Mouse"
    assert data["price"] == 79.99
    assert data["stock"] == 30

@pytest.mark.asyncio
async def test_add_stock_admin(async_client: AsyncClient):
    list_res = await async_client.get("/api/products")
    prod = list_res.json()[0]
    original_stock = prod["stock"]

    res = await async_client.post(f"/api/products/{prod['id']}/stock", json={"quantity": 15})
    assert res.status_code == 200
    data = res.json()
    assert data["stock"] == original_stock + 15


