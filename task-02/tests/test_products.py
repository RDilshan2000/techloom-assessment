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
