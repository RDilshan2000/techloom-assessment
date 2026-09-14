/**
 * Storefront & Payment Gateway Application Logic
 */

const state = {
    products: [],
    cart: JSON.parse(localStorage.getItem('loom_cart') || '[]'),
    activeCategory: 'All',
    searchQuery: '',
    maxPrice: 600,
    inStockOnly: false,
    activeTab: 'store',
    activeOrder: null,
    orders: [],
    idempotencyKey: '',
    selectedPaymentMethod: 'Credit Card',
    countdownInterval: null
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupEventListeners();
    await loadProducts();
    await loadOrders();
    updateCartBadge();
    startGlobalTimers();
}

function setupEventListeners() {
    // Navigation Tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const target = tab.dataset.tab;
            switchView(target);
        });
    });

    // Filters
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce((e) => {
            state.searchQuery = e.target.value;
            renderProducts();
        }, 250));
    }

    const priceSlider = document.getElementById('price-slider');
    const priceDisplay = document.getElementById('price-display');
    if (priceSlider) {
        priceSlider.addEventListener('input', (e) => {
            state.maxPrice = parseFloat(e.target.value);
            if (priceDisplay) priceDisplay.textContent = `$${state.maxPrice}`;
            renderProducts();
        });
    }

    const inStockToggle = document.getElementById('instock-toggle');
    if (inStockToggle) {
        inStockToggle.addEventListener('change', (e) => {
            state.inStockOnly = e.target.checked;
            renderProducts();
        });
    }

    // Cart Drawer Controls
    const cartBtn = document.getElementById('cart-btn');
    if (cartBtn) cartBtn.addEventListener('click', openCartDrawer);

    const closeCartBtn = document.getElementById('close-cart-btn');
    if (closeCartBtn) closeCartBtn.addEventListener('click', closeCartDrawer);

    const checkoutBtn = document.getElementById('proceed-checkout-btn');
    if (checkoutBtn) checkoutBtn.addEventListener('click', handleProceedToCheckout);

    // Modal Close Buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-overlay');
            if (modal) modal.classList.add('hidden');
        });
    });

    // Seed Data Button
    const seedBtn = document.getElementById('seed-data-btn');
    if (seedBtn) seedBtn.addEventListener('click', seedData);

    // Refresh Orders Button
    const refreshOrdersBtn = document.getElementById('refresh-orders-btn');
    if (refreshOrdersBtn) refreshOrdersBtn.addEventListener('click', loadOrders);

    // Admin Panel Listeners
    const adminForm = document.getElementById('admin-create-product-form');
    if (adminForm) adminForm.addEventListener('submit', handleCreateProduct);

    const adminRefreshBtn = document.getElementById('admin-refresh-inventory-btn');
    if (adminRefreshBtn) adminRefreshBtn.addEventListener('click', loadAdminInventory);

    // Regenerate Idempotency Key
    const regenIdemBtn = document.getElementById('regen-idem-btn');
    if (regenIdemBtn) {
        regenIdemBtn.addEventListener('click', () => {
            state.idempotencyKey = generateIdempotencyKey();
            const elem = document.getElementById('idempotency-key-input');
            if (elem) elem.value = state.idempotencyKey;
            showToast('Key Regenerated', 'New unique idempotency key created.', 'info');
        });
    }
}

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function switchView(targetViewId) {
    if (!targetViewId) return;

    // Normalize shorthand names to full view container IDs
    let normalizedId = targetViewId;
    if (targetViewId === 'store' || targetViewId === 'storefront' || targetViewId === 'tab-store') normalizedId = 'storefront-view';
    else if (targetViewId === 'orders' || targetViewId === 'order-history' || targetViewId === 'tab-orders') normalizedId = 'order-history-view';
    else if (targetViewId === 'admin' || targetViewId === 'tab-admin') normalizedId = 'admin-view';
    else if (targetViewId === 'status' || targetViewId === 'system-specs' || targetViewId === 'tab-status' || targetViewId === 'status-view') normalizedId = 'system-specs-view';

    state.activeTab = normalizedId;

    // 1. Toggle hidden class on all 4 main view containers
    const views = ['storefront-view', 'order-history-view', 'admin-view', 'system-specs-view'];
    views.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            if (id === normalizedId || id === targetViewId) {
                el.classList.remove('hidden');
            } else {
                el.classList.add('hidden');
            }
        }
    });

    // 2. Highlight active nav tab button
    const navTabs = document.querySelectorAll('.nav-tab');
    if (navTabs) {
        navTabs.forEach(t => {
            if (!t) return;
            const tabData = t.dataset ? t.dataset.tab : '';
            const isMatch = (tabData === normalizedId) || (tabData === targetViewId) ||
                            (normalizedId === 'storefront-view' && (tabData === 'store' || tabData === 'storefront')) ||
                            (normalizedId === 'order-history-view' && (tabData === 'orders' || tabData === 'order-history')) ||
                            (normalizedId === 'admin-view' && (tabData === 'admin' || tabData === 'admin-view')) ||
                            (normalizedId === 'system-specs-view' && (tabData === 'status' || tabData === 'system-specs' || tabData === 'status-view'));

            if (isMatch) {
                t.classList.add('border-blue-500', 'text-blue-400', 'bg-blue-500/10');
                t.classList.remove('border-transparent', 'text-slate-400');
            } else {
                t.classList.remove('border-blue-500', 'text-blue-400', 'bg-blue-500/10');
                t.classList.add('border-transparent', 'text-slate-400');
            }
        });
    }

    // 3. Trigger data loading & rendering per view
    if (normalizedId === 'storefront-view') {
        if (typeof renderProducts === 'function') {
            renderProducts();
        }
        if (typeof loadProducts === 'function' && (!state.products || state.products.length === 0)) {
            loadProducts();
        }
    } else if (normalizedId === 'order-history-view') {
        if (typeof loadOrders === 'function') loadOrders();
    } else if (normalizedId === 'admin-view') {
        if (typeof loadAdminProducts === 'function') loadAdminProducts();
        else if (typeof loadAdminInventory === 'function') loadAdminInventory();
    }
}

// Backwards compatibility alias
function switchTab(tabName) {
    switchView(tabName);
}

// ================= API CALLS =================

async function loadProducts() {
    try {
        const queryParams = new URLSearchParams();
        if (state.searchQuery) queryParams.append('search', state.searchQuery);
        if (state.activeCategory && state.activeCategory !== 'All') queryParams.append('category', state.activeCategory);
        if (state.maxPrice < 600) queryParams.append('max_price', state.maxPrice);
        if (state.inStockOnly) queryParams.append('in_stock_only', 'true');

        const res = await fetch(`/api/products?${queryParams.toString()}`);
        if (!res.ok) throw new Error('Failed to load products');
        state.products = await res.json();
        renderProducts();
        renderCategoryPills();
    } catch (err) {
        console.error(err);
        showToast('Error', 'Failed to fetch product catalog', 'error');
    }
}

async function loadOrders() {
    try {
        const res = await fetch('/api/orders');
        if (!res.ok) throw new Error('Failed to fetch orders');
        state.orders = await res.json();
        renderOrders();
    } catch (err) {
        console.error(err);
        showToast('Error', 'Failed to fetch order history', 'error');
    }
}

async function seedData() {
    try {
        const res = await fetch('/api/products/seed', { method: 'POST' });
        const data = await res.json();
        showToast('Inventory Reset', data.message, 'success');
        await loadProducts();
    } catch (err) {
        showToast('Error', 'Failed to seed data', 'error');
    }
}

// ================= RENDER FUNCTIONS =================

function renderCategoryPills() {
    const categories = ['All', 'Electronics', 'Clothing', 'Books', 'Home', 'Fitness'];
    const container = document.getElementById('category-pills');
    if (!container) return;

    container.innerHTML = categories.map(cat => {
        const active = state.activeCategory === cat;
        return `
            <button onclick="selectCategory('${cat}')" 
                class="px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${
                    active 
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' 
                    : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700/50'
                }">
                ${cat}
            </button>
        `;
    }).join('');
}

function selectCategory(cat) {
    state.activeCategory = cat;
    renderCategoryPills();
    loadProducts();
}

function renderProducts() {
    const grid = document.getElementById('products-grid');
    if (!grid) return;

    if (state.products.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full py-16 text-center text-slate-400">
                <i class="fa-solid fa-box-open text-5xl mb-4 text-slate-600"></i>
                <p class="text-lg font-medium">No products match your criteria.</p>
                <button onclick="resetFilters()" class="mt-4 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-500">Reset Filters</button>
            </div>
        `;
        return;
    }

    grid.innerHTML = state.products.map(product => {
        const available = product.stock;
        const reserved = product.reserved_stock;
        const total = product.total_stock;
        
        let stockBadge = '';
        if (available > 10) {
            stockBadge = `<span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><i class="fa-solid fa-circle-check mr-1"></i>${available} In Stock</span>`;
        } else if (available > 0) {
            stockBadge = `<span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse-soft"><i class="fa-solid fa-triangle-exclamation mr-1"></i>Low Stock (${available})</span>`;
        } else {
            stockBadge = `<span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20"><i class="fa-solid fa-circle-xmark mr-1"></i>Out of Stock</span>`;
        }

        const isOutOfStock = available <= 0;

        return `
            <div class="glass-panel rounded-2xl overflow-hidden group hover:border-blue-500/40 transition-all duration-300 flex flex-col justify-between">
                <div>
                    <div class="relative h-48 overflow-hidden bg-slate-900">
                        <img src="${product.image_url}" alt="${product.name}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" onError="this.src='https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=500&q=80'">
                        <div class="absolute top-3 left-3">
                            <span class="px-2.5 py-1 text-xs font-medium rounded-full bg-slate-900/80 text-slate-300 backdrop-blur-md border border-slate-700">
                                ${product.category}
                            </span>
                        </div>
                        <div class="absolute top-3 right-3">
                            ${stockBadge}
                        </div>
                    </div>
                    
                    <div class="p-5">
                        <h3 class="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors line-clamp-1">${product.name}</h3>
                        <p class="text-sm text-slate-400 mt-1 line-clamp-2">${product.description}</p>
                        
                        <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                            <div>
                                <span class="text-xs text-slate-500 uppercase tracking-wider block">Price</span>
                                <span class="text-xl font-bold text-emerald-400">$${product.price.toFixed(2)}</span>
                            </div>
                            <div class="text-right">
                                <span class="text-xs text-slate-500 uppercase tracking-wider block">Reserved</span>
                                <span class="text-xs font-medium text-amber-400">${reserved} held</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="p-5 pt-0 flex gap-2">
                    <button onclick="openProductDetailModal(${product.id})" class="flex-1 py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-xl border border-slate-700/50 transition-colors">
                        Details
                    </button>
                    <button onclick="addToCart(${product.id})" ${isOutOfStock ? 'disabled' : ''} 
                        class="flex-1 py-2 px-3 ${
                            isOutOfStock 
                            ? 'bg-slate-800 text-slate-600 cursor-not-allowed border border-slate-800' 
                            : 'bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-lg shadow-blue-600/20'
                        } text-sm rounded-xl transition-all duration-200 flex items-center justify-center gap-1.5">
                        <i class="fa-solid fa-cart-plus"></i> Add
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function resetFilters() {
    state.searchQuery = '';
    state.activeCategory = 'All';
    state.maxPrice = 600;
    state.inStockOnly = false;
    
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.value = '';
    const priceSlider = document.getElementById('price-slider');
    if (priceSlider) priceSlider.value = 600;
    const priceDisplay = document.getElementById('price-display');
    if (priceDisplay) priceDisplay.textContent = '$600';
    const inStockToggle = document.getElementById('instock-toggle');
    if (inStockToggle) inStockToggle.checked = false;

    renderCategoryPills();
    loadProducts();
}

// ================= CART MANAGEMENT =================

function addToCart(productId, qty = 1) {
    const product = state.products.find(p => p.id === productId);
    if (!product) return;

    const existingIndex = state.cart.findIndex(item => item.product_id === productId);
    const currentQtyInCart = existingIndex >= 0 ? state.cart[existingIndex].quantity : 0;
    
    if (currentQtyInCart + qty > product.stock) {
        showToast('Stock Limit Reached', `Only ${product.stock} unit(s) available in stock.`, 'warning');
        return;
    }

    if (existingIndex >= 0) {
        state.cart[existingIndex].quantity += qty;
    } else {
        state.cart.push({
            product_id: product.id,
            name: product.name,
            price: product.price,
            image_url: product.image_url,
            category: product.category,
            stock: product.stock,
            quantity: qty
        });
    }

    saveCart();
    updateCartBadge();
    showToast('Added to Cart', `${product.name} added to cart.`, 'success');
}

function updateCartQuantity(productId, newQty) {
    const item = state.cart.find(i => i.product_id === productId);
    if (!item) return;

    const product = state.products.find(p => p.id === productId);
    const maxAvailable = product ? product.stock : item.stock;

    if (newQty <= 0) {
        removeFromCart(productId);
        return;
    }

    if (newQty > maxAvailable) {
        showToast('Stock Limit Exceeded', `Cannot add more than available stock (${maxAvailable}).`, 'warning');
        item.quantity = maxAvailable;
    } else {
        item.quantity = newQty;
    }

    saveCart();
    renderCartDrawer();
    updateCartBadge();
}

function removeFromCart(productId) {
    state.cart = state.cart.filter(item => item.product_id !== productId);
    saveCart();
    renderCartDrawer();
    updateCartBadge();
    showToast('Removed', 'Item removed from cart.', 'info');
}

function saveCart() {
    localStorage.setItem('loom_cart', JSON.stringify(state.cart));
}

function updateCartBadge() {
    const badge = document.getElementById('cart-badge');
    const totalCount = state.cart.reduce((sum, item) => sum + item.quantity, 0);
    if (badge) {
        badge.textContent = totalCount;
        if (totalCount > 0) {
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }
}

function openCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    if (drawer) {
        renderCartDrawer();
        drawer.classList.remove('hidden');
    }
}

function closeCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    if (drawer) drawer.classList.add('hidden');
}

function renderCartDrawer() {
    const container = document.getElementById('cart-items-container');
    const subtotalElem = document.getElementById('cart-subtotal');
    const checkoutBtn = document.getElementById('proceed-checkout-btn');
    if (!container) return;

    if (state.cart.length === 0) {
        container.innerHTML = `
            <div class="text-center py-16 text-slate-400">
                <i class="fa-solid fa-cart-shopping text-5xl mb-3 text-slate-600"></i>
                <p class="text-base font-medium">Your shopping cart is empty.</p>
                <p class="text-xs text-slate-500 mt-1">Explore our catalog and reserve your items!</p>
            </div>
        `;
        if (subtotalElem) subtotalElem.textContent = '$0.00';
        if (checkoutBtn) checkoutBtn.disabled = true;
        return;
    }

    if (checkoutBtn) checkoutBtn.disabled = false;
    let subtotal = 0;

    container.innerHTML = state.cart.map(item => {
        const itemTotal = item.price * item.quantity;
        subtotal += itemTotal;

        return `
            <div class="glass-panel p-4 rounded-xl flex gap-3 items-center border border-slate-800">
                <img src="${item.image_url}" alt="${item.name}" class="w-16 h-16 object-cover rounded-lg bg-slate-900">
                <div class="flex-1 min-w-0">
                    <h4 class="text-sm font-semibold text-white truncate">${item.name}</h4>
                    <span class="text-xs text-emerald-400 font-medium">$${item.price.toFixed(2)} each</span>
                    <div class="flex items-center gap-2 mt-2">
                        <div class="flex items-center bg-slate-800 rounded-lg border border-slate-700">
                            <button onclick="updateCartQuantity(${item.product_id}, ${item.quantity - 1})" class="px-2 py-0.5 text-slate-300 hover:text-white">-</button>
                            <span class="px-2 text-xs font-semibold text-white">${item.quantity}</span>
                            <button onclick="updateCartQuantity(${item.product_id}, ${item.quantity + 1})" class="px-2 py-0.5 text-slate-300 hover:text-white">+</button>
                        </div>
                        <span class="text-xs text-slate-500">Max: ${item.stock}</span>
                    </div>
                </div>
                <div class="text-right">
                    <span class="text-sm font-bold text-white block">$${itemTotal.toFixed(2)}</span>
                    <button onclick="removeFromCart(${item.product_id})" class="text-xs text-rose-400 hover:text-rose-300 mt-1">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    if (subtotalElem) subtotalElem.textContent = `$${subtotal.toFixed(2)}`;
}

// ================= CHECKOUT & RESERVATION =================

function handleProceedToCheckout() {
    if (state.cart.length === 0) return;
    closeCartDrawer();
    openCheckoutModal();
}

function openCheckoutModal() {
    const modal = document.getElementById('checkout-modal');
    if (!modal) return;

    const summaryContainer = document.getElementById('checkout-summary-items');
    const totalElem = document.getElementById('checkout-total-price');

    let subtotal = 0;
    summaryContainer.innerHTML = state.cart.map(item => {
        const itemTotal = item.price * item.quantity;
        subtotal += itemTotal;
        return `
            <div class="flex justify-between items-center text-sm py-1.5 border-b border-slate-800">
                <span class="text-slate-300">${item.name} <span class="text-slate-500 font-semibold">x${item.quantity}</span></span>
                <span class="font-medium text-white">$${itemTotal.toFixed(2)}</span>
            </div>
        `;
    }).join('');

    if (totalElem) totalElem.textContent = `$${subtotal.toFixed(2)}`;
    modal.classList.remove('hidden');
}

async function submitCheckoutForm(e) {
    e.preventDefault();
    const name = document.getElementById('checkout-name').value;
    const email = document.getElementById('checkout-email').value;

    if (!name || !email) {
        showToast('Required Fields', 'Please fill in name and email.', 'warning');
        return;
    }

    const payload = {
        customer_name: name,
        customer_email: email,
        items: state.cart.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity
        }))
    };

    try {
        const res = await fetch('/api/orders/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Checkout failed');
        }

        const order = await res.json();
        state.activeOrder = order;
        state.cart = [];
        saveCart();
        updateCartBadge();
        
        // Refresh catalogue stock
        loadProducts();

        // Close Checkout modal, open Payment Simulator Modal
        document.getElementById('checkout-modal').classList.add('hidden');
        openPaymentGatewayModal(order);
        showToast('Stock Reserved!', `Order #${order.order_number} created with 5-minute expiry timer.`, 'success');

    } catch (err) {
        showToast('Reservation Error', err.message, 'error');
    }
}

// ================= PAYMENT GATEWAY SIMULATOR =================

function openPaymentGatewayModal(order) {
    const modal = document.getElementById('payment-modal');
    if (!modal) return;

    state.activeOrder = order;
    state.idempotencyKey = generateIdempotencyKey();

    document.getElementById('payment-order-number').textContent = order.order_number;
    document.getElementById('payment-amount').textContent = `$${order.total_amount.toFixed(2)}`;
    document.getElementById('idempotency-key-input').value = state.idempotencyKey;

    startCheckoutTimer(order.seconds_remaining || 300);

    modal.classList.remove('hidden');
}

function generateIdempotencyKey() {
    if (crypto && crypto.randomUUID) {
        return `IDEM-${crypto.randomUUID()}`;
    }
    return `IDEM-${Math.random().toString(36).substring(2, 11)}-${Date.now()}`;
}

function startCheckoutTimer(seconds) {
    if (state.countdownInterval) clearInterval(state.countdownInterval);
    
    let remaining = seconds;
    const timerElem = document.getElementById('reservation-countdown');
    const timerProgress = document.getElementById('timer-progress-bar');
    const totalDuration = 300; // 5 mins

    function updateDisplay() {
        if (remaining <= 0) {
            if (timerElem) timerElem.textContent = "00:00 (EXPIRED)";
            if (timerProgress) timerProgress.style.width = "0%";
            clearInterval(state.countdownInterval);
            showToast('Reservation Expired', 'The 5-minute reservation timer has elapsed. Stock released.', 'error');
            return;
        }

        const mins = Math.floor(remaining / 60);
        const secs = remaining % 60;
        const text = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        if (timerElem) timerElem.textContent = text;

        const pct = Math.max(0, (remaining / totalDuration) * 100);
        if (timerProgress) timerProgress.style.width = `${pct}%`;

        remaining--;
    }

    updateDisplay();
    state.countdownInterval = setInterval(updateDisplay, 1000);
}

async function triggerMockPayment(action) {
    if (!state.activeOrder) return;
    const orderId = state.activeOrder.id;
    const idemKey = document.getElementById('idempotency-key-input').value || state.idempotencyKey;
    const method = document.getElementById('payment-method-select').value;

    const payload = {
        idempotency_key: idemKey,
        payment_action: action,
        payment_method: method
    };

    try {
        const res = await fetch(`/api/orders/${orderId}/pay`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Idempotency-Key': idemKey
            },
            body: JSON.stringify(payload)
        });

        const paymentRes = await res.json();
        
        if (!res.ok) {
            throw new Error(paymentRes.detail || 'Payment failed');
        }

        if (state.countdownInterval) clearInterval(state.countdownInterval);
        document.getElementById('payment-modal').classList.add('hidden');

        // Show Confirmation Modal
        openOrderConfirmModal(paymentRes);
        await loadProducts();
        await loadOrders();

    } catch (err) {
        showToast('Payment Error', err.message, 'error');
    }
}

function openOrderConfirmModal(paymentRes) {
    const modal = document.getElementById('confirm-modal');
    if (!modal) return;

    document.getElementById('confirm-order-number').textContent = paymentRes.order_number;
    
    const statusBadge = document.getElementById('confirm-status-badge');
    const msgElem = document.getElementById('confirm-message');
    const idemElem = document.getElementById('confirm-idempotency-key');
    const cachedBadge = document.getElementById('confirm-cached-badge');

    idemElem.textContent = paymentRes.idempotency_key;

    if (paymentRes.cached) {
        cachedBadge.classList.remove('hidden');
    } else {
        cachedBadge.classList.add('hidden');
    }

    if (paymentRes.payment_status === 'SUCCESS') {
        statusBadge.className = "px-3 py-1 text-xs font-bold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40";
        statusBadge.textContent = "STATUS: PAID";
        msgElem.textContent = paymentRes.message;
    } else if (paymentRes.payment_status === 'FAILED') {
        statusBadge.className = "px-3 py-1 text-xs font-bold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40";
        statusBadge.textContent = "STATUS: FAILED";
        msgElem.textContent = paymentRes.message;
    } else {
        statusBadge.className = "px-3 py-1 text-xs font-bold rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/40";
        statusBadge.textContent = "STATUS: TIMEOUT / RESERVED";
        msgElem.textContent = paymentRes.message;
    }

    modal.classList.remove('hidden');
}

// ================= ORDER HISTORY & LIFECYCLE =================

function renderOrders() {
    const container = document.getElementById('orders-list-container');
    if (!container) return;

    if (state.orders.length === 0) {
        container.innerHTML = `
            <div class="glass-panel p-12 text-center text-slate-400 rounded-2xl">
                <i class="fa-solid fa-receipt text-5xl text-slate-600 mb-3"></i>
                <p class="text-base font-medium">No past orders found.</p>
                <button onclick="switchTab('store')" class="mt-4 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-500">Go to Storefront</button>
            </div>
        `;
        return;
    }

    container.innerHTML = state.orders.map(order => {
        let badgeClass = '';
        if (order.status === 'PAID') badgeClass = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
        else if (order.status === 'RESERVED') badgeClass = 'bg-amber-500/20 text-amber-400 border-amber-500/40 animate-pulse-soft';
        else if (order.status === 'FAILED') badgeClass = 'bg-rose-500/20 text-rose-400 border-rose-500/40';
        else if (order.status === 'EXPIRED') badgeClass = 'bg-slate-700/50 text-slate-400 border-slate-600';
        else if (order.status === 'CANCELLED') badgeClass = 'bg-slate-700/50 text-slate-400 border-slate-600';
        else if (order.status === 'REFUNDED') badgeClass = 'bg-purple-500/20 text-purple-400 border-purple-500/40';

        const createdDate = new Date(order.created_at).toLocaleString();

        let actions = '';
        if (order.status === 'RESERVED') {
            actions = `
                <div class="flex gap-2 mt-3">
                    <button onclick="resumePayment(${order.id})" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow">
                        <i class="fa-solid fa-credit-card mr-1"></i> Pay Now (${order.seconds_remaining}s left)
                    </button>
                    <button onclick="cancelOrder(${order.id})" class="px-3 py-1.5 bg-slate-800 hover:bg-rose-900/50 text-rose-400 text-xs font-semibold rounded-lg border border-rose-500/30">
                        Cancel Order
                    </button>
                </div>
            `;
        } else if (order.status === 'PAID') {
            actions = `
                <div class="mt-3">
                    <button onclick="refundOrder(${order.id})" class="px-3 py-1.5 bg-purple-900/50 hover:bg-purple-800/60 text-purple-300 text-xs font-semibold rounded-lg border border-purple-500/40">
                        <i class="fa-solid fa-rotate-left mr-1"></i> Request Refund & Restock
                    </button>
                </div>
            `;
        }

        const itemsList = order.items.map(i => `
            <div class="flex justify-between text-xs py-1 border-b border-slate-800/60">
                <span class="text-slate-300">${i.product_name} x${i.quantity}</span>
                <span class="text-slate-400">$${i.subtotal.toFixed(2)}</span>
            </div>
        `).join('');

        return `
            <div class="glass-panel p-5 rounded-2xl border border-slate-800">
                <div class="flex flex-wrap justify-between items-start gap-2 mb-3">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="text-base font-bold text-white">${order.order_number}</span>
                            <span class="px-2.5 py-0.5 text-xs font-bold rounded-full border ${badgeClass}">
                                ${order.status}
                            </span>
                        </div>
                        <p class="text-xs text-slate-400 mt-1">${order.customer_name} (${order.customer_email}) • ${createdDate}</p>
                    </div>
                    <div class="text-right">
                        <span class="text-lg font-bold text-emerald-400 block">$${order.total_amount.toFixed(2)}</span>
                    </div>
                </div>

                <div class="bg-slate-950/40 p-3 rounded-xl mb-2">
                    <span class="text-xs font-semibold text-slate-400 block mb-1 uppercase tracking-wider">Ordered Items</span>
                    ${itemsList}
                </div>

                ${actions}
            </div>
        `;
    }).join('');
}

async function resumePayment(orderId) {
    const order = state.orders.find(o => o.id === orderId);
    if (!order) return;
    openPaymentGatewayModal(order);
}

async function cancelOrder(orderId) {
    if (!confirm('Are you sure you want to cancel this reserved order? Reserved items will be restored.')) return;
    try {
        const res = await fetch(`/api/orders/${orderId}/cancel`, { method: 'POST' });
        if (!res.ok) throw new Error('Cancellation failed');
        showToast('Cancelled', 'Order cancelled and stock restored to inventory.', 'info');
        await loadProducts();
        await loadOrders();
    } catch (err) {
        showToast('Error', err.message, 'error');
    }
}

async function refundOrder(orderId) {
    if (!confirm('Request refund for this paid order? Items will be restored back to stock.')) return;
    try {
        const res = await fetch(`/api/orders/${orderId}/refund`, { method: 'POST' });
        if (!res.ok) throw new Error('Refund failed');
        showToast('Refunded', 'Order refunded. Stock restored to catalog.', 'success');
        await loadProducts();
        await loadOrders();
    } catch (err) {
        showToast('Error', err.message, 'error');
    }
}

// ================= PRODUCT DETAIL MODAL =================

function openProductDetailModal(productId) {
    const product = state.products.find(p => p.id === productId);
    if (!product) return;

    const modal = document.getElementById('product-detail-modal');
    if (!modal) return;

    document.getElementById('detail-img').src = product.image_url;
    document.getElementById('detail-title').textContent = product.name;
    document.getElementById('detail-category').textContent = product.category;
    document.getElementById('detail-description').textContent = product.description;
    document.getElementById('detail-price').textContent = `$${product.price.toFixed(2)}`;
    document.getElementById('detail-available').textContent = product.stock;
    document.getElementById('detail-reserved').textContent = product.reserved_stock;
    document.getElementById('detail-total').textContent = product.total_stock;

    const addBtn = document.getElementById('detail-add-btn');
    if (addBtn) {
        addBtn.disabled = product.stock <= 0;
        addBtn.onclick = () => {
            const qty = parseInt(document.getElementById('detail-qty').value || '1');
            addToCart(product.id, qty);
            modal.classList.add('hidden');
        };
    }

    modal.classList.remove('hidden');
}

// ================= UTILITIES & TIMERS =================

function startGlobalTimers() {
    setInterval(() => {
        if (state.activeTab === 'orders') {
            renderOrders();
        }
    }, 5000);
}

function showToast(title, message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    
    let icon = 'fa-circle-info text-blue-400';
    let border = 'border-blue-500/40';

    if (type === 'success') {
        icon = 'fa-circle-check text-emerald-400';
        border = 'border-emerald-500/40';
    } else if (type === 'error') {
        icon = 'fa-circle-xmark text-rose-400';
        border = 'border-rose-500/40';
    } else if (type === 'warning') {
        icon = 'fa-triangle-exclamation text-amber-400';
        border = 'border-amber-500/40';
    }

    toast.className = `toast-enter glass-panel p-4 rounded-xl shadow-2xl border ${border} flex items-start gap-3 min-w-[300px] max-w-sm`;
    toast.innerHTML = `
        <i class="fa-solid ${icon} text-lg mt-0.5"></i>
        <div class="flex-1">
            <h5 class="text-sm font-semibold text-white">${title}</h5>
            <p class="text-xs text-slate-300 mt-0.5">${message}</p>
        </div>
        <button onclick="this.parentElement.remove()" class="text-slate-400 hover:text-white text-xs">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('toast-enter');
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ================= ADMIN PANEL FUNCTIONS =================

// ================= ADMIN PANEL FUNCTIONS =================

async function loadAdminProducts() {
    const tbody = document.getElementById('admin-inventory-tbody') || document.getElementById('admin-products-tbody');
    const alertBox = document.getElementById('admin-error-alert');
    const alertMsg = document.getElementById('admin-error-alert-msg');

    if (alertBox) {
        alertBox.classList.add('hidden');
        if (alertMsg) alertMsg.textContent = '';
    }

    if (!tbody) return;

    try {
        const res = await fetch('/api/products');
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Server returned HTTP ${res.status}`);
        }

        const products = await res.json();

        if (!Array.isArray(products) || products.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-8 text-slate-500">
                        No products found in inventory. Add a product above or click "Seed Inventory".
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = products.map(p => `
            <tr class="hover:bg-slate-900/40 transition-colors">
                <td class="py-3 px-4 font-mono text-xs text-slate-400">#${p.id}</td>
                <td class="py-3 px-4">
                    <div class="flex items-center gap-3">
                        <img src="${escapeHtml(p.image_url || '')}" alt="${escapeHtml(p.name || '')}" class="w-8 h-8 rounded-lg object-cover bg-slate-800" onerror="this.src='https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80'">
                        <div>
                            <span class="font-semibold text-white block">${escapeHtml(p.name || '')}</span>
                            <span class="text-[11px] text-slate-400 block truncate max-w-xs">${escapeHtml(p.description || '')}</span>
                        </div>
                    </div>
                </td>
                <td class="py-3 px-4">
                    <span class="px-2 py-0.5 text-xs font-semibold rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                        ${escapeHtml(p.category || 'General')}
                    </span>
                </td>
                <td class="py-3 px-4 font-bold text-emerald-400">$${(parseFloat(p.price) || 0).toFixed(2)}</td>
                <td class="py-3 px-4 font-semibold ${(p.stock || 0) > 0 ? 'text-emerald-400' : 'text-rose-400'}">
                    ${p.stock || 0} units
                </td>
                <td class="py-3 px-4 text-amber-400 font-medium">
                    ${p.reserved_stock || 0} reserved
                </td>
                <td class="py-3 px-4 font-bold text-slate-200">
                    ${p.total_stock !== undefined ? p.total_stock : ((p.stock || 0) + (p.reserved_stock || 0))} total
                </td>
                <td class="py-3 px-4 text-right">
                    <div class="flex items-center gap-2 justify-end">
                        <input type="number" min="1" value="10" id="admin-add-stock-input-${p.id}" 
                            class="w-16 px-2 py-1 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500">
                        <button onclick="handleAddStock(${p.id})" class="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg flex items-center gap-1 shadow-sm transition-all" title="Add Stock Quantity">
                            <i class="fa-solid fa-plus"></i> Add
                        </button>
                        <button onclick="handleDeleteProduct(${p.id}, '${escapeHtml(p.name || '')}')" class="px-2.5 py-1 bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30 text-xs font-semibold rounded-lg flex items-center gap-1 transition-all" title="Delete Product">
                            <i class="fa-solid fa-trash"></i> Delete
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Error loading admin products:', err);
        if (alertBox) {
            if (alertMsg) alertMsg.textContent = `Failed to load products: ${err.message}`;
            else alertBox.textContent = `Failed to load products: ${err.message}`;
            alertBox.classList.remove('hidden');
        }
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-6 text-rose-400 font-medium">
                        <i class="fa-solid fa-triangle-exclamation mr-2"></i>Failed to load product inventory: ${escapeHtml(err.message)}
                    </td>
                </tr>
            `;
        }
        showToast('Error', 'Failed to load admin inventory', 'error');
    }
}

async function loadAdminInventory() {
    return await loadAdminProducts();
}

async function handleDeleteProduct(productId, productName) {
    if (!confirm(`Are you sure you want to delete product "${productName}" (#${productId})?`)) return;

    try {
        const res = await fetch(`/api/products/${productId}`, { method: 'DELETE' });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || 'Failed to delete product');
        }

        showToast('Product Deleted', `Product "${productName}" has been deleted.`, 'info');
        await loadProducts();
        await loadAdminProducts();
    } catch (err) {
        console.error(err);
        showToast('Error', err.message || 'Failed to delete product', 'error');
    }
}

async function handleCreateProduct(e) {
    if (e && e.preventDefault) e.preventDefault();
    const btn = document.getElementById('admin-submit-btn');
    if (btn) btn.disabled = true;

    try {
        const nameElem = document.getElementById('admin-prod-name') || document.getElementById('product-name');
        const catElem = document.getElementById('admin-prod-category') || document.getElementById('product-category');
        const priceElem = document.getElementById('admin-prod-price') || document.getElementById('product-price');
        const stockElem = document.getElementById('admin-prod-stock') || document.getElementById('product-stock');
        const imgElem = document.getElementById('admin-prod-image') || document.getElementById('product-image');
        const descElem = document.getElementById('admin-prod-desc') || document.getElementById('product-description');

        const name = nameElem ? nameElem.value.trim() : '';
        const category = catElem ? catElem.value.trim() : '';
        const price = priceElem ? parseFloat(priceElem.value) : NaN;
        const stock = stockElem ? parseInt(stockElem.value, 10) : NaN;
        const image_url = imgElem ? imgElem.value.trim() : '';
        const description = descElem ? descElem.value.trim() : '';

        if (!name || !category || isNaN(price) || isNaN(stock)) {
            showToast('Validation Error', 'Please fill in all required fields correctly.', 'warning');
            if (btn) btn.disabled = false;
            return;
        }

        const res = await fetch('/api/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, category, price, stock, image_url, description })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || 'Failed to create product');
        }

        const newProd = await res.json();
        showToast('Product Created', `Successfully added "${newProd.name}" to inventory!`, 'success');

        // Reset form
        const form = document.getElementById('admin-create-product-form');
        if (form) form.reset();

        // Refresh products & admin view
        await loadProducts();
        await loadAdminProducts();
    } catch (err) {
        console.error(err);
        showToast('Error', err.message || 'Failed to create product', 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

async function handleAddStock(productId) {
    const input = document.getElementById(`admin-add-stock-input-${productId}`);
    if (!input) return;

    const quantity = parseInt(input.value, 10);
    if (isNaN(quantity) || quantity <= 0) {
        showToast('Invalid Quantity', 'Please enter a valid stock quantity (> 0).', 'warning');
        return;
    }

    try {
        const res = await fetch(`/api/products/${productId}/stock`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || 'Failed to add stock');
        }

        const updatedProd = await res.json();
        showToast('Stock Updated', `Added +${quantity} units to "${updatedProd.name}". New stock: ${updatedProd.stock}`, 'success');

        // Refresh product list and admin inventory
        await loadProducts();
        await loadAdminInventory();
    } catch (err) {
        console.error(err);
        showToast('Error', err.message || 'Failed to update stock', 'error');
    }
}
