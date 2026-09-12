import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.background import expire_unpaid_orders
from app.routers import products, orders, payments

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start background cleanup worker
    bg_task = asyncio.create_task(expire_unpaid_orders())
    
    yield
    
    # Shutdown: Cancel background cleanup worker
    bg_task.cancel()
    try:
        await bg_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="POS Order & Inventory System",
    description="Concurrency-Safe POS API with stock reservation, payment idempotency, and automatic background cleanup.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(products.router, prefix="/api", tags=["Products & Inventory"])
app.include_router(orders.router, prefix="/api", tags=["Orders"])
app.include_router(payments.router, prefix="/api", tags=["Payments"])

# Static UI Dashboard
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return "<h1>POS Order & Inventory System API is running!</h1>"
