from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import ProductCreate, ProductUpdate, ProductResponse, RealtimeStockResponse
from app import crud

router = APIRouter()

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product_endpoint(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Create a new product with initial stock."""
    return await crud.create_product(db, product_in)

@router.get("/products", response_model=List[ProductResponse])
async def list_products_endpoint(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List all products with stock and reserved quantities."""
    return await crud.list_products(db, skip=skip, limit=limit)

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_endpoint(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get details of a specific product."""
    product = await crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product ID {product_id} not found.")
    return product

@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product_endpoint(product_id: int, product_in: ProductUpdate, db: AsyncSession = Depends(get_db)):
    """Update product details or stock level."""
    product = await crud.update_product(db, product_id, product_in)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product ID {product_id} not found.")
    return product

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_endpoint(product_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a product."""
    success = await crud.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product ID {product_id} not found.")
    return None

@router.get("/products/{product_id}/stock", response_model=RealtimeStockResponse)
async def get_product_realtime_stock_endpoint(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get real-time stock levels (available vs reserved vs total) for a specific product."""
    product = await crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product ID {product_id} not found.")
    return RealtimeStockResponse(
        product_id=product.id,
        name=product.name,
        available_stock=product.stock_quantity,
        reserved_stock=product.reserved_quantity,
        total_stock=product.stock_quantity + product.reserved_quantity
    )

@router.get("/stock", response_model=List[RealtimeStockResponse])
async def list_all_realtime_stock_endpoint(db: AsyncSession = Depends(get_db)):
    """Get real-time stock levels across all products."""
    products = await crud.list_products(db, skip=0, limit=1000)
    return [
        RealtimeStockResponse(
            product_id=p.id,
            name=p.name,
            available_stock=p.stock_quantity,
            reserved_stock=p.reserved_quantity,
            total_stock=p.stock_quantity + p.reserved_quantity
        )
        for p in products
    ]
