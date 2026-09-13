# Task 01: POS & High-Concurrency Inventory Management System
## Comprehensive Test Case Specifications

---

### Overview
This document defines the complete test case suite for **Task 01 (POS & High-Concurrency Inventory Management System)**. The test suite covers functional, boundary, concurrency, state-machine, background worker, and payment idempotency scenarios.

---

## 1. Product & Inventory Management (CRUD Operations)

### TC-101: Create Product - Valid Input
- **Objective:** Verify successful creation of a new product with valid data.
- **Preconditions:** Server is running, database is accessible.
- **Input:** `POST /api/products`
  ```json
  {
    "name": "Barcode Scanner Terminal",
    "price": 249.99,
    "stock_quantity": 50
  }
  ```
- **Expected Outcome:**
  - Status Code: `201 Created`
  - Response contains generated `id`, `reserved_quantity = 0`, `created_at`, `updated_at`.
  - Database contains the new product record.

### TC-102: Create Product - Invalid Price / Stock (Validation Errors)
- **Objective:** Ensure products cannot be created with negative price or stock quantity.
- **Input:** `POST /api/products`
  - Case A: `{"name": "Invalid Item", "price": -10.0, "stock_quantity": 5}`
  - Case B: `{"name": "Invalid Item", "price": 10.0, "stock_quantity": -5}`
- **Expected Outcome:**
  - Status Code: `422 Unprocessable Entity` (Pydantic validation error).
  - Product is not persisted in the database.

### TC-103: List All Products
- **Objective:** Retrieve all products with current stock and reserved quantities.
- **Input:** `GET /api/products?skip=0&limit=100`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Returns array of products, each containing `id`, `name`, `price`, `stock_quantity`, `reserved_quantity`.

### TC-104: Get Product by ID - Valid ID
- **Objective:** Fetch details of a specific existing product.
- **Input:** `GET /api/products/{id}`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Response matches expected product attributes.

### TC-105: Get Product by ID - Non-existent ID
- **Objective:** Verify proper 404 response for invalid product ID.
- **Input:** `GET /api/products/999999`
- **Expected Outcome:**
  - Status Code: `404 Not Found`
  - Response detail: `"Product not found."`

### TC-106: Update Product Details & Stock
- **Objective:** Modify product name, price, or stock quantity using `PUT`.
- **Input:** `PUT /api/products/{id}`
  ```json
  {
    "price": 229.99,
    "stock_quantity": 75
  }
  ```
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Updated product returns `price = 229.99` and `stock_quantity = 75`.

### TC-107: Update Product - Non-existent Product
- **Objective:** Attempting to update a non-existent product should return 404.
- **Input:** `PUT /api/products/999999` `{"price": 50.0}`
- **Expected Outcome:**
  - Status Code: `404 Not Found`

### TC-108: Delete Product
- **Objective:** Delete an existing product from inventory.
- **Input:** `DELETE /api/products/{id}`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Subsequent `GET /api/products/{id}` returns `404 Not Found`.

---

## 2. Real-Time Inventory Accounting & Stock Metrics

### TC-109: Get Product Stock Metrics - Single Product
- **Objective:** Validate calculation of `available_stock`, `reserved_stock`, and `total_stock`.
- **Preconditions:** Product has `stock_quantity = 30` and `reserved_quantity = 10`.
- **Input:** `GET /api/products/{id}/stock`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Payload:
    ```json
    {
      "product_id": <id>,
      "name": "...",
      "available_stock": 30,
      "reserved_stock": 10,
      "total_stock": 40
    }
    ```

### TC-110: Stock Summary API Across Catalog
- **Objective:** Verify aggregate inventory health stats across all products.
- **Input:** `GET /api/stock`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Returns total catalog metrics and array of product stock breakdown objects.

---

## 3. High-Concurrency Stock Reservation & Pessimistic Row Locking (`SELECT FOR UPDATE`)

### TC-111: Order Placement & Single-Threaded Stock Reservation
- **Objective:** Placing an order reduces `stock_quantity` and increases `reserved_quantity` atomically.
- **Preconditions:** Product stock = 10, reserved = 0.
- **Input:** `POST /api/orders`
  ```json
  {
    "items": [{"product_id": <id>, "quantity": 3}]
  }
  ```
- **Expected Outcome:**
  - Status Code: `201 Created`
  - Order status: `RESERVED`
  - Reservation expiration timestamp set to `now + 5 minutes`.
  - Product stock updated to: `stock_quantity = 7`, `reserved_quantity = 3`.

### TC-112: Order Placement - Insufficient Stock
- **Objective:** Attempting to order more units than available stock should fail cleanly without side effects.
- **Preconditions:** Product stock = 4.
- **Input:** `POST /api/orders` `{"items": [{"product_id": <id>, "quantity": 10}]}`
- **Expected Outcome:**
  - Status Code: `400 Bad Request`
  - Detail: `"Insufficient stock for ..."`
  - Stock levels remain unchanged: `stock_quantity = 4`, `reserved_quantity = 0`.

### TC-113: High-Concurrency Race Condition Prevention (20 Parallel Requests)
- **Objective:** Verify zero overselling under heavy concurrent transaction load using pessimistic locking (`SELECT ... FOR UPDATE`).
- **Preconditions:** Product stock = 20, reserved = 0.
- **Execution:** Launch 20 concurrent tasks requesting 5 items each (total requested = 100 items).
- **Expected Outcome:**
  - Exactly 4 requests return `201 Created` (4 x 5 = 20 items reserved).
  - Exactly 16 requests return `400 Bad Request` (Insufficient stock).
  - Real-time stock state: `available_stock = 0`, `reserved_stock = 20`, `total_stock = 20`.
  - Zero negative stock, zero overbooking.

### TC-114: Multi-Product Atomic Order Placement
- **Objective:** An order containing multiple products locks all item rows in a single ACID transaction.
- **Preconditions:** Product A stock = 10, Product B stock = 2 (requested 3).
- **Input:** `POST /api/orders` requesting 2 of Product A and 3 of Product B.
- **Expected Outcome:**
  - Order fails with `400 Bad Request` due to Product B stock limit.
  - Transaction rolls back completely: Product A stock remains 10 (no partial reservation).

---

## 4. Reservation TTL & Background Expiration Cleanup

### TC-115: Background Expiration Cleanup Worker Execution
- **Objective:** Verify unpaid orders exceeding 5-minute reservation window are marked `EXPIRED` and reserved stock is released.
- **Preconditions:** Order placed for 5 items of Product A (`stock = 15`, `reserved = 5`).
- **Execution:** Fast-forward / backdate `reservation_expires_at` past current UTC time and invoke background cleanup function.
- **Expected Outcome:**
  - Order status updated from `RESERVED` to `EXPIRED`.
  - Product stock restored: `stock_quantity = 20`, `reserved_quantity = 0`.

### TC-116: Lazy Expiration Check on Payment Attempt
- **Objective:** Attempting to pay for an expired order triggers lazy expiration check and rejects payment.
- **Preconditions:** Order reservation time expired.
- **Input:** `POST /api/orders/{expired_id}/pay` `{"mock_status": "SUCCESS", "idempotency_key": "K1"}`
- **Expected Outcome:**
  - Status Code: `400 Bad Request`
  - Detail: `"Reservation for order ... has expired."`
  - Order status set to `EXPIRED`. Stock released.

---

## 5. Mock Payment System & Idempotency Protection

### TC-117: Payment Simulation - SUCCESS
- **Objective:** Successful payment converts `RESERVED` order to `PAID` and finalizes inventory deduction.
- **Preconditions:** Order status = `RESERVED`, Product `stock = 10`, `reserved = 5`.
- **Input:** `POST /api/orders/{id}/pay`
  ```json
  {
    "mock_status": "SUCCESS",
    "idempotency_key": "IDEM-SUCCESS-001"
  }
  ```
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Order status: `PAID`
  - Payment record created with status `SUCCESS`.
  - Product stock state: `stock_quantity = 10`, `reserved_quantity = 0` (reserved quantity cleared).

### TC-118: Payment Simulation - FAILURE
- **Objective:** Failed payment converts order to `FAILED` and immediately releases reserved stock back to available stock.
- **Preconditions:** Order status = `RESERVED`, Product `stock = 10`, `reserved = 5`.
- **Input:** `POST /api/orders/{id}/pay` `{"mock_status": "FAILURE", "idempotency_key": "IDEM-FAIL-001"}`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Order status: `FAILED`
  - Product stock restored: `stock_quantity = 15`, `reserved_quantity = 0`.

### TC-119: Payment Simulation - TIMEOUT
- **Objective:** Timeout payment records transaction timeout and marks order as `EXPIRED`, releasing stock.
- **Input:** `POST /api/orders/{id}/pay` `{"mock_status": "TIMEOUT", "idempotency_key": "IDEM-TIME-001"}`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Order status set to `EXPIRED`.
  - Product reserved stock restored to available pool.

### TC-120: Idempotency Protection - Duplicate Payment Retry
- **Objective:** Sending a second request with the same `idempotency_key` returns the cached payment transaction response without duplicate charges or stock mutation.
- **Execution:** Submit `POST /api/orders/{id}/pay` twice with `idempotency_key = "IDEM-SAME-KEY"`.
- **Expected Outcome:**
  - Both requests return `200 OK`.
  - Second response returns the existing `PaymentRecord` matching `idempotency_key`.
  - Stock is modified only once.

### TC-121: Idempotency Key Reuse Across Different Orders (Validation Failure)
- **Objective:** Using an idempotency key already associated with Order A when submitting payment for Order B should fail.
- **Preconditions:** Order A paid with `idempotency_key = "KEY-A"`.
- **Input:** `POST /api/orders/{order_b}/pay` `{"mock_status": "SUCCESS", "idempotency_key": "KEY-A"}`
- **Expected Outcome:**
  - Status Code: `400 Bad Request`
  - Detail: `"Idempotency key 'KEY-A' was already used for order ..."`

---

## 6. Order Cancellation & State Machine

### TC-122: Cancel Active Reserved Order
- **Objective:** Manual cancellation of a `RESERVED` order restores stock immediately.
- **Preconditions:** Order status = `RESERVED`, reserved items = 4.
- **Input:** `POST /api/orders/{id}/cancel`
- **Expected Outcome:**
  - Status Code: `200 OK`
  - Order status: `CANCELLED`
  - Reserved stock released: `stock_quantity += 4`, `reserved_quantity -= 4`.

### TC-123: Cancel Order - Invalid Status (PAID / CANCELLED / EXPIRED)
- **Objective:** Prevent cancellation of orders that are already `PAID`, `CANCELLED`, or `EXPIRED`.
- **Preconditions:** Order status = `PAID`.
- **Input:** `POST /api/orders/{id}/cancel`
- **Expected Outcome:**
  - Status Code: `400 Bad Request`
  - Detail: `"Cannot cancel order ... in status 'PAID'."`

---

## Summary Matrix

| Test ID | Module | Scenario | Expected Status | Stock Impact |
| :--- | :--- | :--- | :--- | :--- |
| **TC-101** | Products | Create Product (Valid) | `201 Created` | Initialized |
| **TC-102** | Products | Create Product (Negative stock/price) | `422 Unprocessable` | None |
| **TC-103** | Products | List Products | `200 OK` | None |
| **TC-105** | Products | Get Non-existent Product | `404 Not Found` | None |
| **TC-111** | Orders | Reserve Stock (Valid) | `201 Created` | `stock -= Q`, `reserved += Q` |
| **TC-112** | Orders | Reserve Stock (Exceeding Stock) | `400 Bad Request` | None |
| **TC-113** | Concurrency| 20 Concurrent Requests (Parallel) | 4x `201`, 16x `400` | Zero overselling |
| **TC-115** | Background | Reservation Cleanup Expiry | Executed | `stock += Q`, `reserved -= Q` |
| **TC-117** | Payments | Pay SUCCESS | `200 OK` | `reserved -= Q` |
| **TC-118** | Payments | Pay FAILURE | `200 OK` | `stock += Q`, `reserved -= Q` |
| **TC-120** | Payments | Idempotency Key Reuse | `200 OK` (Cached) | No duplicate mutation |
| **TC-122** | Orders | Cancel Reserved Order | `200 OK` | `stock += Q`, `reserved -= Q` |
