# TechLoom Assessment - Production-Grade FastAPI POS & E-Commerce Systems

**Candidate Role:** Software Engineer Intern - Practical Assessment  
**Repository Name:** `techloom-assessment`

---

## 📌 Submission Links

| Service / Resource | Deployment & Access Links |
| :--- | :--- |
| 📁 **GitHub Repository** | [https://github.com/RDilshan2000/techloom-assessment](https://github.com/RDilshan2000/techloom-assessment) |
| 🏬 **Task 01 Live URL (POS System)** | [https://techloom-pos-task01.onrender.com/](https://techloom-pos-task01.onrender.com/) |
| 🛒 **Task 02 Live URL (E-Commerce Storefront)** | [https://techloom-ecommerce-task02.onrender.com/](https://techloom-ecommerce-task02.onrender.com/) |

---

## 🚀 Recent Key Highlights & Architectural Refinements

Recent engineering updates and improvements across both projects include:

### 1. Task 01: POS & High-Concurrency Inventory System
- **Database-Level Pessimistic Row Locking (`SELECT FOR UPDATE`)**: Enforced explicit row locking during order creation and stock reservations inside ACID transactions to guarantee zero overselling under heavy concurrent loads.
- **PostgreSQL & SQLite Dual Compatibility**: Configured normalized connection pooling with table isolation (`task01_` vs `task02_` table prefixes) enabling seamless operation on cloud PostgreSQL (Aiven Cloud) and SQLite in-memory development environments.
- **Idempotent Payment Processing**: Single-transaction idempotency validation using `X-Idempotency-Key` headers to eliminate duplicate billing and double stock deductions.
- **Automated Background Restocking**: Integrated background scheduler scanning low-stock items and appending audit trail records automatically.

### 2. Task 02: E-Commerce Storefront, Admin Panel & Gateway
- **Interactive Admin Management Panel**: Designed and integrated a dedicated Admin UI tab in the storefront interface to allow store administrators to create new products, adjust prices, edit categories, and quickly add stock quantities (`+ Add Qty`).
- **Admin REST API Endpoints**:
  - `POST /api/products`: Create new products with metadata & initial stock.
  - `PUT /api/products/{id}`: Edit existing product attributes.
  - `POST /api/products/{id}/stock`: Replenish product stock directly.
- **5-Minute Reservation TTL & Expiry Cleanup**: 300-second live countdown timer during checkout paired with an async background worker running every 10 seconds to auto-cancel expired reservations and restore reserved inventory.
- **Order Lifecycle & Refund System**: Complete customer post-purchase order history interface featuring order cancellation for unpaid holds and simulated instant refunds with catalog stock restoration for paid orders.
- **Comprehensive Pytest Suite**: 100% test coverage across catalog search, filtering, admin product creation, stock replenishment, payment idempotency, and background cleanup.

---

## 📁 Repository Structure

```
techloom-assessment/
├── README.md                      # Comprehensive root documentation (this file)
├── task-01/                       # Task 01: POS & Inventory System
│   ├── app/
│   │   ├── config.py              # App settings & environment loader
│   │   ├── database.py            # Async SQLAlchemy engine & PostgreSQL/SQLite setup
│   │   ├── models.py              # Product, Order, OrderItem, Transaction & Restock models
│   │   ├── schemas.py             # Pydantic validation schemas
│   │   ├── crud.py                # CRUD operations with SELECT FOR UPDATE locks
│   │   ├── background.py          # Automated restock background worker
│   │   ├── main.py                # FastAPI app entrypoint & static mount
│   │   └── routers/               # API routes (products, orders, payments, audit)
│   ├── static/                    # POS Admin Dashboard UI (HTML, CSS, Vanilla JS)
│   ├── tests/                     # Concurrency, lock & payment pytest suite
│   │   ├── test_concurrency.py    # Parallel 20-request race condition test
│   │   ├── test_orders.py         # Order lifecycle tests
│   │   ├── test_payments.py       # Payment idempotency tests
│   │   └── test_products.py       # Stock management & metrics tests
│   ├── requirements.txt           # Task 01 dependencies
│   └── README.md                  # Task 01 specific documentation
└── task-02/                       # Task 02: E-Commerce Storefront & Admin System
    ├── app/
    │   ├── config.py              # Configuration & TTL settings
    │   ├── database.py            # Async database connection setup
    │   ├── models.py              # Product, Order, OrderItem & Payment models
    │   ├── schemas.py             # Pydantic schemas (ProductUpdate, AddStockRequest)
    │   ├── background.py          # 5-minute reservation cleanup worker
    │   ├── main.py                # FastAPI entrypoint
    │   ├── services/              # Product, Order & Payment business logic
    │   └── routers/               # Products, Orders & Payments API endpoints
    ├── static/                    # Storefront & Admin CSS & JS application logic
    ├── templates/                 # Jinja2 storefront & admin UI template (index.html)
    ├── tests/                     # Admin operations, checkout, gateway & cleanup tests
    │   ├── test_cleanup.py        # Expiration worker unit tests
    │   ├── test_orders.py         # Stock reservation & cancellation tests
    │   ├── test_payments.py       # Payment gateway & refund tests
    │   └── test_products.py       # Catalog search, filter & admin tests
    ├── requirements.txt           # Task 02 dependencies
    └── README.md                  # Task 02 specific documentation
```

---

## 🏬 Task 01: POS Order & Inventory System

### 1. Concurrency & Race Condition Prevention
- **Pessimistic Row Locking (`SELECT FOR UPDATE`)**: When an order request is received, the system executes:
  ```python
  stmt = select(Product).where(Product.id == product_id).with_for_update()
  ```
  This locks the requested product row at the database level for the duration of the ACID transaction, blocking concurrent transactions from reading or mutating the row until committed.
- **Zero Overselling Guarantee**: Available stock is decremented and reserved stock is incremented inside the lock boundary. If requested quantity exceeds available stock, a `400 Bad Request` is returned without changing inventory state.

### 2. Stock Reservation TTL & Background Cleanup
- **5-Minute Reservation**: Created orders receive status `RESERVED` with `reservation_expires_at = NOW() + 5 MINUTES`.
- **Background Cleanup Task**: An async worker scans for expired `RESERVED` orders every 10 seconds:
  ```python
  stmt = select(Order).where(Order.status == "RESERVED", Order.reservation_expires_at <= now)
  ```
  Expired orders are updated to `EXPIRED` and reserved items are safely returned to available stock.

### 3. Mock Payment Handling & Idempotency
- **Payment States**: Supports `SUCCESS`, `FAILURE`, and `TIMEOUT` simulation modes.
- **Idempotency Deduplication**: Validates `X-Idempotency-Key` headers against `PaymentRecord` entities to return cached transaction results on repeated clicks or retries.

### 4. Automated Concurrency Test Verification
Run the concurrency stress test suite simulating 20 parallel order requests against 20 units of stock:
```bash
python -m pytest task-01/tests/test_concurrency.py -v
```

---

## 🛒 Task 02: E-Commerce Storefront & Payment System

### 1. Storefront UX & Product Discovery
- **Real-Time Multi-Attribute Search**: Instant client-side and server-side filtering by product name and description.
- **Category & Price Filtering**: Interactive category selection pills (Electronics, Apparel, Books, Home) paired with dynamic price range sliders and an "In-Stock Only" toggle.
- **Stock Indicators**: Real-time visual badges showing exact stock availability and low-stock alerts.

### 2. Cart, Checkout & Admin Inventory Management
- **Cart Management**: Add items, adjust quantities, view real-time subtotal calculations, and open checkout drawer.
- **5-Minute Inventory Hold**: Upon checkout, stock moves to `reserved_stock` and a 5-minute countdown timer displays on screen.
- **Admin Section Tab**:
  - **Create New Product**: Form to publish new items with category, price, stock, and image URL.
  - **Inventory Management Table**: Live view of stock allocations with one-click **`+ Add Qty`** modal to replenish stock without re-entering product data.

### 3. Payment Gateway Simulation & Idempotency Protection
- **Interactive Gateway Modal**: Select payment mode (`SUCCESS`, `FAILURE`, `TIMEOUT`) with automatic `X-Idempotency-Key` generation.
- **Double-Submission Prevention**: Disables action buttons during flight and verifies idempotency keys to prevent duplicate billing.

### 4. Customer Post-Purchase Flow
- **Order History View**: Displays current and historical orders with live status tags (`RESERVED`, `PAID`, `FAILED`, `CANCELLED`, `EXPIRED`).
- **Order Cancellation**: Unpaid `RESERVED` orders can be cancelled immediately, returning stock to the catalog.
- **Simulated Refunds**: Customers can request refunds for `PAID` orders, updating order status to `REFUNDED` and returning items to available stock.

---

## ⚙️ Local Setup & Testing Instructions

### Prerequisites
- Python 3.10+ installed on your machine.
- Git.

---

### Step 1: Clone Repository
```bash
git clone https://github.com/RDilshan2000/techloom-assessment.git
cd techloom-assessment
```

---

### Step 2: Running Task 01 (POS & Inventory System)

1. Open terminal and navigate to `task-01`:
   ```bash
   cd task-01
   ```
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Launch Uvicorn dev server:
   ```bash
   uvicorn app.main:app --app-dir . --reload --port 8000
   ```
5. Open browser:
   - **Dashboard UI:** `http://127.0.0.1:8000`
   - **Swagger OpenAPI Docs:** `http://127.0.0.1:8000/docs`

---

### Step 3: Running Task 02 (E-Commerce Storefront & Admin Panel)

1. Open a new terminal and navigate to `task-02`:
   ```bash
   cd task-02
   ```
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Launch Uvicorn dev server:
   ```bash
   uvicorn app.main:app --app-dir . --reload --port 8001
   ```
5. Open browser:
   - **Storefront & Admin UI:** `http://127.0.0.1:8001`
   - **Swagger OpenAPI Docs:** `http://127.0.0.1:8001/docs`

---

### Step 4: Running Automated Pytest Suites

Run test suites from the root repository folder:

```bash
# Run Task 01 Test Suite (Concurrency, Locking, Payments)
python -m pytest task-01/tests -v

# Run Task 02 Test Suite (Admin Panel, Checkout, Gateway, Expiration)
python -m pytest task-02/tests -v
```

---

## 📊 Evaluator Criteria Mapping

| Evaluation Criteria | Technical Implementation & Compliance | Task Location |
| :--- | :--- | :--- |
| **Concurrency & Lock Handling** | Implemented `SELECT FOR UPDATE` pessimistic row locking and atomic stock deductions inside ACID transactions, guaranteeing zero overselling under parallel loads. | `task-01/app/crud.py`<br>`task-01/tests/test_concurrency.py` |
| **Stock Reservation & TTL** | 5-minute automated inventory reservation hold on checkout paired with a background async worker executing every 10 seconds to expire stale reservations and restore stock. | `task-01/app/background.py`<br>`task-02/app/background.py` |
| **Payment Handling & Gateway** | Full mock payment simulation supporting `SUCCESS`, `FAILURE`, and `TIMEOUT` scenarios with idempotent transaction logging using `X-Idempotency-Key` headers. | `task-01/app/routers/payments.py`<br>`task-02/app/services/payment_service.py` |
| **Order Lifecycle & Refunds** | End-to-end customer order history management, unpaid reservation cancellation, and paid order refund workflows with stock auto-restoration. | `task-02/app/services/order_service.py`<br>`task-02/static/js/app.js` |
| **Admin & Catalog Control** | Built-in Admin Management UI to publish new products, adjust pricing, manage categories, and perform quick stock replenishment via `+ Add Qty` controls. | `task-02/templates/index.html`<br>`task-02/app/services/product_service.py` |
| **Data Integrity & DB Support** | Supports both production PostgreSQL (Aiven Cloud Managed DB) and SQLite with aiosqlite, with isolated table naming (`task01_` vs `task02_`) to prevent schema collisions. | `task-01/app/database.py`<br>`task-02/app/database.py` |
| **Code Quality & Architecture** | Modular Layered Architecture (Routers, Services, Schemas, Models), strict Pydantic v2 validation, 100% async Python FastAPI handlers, and automated pytest coverage. | Entire Codebase |

---

## 👨‍💻 Candidate Information

- **Name:** Ramesh Dilshan
- **Repository:** [`RDilshan2000/techloom-assessment`](https://github.com/RDilshan2000/techloom-assessment)
- **Task 01 Live Deployment:** [https://techloom-pos-task01.onrender.com/](https://techloom-pos-task01.onrender.com/)
- **Task 02 Live Deployment:** [https://techloom-ecommerce-task02.onrender.com/](https://techloom-ecommerce-task02.onrender.com/)
