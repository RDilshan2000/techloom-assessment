# Task 01: POS & High-Concurrency Inventory Management System
## UI & Manual Test Case Specifications

---

### Overview
This document defines step-by-step **UI & Manual Test Cases** for the **Task 01 Admin POS & Inventory Management Dashboard (`http://127.0.0.1:8000`)**.

---

## 1. Inventory Dashboard & Real-Time Metrics

### UI-101: Dashboard Initial Load & Metric Cards
- **Objective:** Verify initial page render, glassmorphic UI elements, and real-time inventory metric cards.
- **User Actions:**
  1. Open browser and navigate to `http://127.0.0.1:8000`.
  2. Inspect top stat cards: "Total Products", "Available Inventory", "Reserved Inventory", "Low Stock Alerts".
- **Expected UI Behavior:**
  - Header displays "TechLoom POS & Inventory Management System".
  - Stat cards show formatted numbers matching live database state.
  - Refresh button triggers live background update with subtle animation.

---

## 2. Product Management UI (Add, Edit, Delete)

### UI-102: Create New Product via UI Modal
- **Objective:** Add a new product to inventory using the modal form.
- **User Actions:**
  1. Click "+ Add Product" button in top toolbar.
  2. Fill form fields:
     - Product Name: `Wireless POS Terminal`
     - Price ($): `199.99`
     - Initial Stock: `25`
  3. Click "Save Product" button.
- **Expected UI Behavior:**
  - Modal closes automatically.
  - Toast notification appears: "Product created successfully!".
  - New product row appears in the Inventory Table with `Stock = 25` and `Reserved = 0`.

### UI-103: Update Stock / Price via UI
- **Objective:** Modify product stock level directly from product row or edit modal.
- **User Actions:**
  1. Click "Edit" icon next to `Wireless POS Terminal`.
  2. Change Price to `179.99` and Stock to `40`.
  3. Click "Update".
- **Expected UI Behavior:**
  - Table updates instantly without full page reload.
  - Price displays `$179.99` and Available Stock shows `40`.

### UI-104: Delete Product via UI
- **Objective:** Remove a product from the inventory table.
- **User Actions:**
  1. Click "Delete" trash icon next to a test product.
  2. Confirm deletion in popup dialog.
- **Expected UI Behavior:**
  - Product row is removed from table with fade animation.
  - Total Products count in metric header decreases by 1.

---

## 3. POS Checkout Station & 5-Minute Reservation

### UI-105: POS Terminal Cart Addition & Quantity Selection
- **Objective:** Add items to POS checkout cart and adjust quantities.
- **User Actions:**
  1. In POS Checkout Station section, select a product from dropdown/grid.
  2. Click "+ Add to Cart".
  3. Increment item quantity to `3`.
- **Expected UI Behavior:**
  - Cart line items update in real time.
  - Total price calculation updates dynamically.

### UI-106: Place Order & 5-Minute Reservation Timer UI
- **Objective:** Submit order and observe live 5-minute reservation timer ticking down.
- **User Actions:**
  1. Click "Complete Checkout & Reserve Stock" button.
- **Expected UI Behavior:**
  - Success banner displays order number and status badge `RESERVED`.
  - Live countdown timer initializes at `05:00` and ticks down second-by-second (`04:59`, `04:58`...).
  - Main inventory table automatically updates: `Available Stock -= 3`, `Reserved Stock += 3`.

---

## 4. Payment Simulator & Idempotency

### UI-107: Payment Simulator Modal - SUCCESS Simulation
- **Objective:** Simulate successful customer payment.
- **User Actions:**
  1. In Order History table, click "Pay Order" on the `RESERVED` order.
  2. In Payment Modal, select status: `SUCCESS`.
  3. Enter Idempotency Key: `IDEM-UI-POS-001`.
  4. Click "Submit Payment".
- **Expected UI Behavior:**
  - Modal closes, status badge turns green `PAID`.
  - Countdown timer disappears.
  - Reserved inventory converts to final sale (`Reserved Stock -= 3`).

### UI-108: Idempotency Key Retry Test via UI
- **Objective:** Resubmit payment modal with same idempotency key to verify cached UI badge.
- **User Actions:**
  1. Click "Pay Order" again on the same order using idempotency key `IDEM-UI-POS-001`.
- **Expected UI Behavior:**
  - System displays badge "Idempotency Cache Hit: Transaction already processed".
  - Stock is not mutated a second time.

### UI-109: Order Cancellation via UI
- **Objective:** Cancel a pending reserved order and verify immediate stock restoration in UI table.
- **User Actions:**
  1. Place a new order for 2 units.
  2. In Order History table, click "Cancel Order".
- **Expected UI Behavior:**
  - Status badge turns red `CANCELLED`.
  - Available stock increases by 2 immediately in the table.
