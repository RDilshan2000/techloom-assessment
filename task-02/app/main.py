import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.routers import products, orders, payments
from app.services.product_service import seed_sample_products
from app.background import cleanup_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed products
    async with AsyncSessionLocal() as db:
        await seed_sample_products(db)

    # Start background cleanup task
    cleanup_worker.start()

    yield

    # Shutdown logic
    await cleanup_worker.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Section 02: E-Commerce Checkout & Payment System with Async SQLAlchemy, 5-Min Inventory Expiry & Idempotency",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files & templates
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Include routers
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)

@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def render_storefront(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "project_name": settings.PROJECT_NAME})

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}
