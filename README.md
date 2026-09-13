# TechLoom Assessment - Production-Grade FastAPI E-Commerce & Inventory System

**Candidate Role:** Software Engineer Intern - Practical Assessment  
**Repository Name:** `techloom-assessment`

---

## 📌 Submission Links

- **GitHub Repository:** `[INSERT_YOUR_GITHUB_REPO_URL_HERE]`
- **Task 01 Live URL (Concurrently-Safe Inventory Management):** `[INSERT_TASK_01_LIVE_URL_HERE]`
- **Task 02 Live URL (E-Commerce Checkout & Payment Gateway System):** `[INSERT_TASK_02_LIVE_URL_HERE]`

---

## 🚀 Overview

This repository contains the complete implementation for the TechLoom Technical Assessment, divided into two sections:

1. **Task 01: High-Concurrency Inventory Management System (`./task-01`)**  
   Focuses on robust backend API endpoints for inventory control, handling race conditions, high concurrent stock deductions, pessimistic locking (`FOR UPDATE`), low-stock alerts, auto-restocking, and audit logs.

2. **Task 02: E-Commerce Checkout & Payment Gateway System (`./task-02`)**  
   A customer-facing storefront web app (FastAPI + Jinja2 + Tailwind CSS + Vanilla JS) featuring live search, filtering, 5-minute stock reservation TTLs, background expiration cleanup, mock payment gateway simulation (`SUCCESS`, `FAILURE`, `TIMEOUT`), idempotency key validation, and post-purchase lifecycle management.

---

## 🛠️ Technology Stack

- **Backend Framework:** Python FastAPI (async/await paradigm)
- **Database ORM:** SQLAlchemy 2.0 (Async Engine & Sessionmaker)
- **Database Storage:** SQLite with `aiosqlite` (Default lightweight zero-config DB), fully compatible with PostgreSQL (`asyncpg`) via `DATABASE_URL` configuration.
- **Data Validation & Settings:** Pydantic v2 & `pydantic-settings`
- **Frontend UI:** Single lightweight service using FastAPI StaticFiles / Jinja2 Templates, Tailwind CSS CDN, FontAwesome 6, and Vanilla JavaScript.
- **Testing Framework:** `pytest` & `pytest-asyncio` with `httpx.AsyncClient`

---

## 📁 Repository Structure

```
techloom-assessment/
├── README.md                  # Comprehensive root documentation (this file)
├── task-01/                   # Task 01: High-Concurrency Inventory Management
│   ├── app/
│   │   ├── config.py          # App settings & environment loader
│   │   ├── database.py        # Async SQLAlchemy engine setup
│   │   ├── models.py          # Inventory, Transaction & Restock models
│   │   ├── schemas.py         # Pydantic validation schemas
│   │   ├── crud.py            # CRUD operations with SELECT FOR UPDATE locks
│   │   ├── background.py      # Automated restock background worker
│   │   ├── main.py            # FastAPI entrypoint
│   │   └── routers/           # API routes (inventory, audit logs, auto-restock)
│   ├── static/                # Admin Dashboard UI
│   ├── tests/                 # Concurrency & race condition pytest suite
│   ├── requirements.txt
│   └── README.md              # Task 01 specific documentation
└── task-02/                   # Task 02: E-Commerce Checkout & Payment System
    ├── app/
    │   ├── config.py          # Task 02 configuration settings
    │   ├── database.py        # Async database setup
    │   ├── models.py          # Product, Order, OrderItem & Payment models
    │   ├── schemas.py         # Pydantic schemas
    │   ├── background.py      # 5-minute reservation cleanup worker
    │   ├── main.py            # Storefront FastAPI application
    │   ├── services/          # Product, Order & Payment business logic
    │   └── routers/           # Product, Order & Payment routes
    ├── static/                # Storefront CSS & JS app logic
    ├── templates/             # Jinja2 storefront HTML UI template
    ├── tests/                 # Checkout, payment & idempotency pytest suite
    ├── requirements.txt
    └── README.md              # Task 02 specific documentation
```

---

## ⚙️ Quick Start & Local Run Instructions

### Prerequisites
- Python 3.10+ installed on system.

---

### Running Task 01: Inventory Management System

1. Navigate to `task-01`:
   ```bash
   cd task-01
   ```
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch server:
   ```bash
   uvicorn app.main:app --app-dir . --reload --port 8000
   ```
4. Access App & Docs:
   - Admin UI: `http://127.0.0.1:8000`
   - Swagger API Docs: `http://127.0.0.1:8000/docs`

---

### Running Task 02: E-Commerce Checkout & Payment System

1. Open a terminal and navigate to `task-02`:
   ```bash
   cd task-02
   ```
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch server:
   ```bash
   uvicorn app.main:app --app-dir . --reload --port 8001
   ```
4. Access Storefront & Docs:
   - Storefront UI: `http://127.0.0.1:8001`
   - Swagger API Docs: `http://127.0.0.1:8001/docs`

---

### Running Automated Test Suites

- **Task 01 Tests (Concurrency & Lock verification):**
  ```bash
  python -m pytest task-01/tests -v
  ```
- **Task 02 Tests (Checkout, Idempotency & Cleanup verification):**
  ```bash
  python -m pytest task-02/tests -v
  ```

---

## 🔒 Concurrency & Stock Locking Architecture (Task 01)

### The Challenge
In high-throughput e-commerce systems, multiple customers may attempt to purchase limited stock simultaneously. Naive read-then-write logic creates race conditions where multiple requests read positive stock before any deduction is committed, leading to negative inventory (overselling).

### Our Solution
1. **Pessimistic Database Locking (`SELECT FOR UPDATE`)**:
   When processing inventory deductions or reservations, queries acquire a pessimistic write lock on the specific `Product` row:
   ```python
   stmt = select(Product).where(Product.id == product_id).with_for_update()
   ```
2. **ACID Transaction Boundaries**:
   Stock verification, deduction, and audit log entries occur within a single atomic database transaction. If stock is insufficient, the transaction immediately rolls back without side effects.
3. **Atomic Inventory Accounting**:
   Available stock vs. reserved stock is updated atomically (`stock = stock - qty`, `reserved_stock = reserved_stock + qty`), guaranteeing zero overselling even under heavy concurrent load.

---

## ⏳ 5-Minute Inventory Reservation & Expiry Worker (Task 02)

1. **Reservation TTL**:
   When a user clicks "Proceed to Checkout", an `Order` is created in `RESERVED` status with an `expires_at` timestamp set to `datetime.now(utc) + 5 minutes`.
2. **Stock Holding**:
   Items requested are moved from available stock (`product.stock`) into `product.reserved_stock`. Other customers immediately see reduced available stock, preventing overbooking.
3. **Background Cleanup Worker**:
   An async background worker runs every 10 seconds. It scans for unpaid `RESERVED` orders whose `expires_at` timestamp has passed:
   - Updates order status to `EXPIRED`.
   - Restores reserved stock back to `product.stock`.

---

## 💳 Mock Payment Gateway & Idempotency Protection (Task 02)

### Payment Actions
The payment endpoint `POST /api/orders/{id}/pay` accepts three simulation actions:
- **`SUCCESS`**: Payment completes. Order status becomes `PAID`. `reserved_stock` is cleared and inventory deduction is finalized.
- **`FAILED`**: Payment authorization fails. Order status becomes `FAILED`. Reserved inventory is immediately released back to available stock.
- **`TIMEOUT`**: Simulates a network/gateway hang. Order remains `RESERVED` until the 5-minute background worker releases stock.

### Idempotency Keys (`X-Idempotency-Key`)
To prevent duplicate billing or double inventory deductions on repeated clicks or network retries:
1. Every payment request includes an `idempotency_key` (header or JSON body).
2. The payment service checks if a `PaymentTransaction` with that key exists.
3. If found, it returns the cached transaction response immediately with `cached: true` without re-processing the payment or mutating stock.

---

## 🧪 Evaluator Step-by-Step Testing Guide

### Testing Task 01 (Inventory Management)
1. Open `http://127.0.0.1:8000` to view the Inventory Dashboard.
2. Trigger inventory deductions via UI or API (`POST /api/inventory/deduct`).
3. Set product stock below threshold (e.g. < 5) to observe low-stock warning badges.
4. Test automated restocking background worker or manual trigger (`POST /api/inventory/restock`).
5. Run `python -m pytest task-01/tests` to verify concurrent request isolation under load.

### Testing Task 02 (E-Commerce Storefront & Gateway)
1. Open `http://127.0.0.1:8001` to view the Storefront UI.
2. Use the live search bar, category pills (e.g., Electronics, Clothing), price range slider, and "In Stock Only" toggle.
3. Add items to the cart and click "Proceed to Checkout".
4. Enter customer details and submit. Observe the **5-minute live reservation timer** ticking down.
5. In the Payment Simulator Modal:
   - Click **Simulate SUCCESS**: Verify order turns `PAID` and stock remains deducted.
   - Or click **Simulate FAILURE**: Verify order turns `FAILED` and items return to available stock.
   - Or click **Simulate TIMEOUT**: Observe timer tick down to `00:00` and background worker release stock.
6. Test Idempotency: Submit payment, copy the generated idempotency key, and submit again to see the `Idempotency Cache Hit` badge.
7. Order History & Refunds: Click "Order History" tab, view past orders, cancel pending reservations, or click "Request Refund" on a paid order to watch stock return to the catalog!
