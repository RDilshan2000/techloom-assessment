# POS Order & Inventory System (Task 01)

A high-performance, concurrency-safe POS (Point of Sale) Order & Inventory System built with **Python FastAPI**, **SQLAlchemy 2.0 (Async)**, **Pydantic v2**, and **SQLite / PostgreSQL**.

Designed with **pessimistic row-level locking (`SELECT ... FOR UPDATE`)**, ACID transaction guarantees, automatic 5-minute stock reservations, a background expiration worker, mock payment idempotency, and an interactive real-time dashboard.

---

## 🌟 Key Features

1. **Product & Real-Time Inventory Management**:
   - Complete CRUD endpoints for products (`id`, `name`, `price`, `stock_quantity`, `reserved_quantity`).
   - Real-time stock endpoint displaying available vs reserved vs total inventory levels.

2. **Concurrency-Safe Stock Reservation**:
   - Reserves product stock instantly upon order creation with a **5-minute expiration time**.
   - Uses **pessimistic row-level locking (`SELECT ... FOR UPDATE`)** inside ACID database transactions to prevent race conditions and guarantee **zero overselling** under high concurrent traffic.

3. **Automatic Expiration Background Worker**:
   - An asynchronous background cleanup task running every **30 seconds**.
   - Identifies unpaid orders with expired 5-minute reservation windows, automatically releases reserved stock back to the available inventory pool, and marks order statuses as `'EXPIRED'`.

4. **Mock Payment System with Idempotency**:
   - Endpoint `/api/orders/{id}/pay` accepting `mock_status` (`SUCCESS`, `FAILURE`, `TIMEOUT`) and a unique `idempotency_key`.
   - **`SUCCESS`**: Finalizes order to `'PAID'` state.
   - **`FAILURE` / `TIMEOUT`**: Restores reserved stock back to available pool and updates state to `'FAILED'` or `'EXPIRED'`.
   - Idempotency key tracking prevents duplicate payment processing.

5. **Order Lifecycle & State Machine**:
   - Enforces valid state transitions: `PENDING` -> `RESERVED` -> `PAID` / `EXPIRED` / `CANCELLED` / `FAILED`.
   - Supports manual order cancellation (`POST /api/orders/{id}/cancel`) with immediate stock restoration.

6. **Interactive Real-Time Dashboard**:
   - Sleek glassmorphism UI built with modern HTML5, Tailwind CSS, and JavaScript.
   - Real-time stock overview metrics, live 5-minute reservation countdown timers, product CRUD forms, POS checkout station, and a one-click payment simulator.

7. **Concurrency Test Suite**:
   - Built-in test script (`tests/test_concurrency.py`) using `asyncio` and `httpx.AsyncClient` to simulate **20 parallel requests** attempting to purchase 5 items each from a stock of 20.
   - Verifies exactly 4 orders succeed and 16 fail with zero overselling.

---

## 📁 Project Structure

```
task-01/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point & lifespan handlers
│   ├── config.py            # Environment configuration via Pydantic Settings
│   ├── database.py          # Async SQLAlchemy engine & session management
│   ├── models.py            # SQLAlchemy ORM models (Product, Order, OrderItem, PaymentRecord)
│   ├── schemas.py           # Pydantic schemas for request validation & responses
│   ├── crud.py              # Core business logic, pessimistic locking & transaction management
│   ├── background.py        # Async background worker for order expiration cleanup
│   └── routers/
│       ├── products.py      # Product CRUD & stock endpoints
│       ├── orders.py        # Order creation, reservation & cancellation endpoints
│       └── payments.py      # Mock payment & idempotency endpoints
├── static/
│   └── index.html           # Interactive frontend web dashboard
├── tests/
│   ├── __init__.py
│   └── test_concurrency.py  # Concurrency verification test script (asyncio + httpx)
├── .env.example             # Example environment variables file
├── requirements.txt         # Project dependencies
└── README.md                # Documentation
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### 2. Create Virtual Environment & Install Dependencies

```bash
# Navigate to project directory
cd task-01

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file (or copy `.env.example`):

```bash
cp .env.example .env
```

Default config (SQLite async fallback):
```env
DATABASE_URL=sqlite+aiosqlite:///./sql_app.db
RESERVATION_EXPIRATION_MINUTES=5
BACKGROUND_CLEANUP_INTERVAL_SECONDS=30
```

To switch to PostgreSQL, set:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/pos_db
```

---

## 🚀 Running the Application

Start the FastAPI web server using Uvicorn:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Once running, access:
- **Interactive Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **API Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Running Concurrency Verification Tests

To verify zero overselling under high concurrency (20 parallel requests purchasing 5 items each from stock = 20):

```bash
# Using pytest
python -m pytest tests/test_concurrency.py -v -s

# Or directly running the test script
python tests/test_concurrency.py
```

### Expected Output:
```text
[TEST] Launching 20 parallel purchase requests (5 units each)...
[TEST] Successful orders created: 4
[TEST] Failed orders (insufficient stock): 16
[TEST] Real-time Stock: Available=0, Reserved=20, Total=20
[TEST] SUCCESS: All concurrency, locking, payment, and stock restoration tests passed!
```

---

## 📡 API Reference

### 📦 Products & Inventory (`/api/products`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/products` | Create a new product |
| `GET` | `/api/products` | List all products with stock info |
| `GET` | `/api/products/{id}` | Get product by ID |
| `PUT` | `/api/products/{id}` | Update product details / stock |
| `DELETE` | `/api/products/{id}` | Delete a product |
| `GET` | `/api/products/{id}/stock` | Get real-time stock levels for product |
| `GET` | `/api/stock` | Get real-time stock levels across all products |

### 🛒 Orders (`/api/orders`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/orders` | Place order (reserves stock for 5 minutes) |
| `GET` | `/api/orders` | List all orders with status & expiration |
| `GET` | `/api/orders/{id}` | Get order details |
| `POST` | `/api/orders/{id}/cancel` | Cancel order and restore reserved stock |

### 💳 Payments (`/api/payments`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/orders/{id}/pay` | Process mock payment (`SUCCESS`, `FAILURE`, `TIMEOUT`) with `idempotency_key` |

---

## 🛡️ License

MIT License.
