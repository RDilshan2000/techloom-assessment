# Task 02: E-Commerce Storefront & Payment System
## Comprehensive Test Case Specifications

---

### Overview
This document defines the complete test case suite for **Task 02 (E-Commerce Storefront & Payment Gateway System)**. The suite validates product discovery, search and filtering, 5-minute stock reservation, background expiration worker, mock payment simulation, idempotency caching, post-purchase refunds/cancellations, and system health endpoints.

---

## 1. Product Catalog, Search & Filtering

### TC-201: List All Products
- **Objective:** Fetch all seeded storefront products.
- **Input:** `GET /api/products`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Array of product objects containing `id`, `name`, `description`, `category`, `price`, `stock`, `reserved_stock`, `total_stock`, `image_url`.

### TC-202: Full-Text Keyword Search
- **Objective:** Filter catalog products by search query matching name or description.
- **Input:** `GET /api/products?search=Headphones`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Returned array contains only products where name or description includes `"Headphones"`.

### TC-203: Category Filtering
- **Objective:** Filter catalog products by category name.
- **Input:** `GET /api/products?category=Electronics`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - All returned products have `category == "Electronics"`.

### TC-204: Price Range Filtering (Min / Max Price Sliders)
- **Objective:** Filter products within price bounds.
- **Input:** `GET /api/products?min_price=50.00&max_price=150.00`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Every returned product satisfies `50.00 <= price <= 150.00`.

### TC-205: In-Stock Availability Filter Toggle
- **Objective:** Filter products to return only items with available stock (`stock > 0`).
- **Input:** `GET /api/products?in_stock_only=true`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - All returned products have `stock > 0`.

### TC-206: Get Single Product Details by ID
- **Objective:** Retrieve product detail payload for modal/view.
- **Input:** `GET /api/products/{id}`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Matches target product attributes.

### TC-207: Catalog Seed Reset API
- **Objective:** Re-seed catalog inventory to default state.
- **Input:** `POST /api/products/seed`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Message: `"Database re-seeded successfully."`
  - Catalog inventory reset.

---

## 2. Cart & 5-Minute Inventory Reservation

### TC-208: Create Order & Reserve Inventory (Checkout)
- **Objective:** Successfully place checkout request, lock inventory, and start 5-minute reservation timer.
- **Preconditions:** Product ID 1 stock = 20, reserved = 0.
- **Input:** `POST /api/orders/checkout`
  ```json
  {
    "customer_name": "Alice Johnson",
    "customer_email": "alice@example.com",
    "items": [{"product_id": 1, "quantity": 2}]
  }
  ```
- **Expected Outcome:**
  - Status Code: `201 Created`
  - Order status: `RESERVED`
  - Generated `order_number` (format `ORD-XXXXXXXX`).
  - `seconds_remaining` is positive (~300 seconds).
  - Product stock updated: `stock = 18`, `reserved_stock = 2`.

### TC-209: Cart Quantity Consolidation (Duplicate Product Items)
- **Objective:** Ensure duplicate product IDs in checkout cart payload are consolidated correctly.
- **Input:** `POST /api/orders/checkout` containing `[{product_id: 1, quantity: 2}, {product_id: 1, quantity: 3}]`.
- **Expected Outcome:**
  - Order created with a single line item for product ID 1 with total `quantity = 5`.
  - Stock deducted by 5.

### TC-210: Checkout - Insufficient Stock Validation
- **Objective:** Reject checkout request when requested quantity exceeds available stock.
- **Input:** `POST /api/orders/checkout` `{"items": [{"product_id": 1, "quantity": 9999}]}`
- **Expected Outcome:**
  - Status Code: `400 Bad Request`
  - Detail: `"Insufficient stock for ..."`
  - Stock levels unchanged.

### TC-211: Checkout - Empty Cart Error
- **Objective:** Reject checkout request when items array is empty.
- **Input:** `POST /api/orders/checkout` `{"customer_name": "Bob", "customer_email": "bob@example.com", "items": []}`
- **Expected Outcome:**
  - Status Code: `400 Bad Request`
  - Detail: `"Cart is empty."`

### TC-212: Get Order Details & Reservation Countdown
- **Objective:** Retrieve single order details with real-time `seconds_remaining`.
- **Input:** `GET /api/orders/{id}`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Response includes `seconds_remaining`, order status, line items.

### TC-213: List Orders with Filtering
- **Objective:** Retrieve past orders filtered by status or customer email.
- **Input:** `GET /api/orders?customer_email=alice@example.com`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Returns array of matching orders sorted by `created_at` descending.

---

## 3. Background Expiration Worker & Lazy Expiration

### TC-214: Automated Background Expiration Worker
- **Objective:** Cleanup worker automatically marks expired `RESERVED` orders as `EXPIRED` and restores stock.
- **Preconditions:** Order placed, `expires_at` backdated past current time.
- **Execution:** Execute `cleanup_expired_orders(db)`.
- **Expected Outcome:**
  - Cleaned order count > 0.
  - Order status updated to `EXPIRED`.
  - Product `stock` restored, `reserved_stock` cleared.

### TC-215: Lazy Expiration on Get Order Request
- **Objective:** Querying an expired `RESERVED` order automatically triggers inline expiration if cleanup worker hasn't run yet.
- **Input:** `GET /api/orders/{expired_id}`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Order status is lazily updated to `EXPIRED`.
  - Reserved stock released.

---

## 4. Mock Payment Gateway & Idempotency Protection

### TC-216: Process Payment - SUCCESS Mode
- **Objective:** Payment completion converts order to `PAID` and finalizes deduction.
- **Input:** `POST /api/orders/{id}/pay`
  ```json
  {
    "idempotency_key": "IDEM-STOREFRONT-SUCCESS-01",
    "payment_action": "SUCCESS",
    "payment_method": "Credit Card"
  }
  ```
- **Expected Outcome:**
  - Status Code: `200 OK`
  - `order_status = "PAID"`, `payment_status = "SUCCESS"`, `cached = false`.
  - Product `reserved_stock` reduced by item quantity. `stock` remains deducted.

### TC-217: Process Payment - FAILED Mode
- **Objective:** Failed payment converts order to `FAILED` and releases reserved items back to available stock.
- **Input:** `POST /api/orders/{id}/pay` `{"idempotency_key": "IDEM-STOREFRONT-FAIL-01", "payment_action": "FAILED"}`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - `order_status = "FAILED"`, `payment_status = "FAILED"`.
  - Product `stock` restored, `reserved_stock` cleared.

### TC-218: Process Payment - TIMEOUT Mode
- **Objective:** Gateway timeout records transaction timeout state; order remains reserved until 5-minute expiry worker executes.
- **Input:** `POST /api/orders/{id}/pay` `{"idempotency_key": "IDEM-STOREFRONT-TIMEOUT-01", "payment_action": "TIMEOUT"}`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - `payment_status = "TIMEOUT"`. Order status remains `RESERVED`.

### TC-219: Idempotency Protection - Duplicate Request Caching
- **Objective:** Sending a duplicate payment request with identical `idempotency_key` returns cached transaction response.
- **Execution:** Submit identical `POST /api/orders/{id}/pay` twice with same `idempotency_key`.
- **Expected Outcome:**
  - First request: `200 OK`, `cached = false`.
  - Second request: `200 OK`, `cached = true`, message indicates `"Duplicate request detected."`.

---

## 5. Post-Purchase Lifecycle (Cancellation & Refund)

### TC-220: Cancel Active Reserved Order
- **Objective:** Customer cancels a pending `RESERVED` order before payment.
- **Input:** `POST /api/orders/{id}/cancel`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Order status: `CANCELLED`
  - Reserved stock returned to `stock`.

### TC-221: Attempt Cancel on Non-Reserved Order (Forbidden Action)
- **Objective:** Reject cancellation of `PAID` or `EXPIRED` orders.
- **Preconditions:** Order is `PAID`.
- **Input:** `POST /api/orders/{paid_id}/cancel`
- **Expected Outcome:**
  - Status Code: `400 Bad Request`
  - Detail: `"Cannot cancel order in status 'PAID'..."`

### TC-222: Refund Paid Order
- **Objective:** Refunding a `PAID` order changes status to `REFUNDED` and returns sold items back to catalog stock.
- **Preconditions:** Order status = `PAID`.
- **Input:** `POST /api/orders/{paid_id}/refund`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Order status: `REFUNDED`
  - Product catalog `stock` increased by item quantity.

### TC-223: Refund Non-Paid Order Error
- **Objective:** Reject refund request for `RESERVED` or `CANCELLED` orders.
- **Input:** `POST /api/orders/{reserved_id}/refund`
- **Expected Outcome:**
  - Status Code: `400 Bad Request`
  - Detail: `"Cannot refund order in status 'RESERVED'..."`

---

## 6. System Health & Infrastructure

### TC-224: Storefront Root HTML Page (`/`)
- **Objective:** Ensure storefront HTML loads successfully via `GET` and `HEAD`.
- **Input:** `GET /` and `HEAD /`
- **Expected Outcome:**
  - Status Code: `200 OK`

### TC-225: Health Check Endpoint (`/health`)
- **Objective:** Monitor application health via `GET` and `HEAD`.
- **Input:** `GET /health` and `HEAD /health`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - JSON response: `{"status": "ok", "app": "TechLoom E-Commerce Storefront & Payment Gateway"}`

---

## Summary Matrix

| Test ID | Module | Scenario | Expected Status | Stock Impact |
| :--- | :--- | :--- | :--- | :--- |
| **TC-201** | Catalog | List Products | `200 OK` | None |
| **TC-202** | Search | Text Search (`Headphones`) | `200 OK` | None |
| **TC-203** | Filter | Category Filter (`Electronics`)| `200 OK` | None |
| **TC-204** | Filter | Price Range (`$50-$150`) | `200 OK` | None |
| **TC-208** | Checkout | Create Order & Reserve | `201 Created` | `stock -= Q`, `reserved += Q` |
| **TC-210** | Checkout | Insufficient Stock | `400 Bad Request` | None |
| **TC-214** | Worker | Cleanup Expired Reservation | Executed | `stock += Q`, `reserved -= Q` |
| **TC-216** | Payments | Pay SUCCESS | `200 OK` | `reserved -= Q` |
| **TC-217** | Payments | Pay FAILED | `200 OK` | `stock += Q`, `reserved -= Q` |
| **TC-219** | Payments | Idempotency Retry | `200 OK` (`cached: true`)| No double deduction |
| **TC-220** | Lifecycle| Cancel Reserved Order | `200 OK` | `stock += Q`, `reserved -= Q` |
| **TC-222** | Lifecycle| Refund Paid Order | `200 OK` | `stock += Q` |
