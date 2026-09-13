# Section 02: E-Commerce Checkout & Payment System

A high-performance, asynchronous E-Commerce Storefront, Checkout & Payment Gateway system built with Python FastAPI, async SQLAlchemy, Pydantic v2, APScheduler/asyncio background worker, and a modern customer-facing Storefront UI.

---

## Key Features

1. **Product Discovery & Catalog**:
   - Seeded sample catalog across multiple categories (Electronics, Clothing, Books, Home, Fitness).
   - Live full-text search, category filter, dynamic price range filter, and stock availability toggle.
   - Detailed product view displaying real-time available stock vs. reserved stock.

2. **Cart & 5-Minute Inventory Reservation**:
   - Interactive slide-over shopping cart drawer with quantity validation against live stock limits.
   - Checkout flow creates an `Order` in `RESERVED` status and locks items immediately (`stock -= qty`, `reserved_stock += qty`).
   - 5-minute TTL per reservation with live countdown timer UI.
   - Background cleanup worker automatically releases expired reservations back to available stock.

3. **Mock Payment Gateway & Idempotency Protection**:
   - Interactive Payment Simulator with three simulation modes:
     - **SUCCESS**: Marks order `PAID`, finalizes sold inventory.
     - **FAILURE**: Marks order `FAILED`, immediately restores reserved stock.
     - **TIMEOUT**: Simulates gateway hang, order remains reserved until the 5-minute expiry worker releases stock.
   - Mandated **Idempotency Key** (`X-Idempotency-Key` / payload) preventing duplicate charges on double-clicks or retries.

4. **Post-Purchase & Complete Order Lifecycle**:
   - Order History dashboard with live status indicators (`RESERVED`, `PAID`, `FAILED`, `EXPIRED`, `CANCELLED`, `REFUNDED`).
   - Order Cancellation for active pending reservations (restores stock).
   - Order Refund for paid orders (returns sold inventory back into available catalog stock).

---

## Tech Stack & Architecture

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Database ORM**: [SQLAlchemy 2.0 (Async)](https://www.sqlalchemy.org/)
- **Database Driver**: `aiosqlite` (SQLite default) / `asyncpg` (PostgreSQL via `DATABASE_URL`)
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/latest/) & `pydantic-settings`
- **Frontend Stack**: Single lightweight service utilizing FastAPI StaticFiles and Jinja2 templates, Tailwind CSS CDN, FontAwesome 6, and Vanilla JS.
- **Testing**: `pytest` & `pytest-asyncio` with `httpx.AsyncClient`

---

## Project Structure

```
task-02/
├── app/
│   ├── __init__.py
│   ├── config.py           # App configuration & settings
│   ├── database.py         # Async engine & sessionmaker
│   ├── models.py           # Product, Order, OrderItem, PaymentTransaction models
│   ├── schemas.py          # Pydantic request/response schemas
│   ├── background.py       # Expiration cleanup background worker
│   ├── main.py             # FastAPI app entrypoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── product_service.py # Catalog querying & seeding
│   │   ├── order_service.py   # Reservation, expiry & lifecycle logic
│   │   └── payment_service.py # Mock payment gateway & idempotency
│   └── routers/
│       ├── __init__.py
│       ├── products.py     # Product API endpoints
│       ├── orders.py       # Order & Checkout API endpoints
│       └── payments.py     # Payment gateway API endpoints
├── static/
│   ├── css/styles.css      # Glassmorphic Tailwind styling
│   └── js/app.js           # Frontend application & payment simulator logic
├── templates/
│   └── index.html          # Main storefront Jinja2 template
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures & async DB setup
│   ├── test_products.py    # Catalog & search tests
│   ├── test_orders.py      # Checkout & reservation tests
│   ├── test_payments.py    # Gateway & idempotency tests
│   └── test_cleanup.py     # Expiry worker tests
├── requirements.txt
└── README.md
```

---

## Setup & Running Instructions

### 1. Install Dependencies

Ensure Python 3.10+ is installed, then run:

```bash
pip install -r task-02/requirements.txt
```

### 2. Launch Development Server

Start the FastAPI application with Uvicorn:

```bash
uvicorn app.main:app --app-dir task-02 --reload --port 8000
```

### 3. Open Storefront UI

Open your web browser and navigate to:
`http://127.0.0.1:8000`

Interactive OpenAPI Documentation (Swagger UI) is available at:
`http://127.0.0.1:8000/docs`

---

## API Endpoints Reference

### Products API (`/api/products`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/products` | Query products with filters (`search`, `category`, `min_price`, `max_price`, `in_stock_only`) |
| `GET` | `/api/products/{id}` | Retrieve detailed information for a single product |
| `POST` | `/api/products/seed` | Reset/re-seed sample product inventory |

### Orders & Checkout API (`/api/orders`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/orders/checkout` | Create order & reserve inventory with a 5-minute expiration timer |
| `GET` | `/api/orders` | List orders (filterable by `status` or `email`) |
| `GET` | `/api/orders/{id}` | Retrieve single order with remaining reservation countdown seconds |
| `POST` | `/api/orders/{id}/cancel` | Cancel pending `RESERVED` order and restore reserved stock |
| `POST` | `/api/orders/{id}/refund` | Refund `PAID` order and restore sold items to inventory |

### Payments API (`/api/orders/{id}/pay`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/orders/{id}/pay` | Process payment (`SUCCESS`, `FAILED`, `TIMEOUT`) using Idempotency Key |

---

## Running Automated Tests

Run the complete pytest test suite:

```bash
python -m pytest task-02/tests/ -v
```
