from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.routers import products, orders, payments
from app.services.product_service import seed_sample_products
from app.background import cleanup_worker

BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = (BASE_DIR / "static").resolve()
templates_dir = (BASE_DIR / "templates").resolve()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Ensure database tables exist
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"[Lifespan Error] Table creation failed: {e}")

    # 2. Seed products if table is empty
    try:
        async with AsyncSessionLocal() as db:
            await seed_sample_products(db)
    except Exception as e:
        print(f"[Lifespan Error] Product seeding failed: {e}")

    # 3. Start background cleanup worker
    try:
        cleanup_worker.start()
    except Exception as e:
        print(f"[Lifespan Error] Background worker start failed: {e}")

    yield

    # 4. Shutdown logic
    try:
        await cleanup_worker.stop()
    except Exception as e:
        print(f"[Lifespan Error] Background worker stop failed: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Section 02: E-Commerce Checkout & Payment System with Async SQLAlchemy, 5-Min Inventory Expiry & Idempotency",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files if directory exists
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(templates_dir))

# Include routers
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse, tags=["UI"])
async def render_storefront(request: Request):
    if request.method == "HEAD":
        return Response(status_code=200)
    
    try:
        index_file = templates_dir / "index.html"
        if index_file.exists():
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={"project_name": settings.PROJECT_NAME}
            )
        else:
            return HTMLResponse(
                content=f"<!DOCTYPE html><html><body><h1>{settings.PROJECT_NAME}</h1><p>Storefront UI operational.</p></body></html>",
                status_code=200
            )
    except Exception as e:
        # Fallback to clean HTML response instead of unhandled 500 error
        return HTMLResponse(
            content=f"<!DOCTYPE html><html><body><h1>{settings.PROJECT_NAME}</h1><p>Service Operational.</p></body></html>",
            status_code=200
        )

@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"])
async def health_check(request: Request):
    if request.method == "HEAD":
        return Response(status_code=200)
    return {"status": "ok", "project": settings.PROJECT_NAME}
