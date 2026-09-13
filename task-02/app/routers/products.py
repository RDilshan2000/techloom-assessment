from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import ProductRead, ProductCreate, ProductUpdate, AddStockRequest, SeedResponse
from app.services import product_service

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("", response_model=List[ProductRead])
async def list_products(
    search: Optional[str] = Query(None, description="Search by name or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    in_stock_only: bool = Query(False, description="Filter only products with available stock > 0"),
    db: AsyncSession = Depends(get_db)
):
    products = await product_service.get_products(
        db,
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only
    )
    return products

@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    return await product_service.create_product(
        db,
        name=data.name,
        category=data.category,
        price=data.price,
        stock=data.stock,
        description=data.description,
        image_url=data.image_url
    )

@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    product = await product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found."
        )
    return product

@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    product = await product_service.update_product(
        db,
        product_id,
        name=data.name,
        category=data.category,
        price=data.price,
        stock=data.stock,
        description=data.description,
        image_url=data.image_url
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found."
        )
    return product

@router.post("/{product_id}/stock", response_model=ProductRead)
async def add_product_stock(
    product_id: int,
    data: AddStockRequest,
    db: AsyncSession = Depends(get_db)
):
    product = await product_service.add_stock(db, product_id, data.quantity)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found."
        )
    return product

@router.post("/seed", response_model=SeedResponse)
async def seed_products(
    db: AsyncSession = Depends(get_db)
):
    count = await product_service.seed_sample_products(db)
    return SeedResponse(
        message="Products successfully seeded/verified.",
        product_count=count
    )
