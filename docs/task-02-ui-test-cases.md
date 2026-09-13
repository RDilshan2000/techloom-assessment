# Task 02: E-Commerce Storefront & Payment System
## UI & Manual Test Case Specifications

---

### Overview
This document defines step-by-step **UI & Manual Test Cases** for the **Task 02 Customer-Facing Storefront (`http://127.0.0.1:8001`)**.

---

## 1. Storefront Discovery, Search & Category Navigation

### UI-201: Storefront Home Page & Catalog Grid
- **Objective:** Verify rendering of navigation bar, hero banner, category pills, search bar, and product card grid.
- **User Actions:**
  1. Open browser and navigate to `http://127.0.0.1:8001`.
  2. Scroll down to inspect product cards (image, badge, title, price, available stock, "Add to Cart" button).
- **Expected UI Behavior:**
  - Header logo "TechLoom Storefront" renders.
  - Cart button shows `0` badge.
  - Catalog renders seeded products with stock badges.

### UI-202: Live Search Input Interaction
- **Objective:** Type keywords in search bar and observe instant filtered results.
- **User Actions:**
  1. Click search input box.
  2. Type `Headphones`.
- **Expected UI Behavior:**
  - Product grid filters dynamically to display matching headphone products.
  - Result count updates (e.g., "Showing 2 products").

### UI-203: Category Pills Navigation
- **Objective:** Click category buttons (`Electronics`, `Clothing`, `Books`, `All`).
- **User Actions:**
  1. Click "Electronics" category pill.
- **Expected UI Behavior:**
  - Active pill is highlighted in primary theme color.
  - Catalog updates to display only Electronics items.

### UI-204: Price Range Slider & In-Stock Filter
- **Objective:** Drag price slider and toggle "In-Stock Only" checkbox.
- **User Actions:**
  1. Set Max Price slider to `$100`.
  2. Check "In Stock Only" toggle.
- **Expected UI Behavior:**
  - Catalog updates to show items under $100 with available stock > 0.

---

## 2. Slide-Over Cart Drawer & Checkout Reservation

### UI-205: Shopping Cart Drawer Interaction
- **Objective:** Add items to cart, open slide-over drawer, and modify quantities.
- **User Actions:**
  1. Click "Add to Cart" on a product card.
  2. Click Cart icon in top header to open slide-over drawer.
  3. Click `+` button inside drawer to increase quantity.
- **Expected UI Behavior:**
  - Slide-over cart drawer smoothly slides in from right.
  - Subtotal and Total calculations update in real time.
  - Header cart counter badge updates.

### UI-206: Checkout Form & 5-Minute Live Reservation Banner
- **Objective:** Submit checkout form and verify 5-minute live reservation banner & timer.
- **User Actions:**
  1. In Cart drawer, click "Proceed to Checkout".
  2. Fill Checkout Modal form:
     - Name: `Jane Doe`
     - Email: `jane@example.com`
  3. Click "Reserve & Proceed to Payment".
- **Expected UI Behavior:**
  - Payment Simulator modal appears.
  - Top alert banner shows order number `ORD-XXXXXXXX` and live countdown timer `05:00` ticking down.
  - Background stock for item decreases in storefront catalog.

---

## 3. Payment Simulator & Idempotency Protection

### UI-207: Payment Simulator - SUCCESS Mode
- **Objective:** Simulate successful card payment flow.
- **User Actions:**
  1. In Payment Simulator modal, click "Simulate SUCCESS" button.
- **Expected UI Behavior:**
  - Modal displays success animation & green badge `PAID`.
  - Confirmation notification: "Order Paid Successfully!".

### UI-208: Payment Simulator - FAILURE Mode
- **Objective:** Simulate failed card payment and verify stock restoration.
- **User Actions:**
  1. Checkout another item.
  2. In Payment Simulator modal, click "Simulate FAILURE".
- **Expected UI Behavior:**
  - Modal shows red error badge `FAILED`.
  - Alert indicates "Payment Declined. Reserved stock released to catalog".
  - Catalog stock increases back to original amount.

### UI-209: Payment Simulator - TIMEOUT Mode
- **Objective:** Simulate gateway timeout.
- **User Actions:**
  1. Checkout an item.
  2. Click "Simulate TIMEOUT".
- **Expected UI Behavior:**
  - Yellow badge `TIMEOUT` appears.
  - Banner informs user that order remains reserved until 5-minute expiry.

---

## 4. Post-Purchase Dashboard (Cancellation & Refunds)

### UI-210: Order History Dashboard & Cancellation
- **Objective:** View order history tab, filter by email, and cancel pending reservation.
- **User Actions:**
  1. Click "Order History" tab in header.
  2. Enter email `jane@example.com` in filter.
  3. Click "Cancel Order" on a `RESERVED` order.
- **Expected UI Behavior:**
  - Order status badge updates to `CANCELLED`.
  - Reserved stock is restored.

### UI-211: Request Refund Flow
- **Objective:** Request refund on a `PAID` order and verify item returns to stock.
- **User Actions:**
  1. In Order History, locate a `PAID` order.
  2. Click "Request Refund" button.
  3. Confirm refund prompt.
- **Expected UI Behavior:**
  - Status badge updates to purple `REFUNDED`.
  - Item stock increases by order quantity in catalog grid.
