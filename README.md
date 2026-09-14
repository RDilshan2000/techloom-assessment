# Production-Grade FastAPI POS & E-Commerce Systems

**Candidate Name:** Ramesh Dilshan Dissanayaka    
**Repository Name:** `techloom-assessment`

---

## 📌 Live Deployment Links

| Service / Resource | Access & Deployment Links |
| :--- | :--- |
| 👨‍💻 **Candidate Name** | **Ramesh Dilshan Dissanayaka**  |
| 📁 **GitHub Repository** | [https://github.com/RDilshan2000/techloom-assessment](https://github.com/RDilshan2000/techloom-assessment) |
| 🏬 **Task 01 Live URL (POS System)** | [https://techloom-pos-task01.onrender.com/](https://techloom-pos-task01.onrender.com/) |
| 🛒 **Task 02 Live URL (E-Commerce Storefront & Admin)** | [https://techloom-ecommerce-task02.onrender.com/](https://techloom-ecommerce-task02.onrender.com/) |

---

## 🚀 Key Feature Highlights

### 🏬 Task 01: High-Concurrency POS & Inventory System
- **High-Concurrency Transaction Handling**: Designed for point-of-sale operations with simultaneous multi-terminal order placements and payment authorizations.
- **Database-Level Pessimistic Row Locking (`SELECT ... FOR UPDATE`)**: Enforces explicit row locks during order creation and stock reservations inside ACID database transactions, guaranteeing **0 overselling** even under heavy concurrent traffic.
- **Automated Concurrency Stress Test Verification**: Includes dedicated unit and stress tests (`task-01/tests/test_concurrency.py`) simulating 20 parallel simultaneous order requests against a single inventory item to empirically prove lock safety.
- **Stock Hold & Expiration**: 5-minute automated inventory reservation TTL backed by an async background worker scanning every 10 seconds to auto-expire unpaid reservations and restore stock.
- **Payment Idempotency & Audit Trails**: Mandates `X-Idempotency-Key` headers to prevent double-billing and maintains automated restock audit log records.

### 🛒 Task 02: E-Commerce Storefront & Product Admin System
- **Customer Storefront**: Interactive responsive UI featuring seeded product catalog, multi-keyword live search, category pills, price range slider, in-stock filter toggle, slide-over cart drawer, and live 5-minute checkout countdown timer.
- **Dedicated Product & Inventory Admin Panel**: Full-featured admin interface (`#admin-view`) allowing store managers to publish new products (Name, Description, Price, Stock, Category, Image URL) and manage existing inventory with dynamic direct stock replenishment (`+ Add Qty`).
- **Mock Payment Gateway with Idempotency**: Interactive gateway supporting `SUCCESS`, `FAILURE`, and `TIMEOUT` simulation modes with automatic `X-Idempotency-Key` deduplication and instant catalog stock release on payment failure.
- **Automated 19 Passing Test Cases**: 100% passing test suite across `test_cleanup.py`, `test_orders.py`, `test_payments.py`, and `test_products.py`.

---

## 📁 Repository Structure

```
techloom-assessment/
├── README.md                      # Comprehensive root documentation (this file)
├── task-01/                       # Task 01: High-Concurrency POS System
│   ├── app/
│   │   ├── config.py              # Environment configuration loader
│   │   ├── database.py            # Async SQLAlchemy engine & connection pool
│   │   ├── models.py              # Product, Order, OrderItem, Transaction & Restock models
│   │   ├── schemas.py             # Pydantic v2 validation schemas
│   │   ├── crud.py                # CRUD operations with SELECT FOR UPDATE pessimistic locking
│   │   ├── background.py          # Automated background restock & expiry worker
│   │   ├── main.py                # FastAPI app entrypoint
│   │   └── routers/               # Products, Orders, Payments & Audit API routes
│   ├── static/                    # POS Dashboard UI (HTML, CSS, JS)
│   ├── tests/                     # Concurrency, locking & payment pytest suite
│   │   ├── test_concurrency.py    # 20-parallel-request race condition test suite
│   │   ├── test_orders.py         # Order reservation & expiration tests
│   │   ├── test_payments.py       # Payment idempotency tests
│   │   └── test_products.py       # Stock metrics & inventory tests
│   ├── requirements.txt           # Task 01 Python dependencies
│   └── README.md                  # Task 01 specific documentation
└── task-02/                       # Task 02: E-Commerce Storefront & Admin System
    ├── app/
    │   ├── config.py              # Configuration & TTL settings
    │   ├── database.py            # Async SQLAlchemy engine setup
    │   ├── models.py              # Product, Order, OrderItem & Payment models
    │   ├── schemas.py             # Pydantic validation schemas
    │   ├── background.py          # 5-minute stock reservation cleanup worker
    │   ├── main.py                # FastAPI app entrypoint & static mount
    │   ├── services/              # Product, Order & Payment domain business logic
    │   └── routers/               # Products, Orders & Payments API endpoints
    ├── static/                    # Storefront & Admin CSS and JS application logic (app.js)
    ├── templates/                 # Storefront & Admin HTML view layout (index.html)
    ├── tests/                     # 19 passing test cases (Admin, Checkout, Gateway, Expiry)
    │   ├── test_cleanup.py        # Expiration worker unit tests
    │   ├── test_orders.py         # Reservation & cancellation tests
    │   ├── test_payments.py       # Gateway simulation & refund tests
    │   └── test_products.py       # Catalog search, filter & admin API tests
    ├── requirements.txt           # Task 02 Python dependencies
    └── README.md                  # Task 02 specific documentation
```

---

## 🏬 Detailed Technical Architecture: Task 01 (POS System)

### 1. Concurrency & Race Condition Prevention
- **Pessimistic Row Locking (`SELECT FOR UPDATE`)**: During order creation, product rows are locked at the database level:
  ```python
  stmt = select(Product).where(Product.id == product_id).with_for_update()
  ```
  This locks the targeted inventory rows until the ACID transaction commits or rolls back, completely blocking concurrent transactions from over-committing inventory.
- **Zero Overselling Guarantee**: Stock validation and atomic decrement occur strictly inside the lock boundary. If requested stock exceeds available units, a `400 Bad Request` exception is thrown without mutating state.

### 2. Stock Reservation TTL & Background Cleanup
- **5-Minute Reservation**: Orders are created in `RESERVED` status with `reservation_expires_at = NOW() + 5 MINUTES`.
- **Background Cleanup Task**: An async worker scans for expired reservations every 10 seconds:
  ```python
  stmt = select(Order).where(Order.status == "RESERVED", Order.reservation_expires_at <= now)
  ```
  Expired orders transition to `EXPIRED` and reserved quantities are automatically restored to available stock.

### 3. Automated Concurrency Test Verification
Run the concurrency stress test suite simulating 20 parallel order requests against 20 units of stock:
```bash
python -m pytest task-01/tests/test_concurrency.py -v
```

---

## 🛒 Detailed Technical Architecture: Task 02 (E-Commerce Storefront & Admin)

### 1. Storefront UX & Product Discovery
- **Live Search & Multi-Attribute Filter**: Dynamic filtering by keyword, category selection pills, max price range slider, and an "In-Stock Only" toggle.
- **Stock Badges**: Visual indicators displaying live available stock, low-stock warnings, and out-of-stock badges.

### 2. Dedicated Product & Inventory Admin Panel
- **Add New Product Form**: Publish items directly to catalog with Name, Description, Price, Stock, Category, and optional Image URL.
- **Inventory Management Table**: Live tabular overview of all products displaying ID, Name, Category, Price, Available Stock, Reserved Stock, Total Stock, and direct `+ Add Qty` replenishment inputs.

### 3. Payment Gateway Simulation & Idempotency
- **Mock Payment Modes**: Interactive simulation supporting `SUCCESS` (locks sold stock), `FAILED` (releases reserved stock back to catalog), and `TIMEOUT` (keeps reservation active until 5-minute expiry).
- **Idempotency Protection**: Enforces unique `X-Idempotency-Key` tokens to return cached responses on repeated payments without duplicate charges.

### 4. Post-Purchase Lifecycle & Refunds
- **Order History View**: Track active reservations, paid orders, cancelled reservations, and refunded orders.
- **Order Refund Flow**: Customers can request refunds on `PAID` orders, transitioning status to `REFUNDED` and returning items to catalog stock.

---

## ⚙️ Local Setup & Running Instructions

### Step 1: Clone Repository
```bash
git clone https://github.com/RDilshan2000/techloom-assessment.git
cd techloom-assessment
```

---

### Step 2: Run Task 01 (POS System)
```bash
cd task-01
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --app-dir . --reload --port 8000
```
- **POS Dashboard UI:** `http://127.0.0.1:8000`
- **Swagger Docs:** `http://127.0.0.1:8000/docs`

---

### Step 3: Run Task 02 (E-Commerce Storefront & Admin)
```bash
cd task-02
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --app-dir . --reload --port 8001
```
- **Storefront & Admin UI:** `http://127.0.0.1:8001`
- **Swagger Docs:** `http://127.0.0.1:8001/docs`

---

### Step 4: Run Pytest Automation Suites

Run automated test suites from the root directory:

```bash
# Run Task 01 Test Suite (Concurrency, Locking, Payments)
python -m pytest task-01/tests -v

# Run Task 02 Test Suite (19 Passing Tests: Admin Panel, Checkout, Gateway, Expiration)
python -m pytest task-02/tests -v
```

---

## 📊 Evaluator Criteria Mapping

| Evaluation Criteria | Technical Implementation & Compliance | Location |
| :--- | :--- | :--- |
| **Concurrency & Lock Handling** | Implemented `SELECT FOR UPDATE` pessimistic row locking and atomic stock deductions inside ACID transactions, guaranteeing 0 overselling under parallel loads. | `task-01/app/crud.py`<br>`task-01/tests/test_concurrency.py` |
| **Stock Reservation & TTL** | 5-minute automated inventory reservation hold on checkout paired with a background async worker executing every 10 seconds to expire stale reservations and restore stock. | `task-01/app/background.py`<br>`task-02/app/background.py` |
| **Payment Handling & Gateway** | Full mock payment simulation supporting `SUCCESS`, `FAILURE`, and `TIMEOUT` scenarios with idempotent transaction logging using `X-Idempotency-Key` headers. | `task-01/app/routers/payments.py`<br>`task-02/app/services/payment_service.py` |
| **Order Lifecycle & Refunds** | End-to-end customer order history management, unpaid reservation cancellation, and paid order refund workflows with stock auto-restoration. | `task-02/app/services/order_service.py`<br>`task-02/static/js/app.js` |
| **Admin & Catalog Control** | Built-in Admin Management UI (`#admin-view`) to publish new products, adjust pricing, manage categories, and perform quick stock replenishment via `+ Add Qty` controls. | `task-02/templates/index.html`<br>`task-02/app/services/product_service.py` |
| **Data Integrity & DB Support** | Supports both production PostgreSQL (Aiven Cloud Managed DB) and SQLite with aiosqlite, with isolated table naming (`task01_` vs `task02_`) to prevent schema collisions. | `task-01/app/database.py`<br>`task-02/app/database.py` |
| **Automated Testing** | 100% pass rate across concurrency stress test suite (Task 01) and 19 automated Pytest test cases (Task 02). | `task-01/tests/`<br>`task-02/tests/` |

---

## 👨‍💻 Candidate Information

- **Name:** Ramesh Dilshan Dissanayaka
- **GitHub Repository:** [https://github.com/RDilshan2000/techloom-assessment](https://github.com/RDilshan2000/techloom-assessment)
- **Task 01 Live URL (POS System):** [https://techloom-pos-task01.onrender.com/](https://techloom-pos-task01.onrender.com/)
- **Task 02 Live URL (E-Commerce Storefront & Admin):** [https://techloom-ecommerce-task02.onrender.com/](https://techloom-ecommerce-task02.onrender.com/)
