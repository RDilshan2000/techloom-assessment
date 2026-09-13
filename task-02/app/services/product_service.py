from typing import List, Optional
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Product

SAMPLE_PRODUCTS = [
    {
        "name": "Wireless Noise-Canceling Headphones",
        "description": "Premium over-ear headphones with active noise cancellation, 30-hour battery life, and spatial audio.",
        "category": "Electronics",
        "price": 249.99,
        "stock": 15,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80"
    },
    {
        "name": "Ultra-Wide Gaming Monitor 34\"",
        "description": "Curved 144Hz 1ms IPS gaming display with HDR400 and ultra-thin bezel.",
        "category": "Electronics",
        "price": 499.00,
        "stock": 8,
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&q=80"
    },
    {
        "name": "Mechanical RGB Keyboard",
        "description": "Hot-swappable tactile mechanical switches with per-key RGB backlighting and aluminum frame.",
        "category": "Electronics",
        "price": 119.50,
        "stock": 25,
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&q=80"
    },
    {
        "name": "Organic Cotton Hoodie",
        "description": "Ultra-soft heavy fleece hoodie made from 100% certified organic cotton.",
        "category": "Clothing",
        "price": 65.00,
        "stock": 40,
        "image_url": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=500&q=80"
    },
    {
        "name": "Classic Denim Jacket",
        "description": "Timeless vintage wash denim jacket with custom brass buttons and durable stitching.",
        "category": "Clothing",
        "price": 89.99,
        "stock": 20,
        "image_url": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=500&q=80"
    },
    {
        "name": "Minimalist Leather Backpack",
        "description": "Full-grain Italian leather laptop backpack featuring water-resistant lining.",
        "category": "Clothing",
        "price": 145.00,
        "stock": 12,
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&q=80"
    },
    {
        "name": "Clean Code & Architecture Manual",
        "description": "Definitive handbook on software design principles, refactoring, and enterprise patterns.",
        "category": "Books",
        "price": 42.99,
        "stock": 30,
        "image_url": "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=500&q=80"
    },
    {
        "name": "Designing Data-Intensive Applications",
        "description": "Essential guide to big data architectures, distributed systems, and reliability.",
        "category": "Books",
        "price": 49.95,
        "stock": 18,
        "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500&q=80"
    },
    {
        "name": "Ergonomic Mesh Office Chair",
        "description": "Adjustable lumbar support, breathable mesh, 3D armrests, and synchro-tilt mechanism.",
        "category": "Home",
        "price": 299.99,
        "stock": 10,
        "image_url": "https://images.unsplash.com/photo-1580481072645-022f9a6d83d0?w=500&q=80"
    },
    {
        "name": "Pour-Over Coffee Maker Set",
        "description": "Handblown borosilicate glass carafe with stainless steel reusable mesh filter.",
        "category": "Home",
        "price": 38.50,
        "stock": 50,
        "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500&q=80"
    },
    {
        "name": "Smart Fitness Watch",
        "description": "GPS activity tracker, heart rate monitor, sleep analysis, and 7-day battery life.",
        "category": "Fitness",
        "price": 179.00,
        "stock": 22,
        "image_url": "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=500&q=80"
    },
    {
        "name": "Adjustable Dumbbell Set 50lbs",
        "description": "Space-saving selector dumbbell system adjustable from 5 to 50 lbs with steel plates.",
        "category": "Fitness",
        "price": 219.00,
        "stock": 5,
        "image_url": "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=500&q=80"
    }
]

async def get_products(
    db: AsyncSession,
    search: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = False
) -> List[Product]:
    query = select(Product)

    conditions = []
    if search and search.strip():
        term = f"%{search.strip()}%"
        conditions.append(or_(Product.name.ilike(term), Product.description.ilike(term)))
    
    if category and category.strip() and category.strip().lower() != "all":
        conditions.append(Product.category.ilike(category.strip()))

    if min_price is not None:
        conditions.append(Product.price >= min_price)

    if max_price is not None:
        conditions.append(Product.price <= max_price)

    if in_stock_only:
        conditions.append(Product.stock > 0)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(Product.id.asc())
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_product(db: AsyncSession, product_id: int) -> Optional[Product]:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

async def seed_sample_products(db: AsyncSession) -> int:
    result = await db.execute(select(Product))
    existing = result.scalars().all()
    
    if existing:
        # Reset existing stock to sample values or keep clean
        return len(existing)

    for item in SAMPLE_PRODUCTS:
        prod = Product(
            name=item["name"],
            description=item["description"],
            category=item["category"],
            price=item["price"],
            stock=item["stock"],
            reserved_stock=0,
            image_url=item["image_url"]
        )
        db.add(prod)
    
    await db.commit()
    return len(SAMPLE_PRODUCTS)
