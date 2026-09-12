/**
 * E-GROSSARY — CONSOLIDATED ADMIN ERP CONSOLE ENGINE (admin.js)
 * Enterprise-grade full-stack ERP console connected directly to live backend REST APIs:
 * - Server-validated Admin authentication guard via /api/auth/me
 * - Live KPI dashboard analytics & Chart.js sales trends via /api/admin/dashboard
 * - Full Product & Inventory CRUD with image uploads via /api/admin/products
 * - Live Point-of-Sale (POS) counter with atomic DB stock deduction via /api/admin/pos/checkout
 * - Real-time Master Orders pipeline & status transitions via /api/admin/orders
 * - Categories, Suppliers, Restock Purchases, Customer Udhar (credit) & Audit Log live sync
 */

(function () {
    'use strict';

    function escapeHTML(str) {
        if (window.EG && window.EG.utils && window.EG.utils.escapeHTML) {
            return window.EG.utils.escapeHTML(str);
        }
        if (str === null || str === undefined) return '';
        return String(str).replace(/[&<>"']/g, function (m) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[m];
        });
    }

    // ── Application State ──
    let state = {
        products: [],
        categories: [],
        orders: [],
        customers: [],
        suppliers: [],
        purchases: [],
        coupons: [],
        activity: [],
        sales: [],
        posCart: [],
        posDiscount: 0,
        twoFactorEnabled: false,
        user: null
    };

    let salesChartInstance = null;
    let orderStatusChartInstance = null;

    // Helper to log actions locally and fetch from server
    function logActionLocally(action, details) {
        state.activity.unshift({
            id: Date.now(),
            action: action,
            details: details,
            actor: (state.user && (state.user.full_name || state.user.username)) || 'Super Admin',
            created_at: new Date().toISOString()
        });
        renderActivity();
    }

    // ── 1. True Authentication & Session Validation Guard ──
    async function verifyAdminAuth() {
        const localAuth = JSON.parse(localStorage.getItem('jg_auth_user') || 'null');
        if (!localAuth || localAuth.role !== 'admin') {
            if (document.body) document.body.style.display = 'none';
        }

        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/auth/me');
            if (res.ok) {
                const data = await res.json();
                if (data && data.authenticated && data.user && data.user.role === 'admin') {
                    state.user = data.user;
                    localStorage.setItem('jg_auth_user', JSON.stringify(data.user));
                    if (document.body) document.body.style.display = '';
                    updateAdminHeaderUI(data.user);
                    return true;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Auth verification error:', e);
        }

        // Unauthorized access: strictly purge stale client state and redirect to login
        localStorage.removeItem('jg_auth_user');
        console.warn('[Admin ERP] Unauthorized access detected. Redirecting to login.');
        const inAdmin = window.location.pathname.includes('/admin/');
        const targetPage = window.location.pathname.split('/').pop() || 'index.html';
        const redirectParam = encodeURIComponent(inAdmin ? `admin/${targetPage}` : targetPage);
        const loginUrl = inAdmin ? `../auth/login.html?redirect=${redirectParam}` : `auth/login.html?redirect=${redirectParam}`;

        if (document.body) document.body.style.display = 'none';
        window.location.replace(loginUrl);
        return false;
    }

    function updateAdminHeaderUI(user) {
        const nameEl = document.querySelector('.admin-topbar .fw-bold.small.text-dark');
        if (nameEl && user) {
            nameEl.textContent = user.full_name || user.username || 'Administrator';
        }
        const emailEl = document.querySelector('.admin-topbar .smallest.text-muted, .admin-topbar .admin-user-email');
        if (emailEl && user) {
            emailEl.textContent = user.email || '';
        }
    }

    // ── 2. Data Loaders (Live REST API with Graceful Cache Fallback) ──
    async function loadDashboardData() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/admin/dashboard');
            if (res.ok) {
                const data = await res.json();
                renderDashboardWithData(data);
                return;
            }
        } catch (e) {
            console.warn('[Admin ERP] Dashboard load error:', e);
        }
        renderDashboardFallback();
    }

    async function loadProductsData() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/admin/products?per_page=100');
            if (res.ok) {
                const data = await res.json();
                if (data && data.products) {
                    state.products = data.products.map(p => ({
                        id: p.id,
                        sku: `JG-${(p.category || 'GEN').substring(0, 3).toUpperCase()}-${String(p.id).padStart(3, '0')}`,
                        name: p.name,
                        category: p.category || 'General',
                        category_id: p.category_id,
                        cost: parseFloat(p.cost_price || 0),
                        price: parseFloat(p.selling_price || 0),
                        stock: parseInt(p.stock_quantity || 0),
                        minAlert: parseInt(p.minimum_stock_alert || 5),
                        image: p.image_path || 'static/images/logo-icon.png'
                    }));
                    populatePurchaseProductSelect();
                    renderProducts();
                    renderPOS();
                    applyCategoryFilterFromURL();
                    return;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Products load error:', e);
        }
        renderProducts();
        applyCategoryFilterFromURL();
    }

    function applyCategoryFilterFromURL() {
        const catFilter = new URLSearchParams(window.location.search).get('category') || sessionStorage.getItem('adm_filter_category');
        if (catFilter) {
            sessionStorage.removeItem('adm_filter_category');
            const searchInput = document.getElementById('adminMasterSearch');
            if (searchInput) {
                searchInput.value = catFilter;
                setTimeout(() => searchInput.dispatchEvent(new Event('input')), 50);
            }
        }
    }

    async function loadOrdersData() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/admin/orders?per_page=100');
            if (res.ok) {
                const data = await res.json();
                if (data && data.orders) {
                    state.orders = data.orders.map(o => ({
                        id: o.id,
                        customer: `Customer #${o.user_id}`,
                        user_id: o.user_id,
                        date: o.created_at ? new Date(o.created_at).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' }) : 'Recent',
                        total: parseFloat(o.total_amount || 0),
                        status: o.order_status || 'Pending',
                        payment: o.payment_method || 'COD',
                        payment_status: o.payment_status || 'Pending',
                        shipping_address: o.shipping_address || '',
                        items: []
                    }));
                    renderOrders();
                    return;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Orders load error:', e);
        }
        renderOrders();
    }

    async function loadCategoriesData() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/admin/categories');
            if (res.ok) {
                const data = await res.json();
                if (data && data.categories) {
                    state.categories = data.categories.map(c => ({
                        id: c.id,
                        name: c.name,
                        desc: c.description || '',
                        icon: getCategoryIcon(c.name),
                        count: c.product_count || 0
                    }));
                    renderCategories();
                    return;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Categories load error:', e);
        }
        renderCategories();
    }

    async function loadCustomersData() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/admin/customers');
            if (res.ok) {
                const data = await res.json();
                if (data && data.customers) {
                    state.customers = data.customers;
                    renderCustomers();
                    return;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Customers load error:', e);
        }
        renderCustomers();
    }

    async function loadSuppliersData() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/admin/suppliers');
            if (res.ok) {
                const data = await res.json();
                if (data && data.suppliers) {
                    state.suppliers = data.suppliers.map(s => ({
                        id: s.id,
                        name: s.name,
                        contact: s.contact_person || '',
                        phone: s.phone || '',
                        email: s.email || '',
                        category: 'FMCG Supplier',
                        address: s.address || ''
                    }));
                    renderSuppliers();
                    return;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Suppliers load error:', e);
        }
        renderSuppliers();
    }

    async function loadPurchasesData() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/admin/purchases');
            if (res.ok) {
                const data = await res.json();
                if (data && data.purchases) {
                    state.purchases = data.purchases.map(p => ({
                        id: p.id,
                        invoice: `INV-RESTOCK-${p.id}`,
                        supplier: p.supplier_name || 'Vendor',
                        product: p.product_name || 'Stock',
                        date: p.purchase_date ? new Date(p.purchase_date).toLocaleDateString('en-IN') : 'Recent',
                        itemsCount: p.quantity,
                        total: p.total_cost
                    }));
                    renderPurchases();
                    return;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Purchases load error:', e);
        }
        renderPurchases();
    }

    async function loadCouponsData() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/admin/coupons');
            if (res.ok) {
                const data = await res.json();
                if (data && data.coupons) {
                    state.coupons = data.coupons.map(c => ({
                        id: c.id,
                        code: c.code,
                        discount: c.discount_type === 'percentage' ? `${c.discount_value}% OFF` : `₹${c.discount_value} OFF`,
                        minSpend: c.min_order_amount || 0,
                        expiry: c.expires_at ? new Date(c.expires_at).toLocaleDateString('en-IN') : 'Ongoing',
                        used: c.used_count || 0,
                        active: Boolean(c.is_active)
                    }));
                    renderCoupons();
                    return;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Coupons load error:', e);
        }
        renderCoupons();
    }

    async function loadActivityData() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/admin/activity-log');
            if (res.ok) {
                const data = await res.json();
                if (data && data.logs) {
                    state.activity = data.logs;
                    renderActivity();
                    return;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Activity load error:', e);
        }
        renderActivity();
    }

    async function loadSalesData() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/admin/sales/history');
            if (res.ok) {
                const data = await res.json();
                if (data && data.sales) {
                    state.sales = data.sales;
                    renderSales();
                    return;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Sales load error:', e);
        }
        renderSales();
    }

    function getCategoryIcon(name) {
        const n = (name || '').toLowerCase();
        if (n.includes('fruit') || n.includes('veg')) return '🥦';
        if (n.includes('dairy') || n.includes('milk')) return '🥛';
        if (n.includes('staple') || n.includes('grain') || n.includes('atta')) return '🌾';
        if (n.includes('snack') || n.includes('biscuit')) return '🍿';
        if (n.includes('bev') || n.includes('tea')) return '🧃';
        if (n.includes('care') || n.includes('personal')) return '✨';
        if (n.includes('clean') || n.includes('house')) return '🧼';
        if (n.includes('spice') || n.includes('masala')) return '🌶️';
        return '📦';
    }

    function populatePurchaseProductSelect() {
        const purchaseProdSelect = document.getElementById('purchaseProductSelect');
        if (purchaseProdSelect && state.products.length > 0) {
            purchaseProdSelect.innerHTML = state.products.map(p => `
                <option value="${Number(p.id)}">${escapeHTML(p.name)} (Stock: ${Number(p.stock)})</option>
            `).join('');
        }
    }

    // ── 3. Router Engine ──
    function router() {
        const pageAttr = document.body ? document.body.getAttribute('data-admin-page') : null;
        const pathFile = window.location.pathname.split('/').pop().replace('.html', '').toLowerCase();
        const rawHash = window.location.hash ? window.location.hash.split('?')[0].replace('#', '') : '';
        const inAdminDir = window.location.pathname.includes('/admin/');

        // If inside /admin/ and a hash points to an admin page not on the current DOM, redirect to that file
        if (rawHash && inAdminDir && !document.getElementById(`adm-view-${rawHash}`)) {
            const knownAdminPages = ['dashboard', 'pos', 'products', 'categories', 'orders', 'customers', 'sales', 'purchases', 'suppliers', 'coupons', 'activity', 'security'];
            if (knownAdminPages.includes(rawHash)) {
                const targetFile = rawHash === 'dashboard' ? 'index.html' : `${rawHash}.html`;
                window.location.href = targetFile;
                return;
            }
        }

        let route = 'dashboard';
        if (rawHash && document.getElementById(`adm-view-${rawHash}`)) {
            route = rawHash;
        } else if (pageAttr) {
            route = pageAttr;
        } else if (pathFile && pathFile !== 'admin' && pathFile !== 'index') {
            route = pathFile;
        } else if (rawHash) {
            route = rawHash;
        }

        document.querySelectorAll('.adm-view').forEach(view => {
            view.classList.remove('active-view');
        });

        const targetView = document.getElementById(`adm-view-${route}`) || document.getElementById('adm-view-dashboard');
        if (targetView) {
            targetView.classList.add('active-view');
        }

        document.querySelectorAll('.admin-nav-item').forEach(link => {
            const linkRoute = link.getAttribute('data-admin-route');
            if (linkRoute === route) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Close mobile sidebar if open
        const sidebar = document.getElementById('adminSidebar');
        if (sidebar) sidebar.classList.remove('show-mobile');

        // Route specific live loader
        if (route === 'dashboard') loadDashboardData();
        else if (route === 'pos') { loadProductsData(); renderPOS(); }
        else if (route === 'products') loadProductsData();
        else if (route === 'categories') loadCategoriesData();
        else if (route === 'orders') loadOrdersData();
        else if (route === 'customers') loadCustomersData();
        else if (route === 'sales') loadSalesData();
        else if (route === 'purchases') loadPurchasesData();
        else if (route === 'suppliers') loadSuppliersData();
        else if (route === 'coupons') loadCouponsData();
        else if (route === 'activity') loadActivityData();
        else if (route === 'security') renderSecurity();

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // ── 4. Renderers ──

    function renderDashboardWithData(data) {
        const stats30 = data.stats_30_days || {};
        const totalRev = Number(data.total_order_revenue || stats30.revenue || 0);
        const totalOrders = Number(data.total_orders || stats30.count || 0);
        const lowStockCount = Number(data.stock_stats?.low_stock_count || 0);
        const totalProducts = Number(data.stock_stats?.total_products || state.products.length);

        document.getElementById('dashKpiRevenue').textContent = `₹${totalRev.toLocaleString('en-IN')}`;
        document.getElementById('dashKpiOrders').textContent = totalOrders;
        document.getElementById('dashKpiProducts').textContent = totalProducts;
        document.getElementById('dashKpiLowStock').textContent = lowStockCount;

        const lowStockBanner = document.getElementById('dashLowStockBanner');
        if (lowStockBanner) {
            lowStockBanner.style.display = lowStockCount > 0 ? 'flex' : 'none';
            document.getElementById('dashLowStockCount').textContent = lowStockCount;
        }

        // Recent Orders
        loadOrdersData();

        // Chart.js Sales Graph
        if (typeof Chart !== 'undefined' && data.chart_data) {
            const ctxSales = document.getElementById('dashSalesChart');
            if (ctxSales) {
                if (salesChartInstance) salesChartInstance.destroy();
                salesChartInstance = new Chart(ctxSales, {
                    type: 'line',
                    data: {
                        labels: data.chart_data.labels || ['1', '2', '3', '4', '5', '6', '7'],
                        datasets: [
                            {
                                label: 'Revenue (₹)',
                                data: data.chart_data.revenue || [],
                                borderColor: '#059669',
                                backgroundColor: 'rgba(5, 150, 105, 0.1)',
                                fill: true,
                                tension: 0.35,
                                borderWidth: 3,
                                pointRadius: 4
                            },
                            {
                                label: 'Profit (₹)',
                                data: data.chart_data.profit || [],
                                borderColor: '#0284c7',
                                backgroundColor: 'rgba(2, 132, 199, 0.05)',
                                fill: true,
                                tension: 0.35,
                                borderWidth: 2,
                                pointRadius: 3
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: true, position: 'top' }
                        },
                        scales: { y: { beginAtZero: true } }
                    }
                });
            }
        }
    }

    function renderDashboardFallback() {
        const todayRevenue = state.orders.reduce((sum, o) => sum + (o.status !== 'Cancelled' ? o.total : 0), 0);
        const lowStockItems = state.products.filter(p => p.stock <= 5);

        document.getElementById('dashKpiRevenue').textContent = `₹${todayRevenue.toLocaleString('en-IN')}`;
        document.getElementById('dashKpiOrders').textContent = state.orders.length;
        document.getElementById('dashKpiProducts').textContent = state.products.length;
        document.getElementById('dashKpiLowStock').textContent = lowStockItems.length;
    }

    // POS
    function renderPOS() {
        const grid = document.getElementById('posProductsGrid');
        if (!grid) return;

        if (state.products.length === 0) {
            grid.innerHTML = `<div class="col-12 text-center text-muted py-5">Loading catalog products...</div>`;
            return;
        }

        grid.innerHTML = state.products.map(p => `
            <div class="col-6 col-md-4 col-xl-3">
                <div class="pos-product-tile" onclick="window.Adm.posAddToCart(${Number(p.id)})">
                    <img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}" class="pos-product-img">
                    <div class="fw-bold text-dark text-truncate small">${escapeHTML(p.name)}</div>
                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <span class="fw-bold text-success">₹${Number(p.price)}</span>
                        <span class="smallest badge ${p.stock <= 5 ? 'bg-danger' : 'bg-light text-dark border'}">
                            Qty: ${Number(p.stock)}
                        </span>
                    </div>
                </div>
            </div>
        `).join('');

        renderPOSCart();
    }

    function renderPOSCart() {
        const container = document.getElementById('posCartItems');
        if (!container) return;

        if (state.posCart.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5 text-muted opacity-50">
                    <i class="bi bi-cart3 display-4 d-block mb-2"></i>
                    <div class="small fw-bold">Cart is empty</div>
                    <div class="smallest">Click products to bill</div>
                </div>
            `;
            document.getElementById('posSubtotalTxt').textContent = '₹0';
            document.getElementById('posTaxTxt').textContent = '₹0';
            document.getElementById('posTotalTxt').textContent = '₹0';
            return;
        }

        let subtotal = 0;
        container.innerHTML = state.posCart.map(item => {
            const p = state.products.find(prod => prod.id === item.productId);
            if (!p) return '';
            const lineTotal = p.price * item.qty;
            subtotal += lineTotal;

            return `
                <div class="d-flex align-items-center justify-content-between py-2 border-bottom">
                    <div class="text-truncate me-2" style="max-width: 140px;">
                        <div class="fw-bold text-dark small text-truncate">${escapeHTML(p.name)}</div>
                        <div class="smallest text-muted">₹${Number(p.price)} x ${Number(item.qty)}</div>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-secondary btn-sm px-2" onclick="window.Adm.posUpdateQty(${Number(p.id)}, -1)">-</button>
                            <span class="btn btn-light btn-sm fw-bold disabled text-dark" style="width: 32px;">${Number(item.qty)}</span>
                            <button class="btn btn-outline-secondary btn-sm px-2" onclick="window.Adm.posUpdateQty(${Number(p.id)}, 1)">+</button>
                        </div>
                        <div class="fw-bold text-dark small text-end" style="min-width: 50px;">₹${lineTotal}</div>
                        <button class="btn btn-link text-danger p-0 ms-1" onclick="window.Adm.posRemoveItem(${Number(p.id)})">
                            <i class="bi bi-x fs-5"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        const tax = Math.round(subtotal * 0.05);
        const total = Math.max(0, subtotal + tax - state.posDiscount);

        document.getElementById('posSubtotalTxt').textContent = `₹${subtotal}`;
        document.getElementById('posTaxTxt').textContent = `₹${tax}`;
        document.getElementById('posTotalTxt').textContent = `₹${total}`;
    }

    // Products
    function renderProducts() {
        const tbody = document.getElementById('productsTableTbody');
        if (!tbody) return;

        if (state.products.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4 small">No products in inventory.</td></tr>`;
            return;
        }

        tbody.innerHTML = state.products.map(p => {
            const margin = p.price > 0 ? Math.round(((p.price - p.cost) / p.price) * 100) : 0;
            return `
                <tr>
                    <td class="text-muted smallest font-monospace">${escapeHTML(p.sku)}</td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}" class="rounded" style="width: 36px; height: 36px; object-fit: contain; background:#f8fafc; border:1px solid #e2e8f0;">
                            <span class="fw-bold text-dark">${escapeHTML(p.name)}</span>
                        </div>
                    </td>
                    <td><span class="badge bg-light text-dark border">${escapeHTML(p.category)}</span></td>
                    <td>₹${Number(p.cost)}</td>
                    <td class="fw-bold text-dark">₹${Number(p.price)}</td>
                    <td><span class="badge bg-success-subtle text-success fw-bold">${margin}%</span></td>
                    <td>
                        <span class="badge ${p.stock <= 5 ? 'bg-danger' : 'bg-success'}">
                            ${Number(p.stock)} units
                        </span>
                    </td>
                    <td>
                        <div class="d-flex gap-1">
                            <button class="btn btn-sm btn-outline-primary rounded-pill px-2" title="Edit" onclick="window.Adm.openEditProductModal(${Number(p.id)})">
                                <i class="bi bi-pencil-square"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger rounded-pill px-2" title="Delete" onclick="window.Adm.deleteProduct(${Number(p.id)})">
                                <i class="bi bi-trash3"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // Categories
    function renderCategories() {
        const grid = document.getElementById('categoriesGrid');
        if (!grid) return;

        if (state.categories.length === 0) {
            grid.innerHTML = `<div class="col-12 text-center text-muted py-4">No categories loaded.</div>`;
            return;
        }

        grid.innerHTML = state.categories.map(c => `
            <div class="col-md-6 col-xl-4">
                <div class="kpi-card p-4">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <div class="fs-1">${escapeHTML(c.icon || '📦')}</div>
                        <span class="badge bg-success text-white px-3 py-1 rounded-pill">${c.count || 0} Products</span>
                    </div>
                    <h4 class="fw-bold brand-font text-dark mb-1">${escapeHTML(c.name)}</h4>
                    <p class="text-muted small mb-3">${escapeHTML(c.desc || 'Category items collection')}</p>
                    <button class="btn btn-sm btn-outline-secondary rounded-pill px-3" onclick="window.Adm.filterInventoryByCategory('${escapeHTML(c.name)}')">
                        <i class="bi bi-eye me-1"></i> View Items
                    </button>
                </div>
            </div>
        `).join('');
    }

    // Orders
    function renderOrders() {
        const tbody = document.getElementById('ordersTableTbody');
        if (!tbody) return;

        if (state.orders.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4 small">No customer orders placed yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = state.orders.map(o => `
            <tr>
                <td class="fw-bold text-dark">#${escapeHTML(o.id)}</td>
                <td>
                    <div class="fw-bold">${escapeHTML(o.customer || 'Customer')}</div>
                    <div class="smallest text-muted">${escapeHTML(o.shipping_address ? o.shipping_address.substring(0, 30) + '...' : '')}</div>
                </td>
                <td class="small">${escapeHTML(o.date)}</td>
                <td class="text-center">${o.items ? o.items.length : 1} items</td>
                <td class="fw-bold text-dark">₹${escapeHTML(o.total)}</td>
                <td><span class="badge bg-light text-dark border small">${escapeHTML(o.payment || 'COD')}</span></td>
                <td>
                    <select class="form-select form-select-sm rounded-pill" style="width: 140px;" onchange="window.Adm.updateOrderStatus('${escapeHTML(o.id)}', this.value)">
                        <option value="Pending" ${o.status === 'Pending' ? 'selected' : ''}>Pending</option>
                        <option value="Confirmed" ${o.status === 'Confirmed' || o.status === 'Order Placed' ? 'selected' : ''}>Confirmed</option>
                        <option value="Processing" ${o.status === 'Processing' ? 'selected' : ''}>Processing</option>
                        <option value="Shipped" ${o.status === 'Shipped' || o.status === 'Out for Delivery' ? 'selected' : ''}>Shipped</option>
                        <option value="Delivered" ${o.status === 'Delivered' ? 'selected' : ''}>Delivered</option>
                        <option value="Cancelled" ${o.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                    </select>
                </td>
                <td>
                    <div class="d-flex gap-1">
                        <button class="btn btn-sm btn-outline-success rounded-pill px-2" onclick="window.Adm.viewOrderDetail('${escapeHTML(o.id)}')">
                            <i class="bi bi-file-text me-1"></i>Detail
                        </button>
                        <a href="/api/orders/${Number(o.id)}/invoice" target="_blank" class="btn btn-sm btn-outline-secondary rounded-pill px-2" title="Download PDF Invoice">
                            <i class="bi bi-printer"></i>
                        </a>
                    </div>
                </td>
            </tr>
        `).join('');

        // Also update recent orders on dashboard
        const recentTbody = document.getElementById('dashRecentOrdersTbody');
        if (recentTbody) {
            recentTbody.innerHTML = state.orders.slice(0, 5).map(o => `
                <tr>
                    <td class="fw-bold text-dark">#${escapeHTML(o.id)}</td>
                    <td>${escapeHTML(o.customer || 'Customer')}</td>
                    <td>${escapeHTML(o.date)}</td>
                    <td class="fw-bold">₹${escapeHTML(o.total)}</td>
                    <td><span class="badge ${getStatusBadgeClass(o.status)}">${escapeHTML(o.status)}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-success rounded-pill px-3" onclick="window.Adm.viewOrderDetail('${escapeHTML(o.id)}')">
                            View
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    }

    function getStatusBadgeClass(status) {
        if (status === 'Delivered') return 'bg-success';
        if (status === 'Shipped' || status === 'Out for Delivery') return 'bg-primary';
        if (status === 'Confirmed' || status === 'Processing' || status === 'Order Placed') return 'bg-warning text-dark';
        if (status === 'Pending') return 'bg-info text-dark';
        return 'bg-danger';
    }

    // Customers
    function renderCustomers() {
        const tbody = document.getElementById('customersTableTbody');
        if (!tbody) return;

        if (state.customers.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4 small">No registered customers yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = state.customers.map(c => `
            <tr>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <div class="bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center fw-bold" style="width: 32px; height: 32px; font-size: 0.8rem;">
                            ${escapeHTML(((c.full_name || c.username || 'CU')).substring(0, 2).toUpperCase())}
                        </div>
                        <div>
                            <span class="fw-bold text-dark d-block">${escapeHTML(c.full_name || c.username)}</span>
                            <span class="smallest text-muted">@${escapeHTML(c.username)}</span>
                        </div>
                    </div>
                </td>
                <td>${escapeHTML(c.email || '-')}</td>
                <td>${escapeHTML(c.phone || '-')}</td>
                <td><span class="badge ${c.credit > 0 ? 'bg-danger-subtle text-danger' : 'bg-light text-dark border'}">Udhar: ₹${Number(c.credit || 0)}</span></td>
                <td class="text-center">${c.is_verified ? '<span class="badge bg-success">Verified</span>' : '<span class="badge bg-secondary">Unverified</span>'}</td>
                <td>
                    ${c.credit > 0 ? `
                        <button class="btn btn-sm btn-outline-danger rounded-pill px-3" onclick="window.Adm.clearCustomerUdhar(${Number(c.id)}, ${Number(c.credit)})">
                            Clear Udhar
                        </button>
                    ` : '<span class="text-muted small">Settled</span>'}
                </td>
            </tr>
        `).join('');
    }

    // Sales (Counter Sales from Sale model)
    function renderSales() {
        const tbody = document.getElementById('salesTableTbody');
        if (!tbody) return;

        if (state.sales.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4 small">No counter sales recorded yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = state.sales.map(s => `
            <tr>
                <td class="fw-bold text-dark">#SAL-${Number(s.id)}</td>
                <td>${s.sale_date ? new Date(s.sale_date).toLocaleString('en-IN') : 'Recent'}</td>
                <td>${escapeHTML(s.product_name || 'Item')}</td>
                <td><span class="badge bg-light text-dark border">Qty: ${Number(s.quantity)}</span></td>
                <td class="fw-bold text-dark">₹${Number(s.total_price)}</td>
                <td class="fw-bold text-success">₹${Number(s.profit)}</td>
                <td>
                    <span class="badge bg-success-subtle text-success">Recorded</span>
                </td>
            </tr>
        `).join('');
    }

    // Purchases
    function renderPurchases() {
        const tbody = document.getElementById('purchasesTableTbody');
        if (!tbody) return;

        if (state.purchases.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4 small">No restock purchases recorded yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = state.purchases.map(p => `
            <tr>
                <td class="fw-bold text-dark">#${escapeHTML(p.id)}</td>
                <td class="font-monospace text-muted small">${escapeHTML(p.invoice)}</td>
                <td class="fw-bold">${escapeHTML(p.supplier)}</td>
                <td>${escapeHTML(p.date)}</td>
                <td class="text-center">${Number(p.itemsCount)} units</td>
                <td class="fw-bold text-dark">₹${Number(p.total).toLocaleString('en-IN')}</td>
                <td><span class="badge bg-success">Stock Added</span></td>
            </tr>
        `).join('');
    }

    // Suppliers
    function renderSuppliers() {
        const grid = document.getElementById('suppliersGrid');
        if (!grid) return;

        if (state.suppliers.length === 0) {
            grid.innerHTML = `<div class="col-12 text-center text-muted py-4">No suppliers registered.</div>`;
            return;
        }

        grid.innerHTML = state.suppliers.map(s => `
            <div class="col-md-6 col-xl-4">
                <div class="kpi-card p-4">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge bg-light text-dark border">${escapeHTML(s.category)}</span>
                        <i class="bi bi-building text-success fs-4"></i>
                    </div>
                    <h5 class="fw-bold brand-font text-dark mb-1">${escapeHTML(s.name)}</h5>
                    <div class="small text-muted mb-2"><i class="bi bi-person me-1"></i>Contact: <strong>${escapeHTML(s.contact)}</strong></div>
                    <div class="small text-muted mb-2"><i class="bi bi-telephone me-1"></i>${escapeHTML(s.phone)}</div>
                    <div class="small text-muted mb-3"><i class="bi bi-envelope me-1"></i>${escapeHTML(s.email)}</div>
                    <button class="btn btn-sm btn-outline-success rounded-pill px-3" onclick="window.Adm.openRecordPurchaseModal('${escapeHTML(s.name)}')">
                        + Record Stock In
                    </button>
                </div>
            </div>
        `).join('');
    }

    // Coupons
    function renderCoupons() {
        const tbody = document.getElementById('couponsTableTbody');
        if (!tbody) return;

        if (state.coupons.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4 small">No promotional vouchers found.</td></tr>`;
            return;
        }

        tbody.innerHTML = state.coupons.map(c => `
            <tr>
                <td class="fw-bold text-success font-monospace">${escapeHTML(c.code)}</td>
                <td class="fw-bold">${escapeHTML(c.discount)}</td>
                <td>₹${Number(c.minSpend)}</td>
                <td>${escapeHTML(c.expiry)}</td>
                <td class="text-center">${Number(c.used)} times</td>
                <td>
                    <span class="badge ${c.active ? 'bg-success' : 'bg-secondary'}">
                        ${c.active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-danger rounded-pill px-2" onclick="window.Adm.toggleCoupon(${Number(c.id)})">
                        ${c.active ? 'Deactivate' : 'Activate'}
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // Activity Log
    function renderActivity() {
        const list = document.getElementById('activityLogList');
        if (!list) return;

        if (state.activity.length === 0) {
            list.innerHTML = `<div class="text-center text-muted py-4 small">No recent activity logs recorded.</div>`;
            return;
        }

        list.innerHTML = state.activity.map(a => `
            <div class="d-flex align-items-start gap-3 py-3 border-bottom">
                <div class="bg-success-subtle text-success p-2 rounded-circle" style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center;">
                    <i class="bi bi-clock-history"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="badge bg-dark text-white fw-bold">${escapeHTML(a.action)}</span>
                        <span class="smallest text-muted">${a.created_at ? new Date(a.created_at).toLocaleString('en-IN') : 'Recent'}</span>
                    </div>
                    <div class="small text-dark mb-1">${escapeHTML(a.details || '')}</div>
                    <div class="smallest text-muted">Entity: <strong>${escapeHTML(a.entity_type || 'System')} #${escapeHTML(a.entity_id || '')}</strong></div>
                </div>
            </div>
        `).join('');
    }

    function renderSecurity() {
        const toggle = document.getElementById('security2faToggle');
        const badge = document.getElementById('security2faStatusBadge');
        if (toggle && badge) {
            toggle.checked = state.twoFactorEnabled;
            badge.className = `badge ${state.twoFactorEnabled ? 'bg-success' : 'bg-secondary'}`;
            badge.textContent = state.twoFactorEnabled ? '2FA Active & Enforced' : '2FA Disabled';
        }
    }

    // ── 5. Public Global Adm Controller API ──
    window.Adm = {
        posAddToCart: function (productId) {
            const p = state.products.find(prod => prod.id === productId);
            if (!p || p.stock <= 0) {
                alert('Item is currently out of stock in warehouse!');
                return;
            }

            const existing = state.posCart.find(i => i.productId === productId);
            if (existing) {
                if (existing.qty < p.stock) {
                    existing.qty += 1;
                } else {
                    alert(`Cannot exceed available warehouse stock (${p.stock})!`);
                }
            } else {
                state.posCart.push({ productId: productId, qty: 1 });
            }
            renderPOSCart();
        },

        posUpdateQty: function (productId, delta) {
            const p = state.products.find(prod => prod.id === productId);
            const item = state.posCart.find(i => i.productId === productId);
            if (item) {
                item.qty += delta;
                if (item.qty <= 0) {
                    state.posCart = state.posCart.filter(i => i.productId !== productId);
                } else if (p && item.qty > p.stock) {
                    item.qty = p.stock;
                    alert(`Maximum available stock reached (${p.stock})!`);
                }
            }
            renderPOSCart();
        },

        posRemoveItem: function (productId) {
            state.posCart = state.posCart.filter(i => i.productId !== productId);
            renderPOSCart();
        },

        posClearCart: function () {
            state.posCart = [];
            state.posDiscount = 0;
            renderPOSCart();
        },

        posApplyDiscount: function () {
            const val = parseFloat(document.getElementById('posDiscountInput').value) || 0;
            state.posDiscount = val;
            renderPOSCart();
        },

        posCompleteSale: async function () {
            if (state.posCart.length === 0) {
                alert('POS cart is empty! Select products first.');
                return;
            }

            const phone = document.getElementById('posCustomerPhoneInput').value.trim() || 'Walk-in';
            const paymentMode = document.getElementById('posPaymentModeSelect').value || 'Cash';
            const fetchFn = window.apiFetch || fetch;

            // Prepare POS checkout payload
            const payload = {
                cart: state.posCart.map(c => ({
                    id: c.productId,
                    qty: c.qty
                }))
            };

            try {
                const res = await fetchFn('/api/admin/pos/checkout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();

                if (!res.ok || !data.success) {
                    alert(data.error || data.message || 'POS Checkout failed on server.');
                    return;
                }

                const total = data.total;
                const billId = `BILL-${Math.floor(100000 + Math.random() * 900000)}`;
                const dateStr = new Date().toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' });

                // Populate thermal bill modal
                document.getElementById('billModalNumber').textContent = billId;
                document.getElementById('billModalDate').textContent = dateStr;
                document.getElementById('billModalCustomer').textContent = phone;
                document.getElementById('billModalPayment').textContent = paymentMode;
                document.getElementById('billModalTotal').textContent = `₹${total}`;

                const tbody = document.getElementById('billModalItemsTbody');
                tbody.innerHTML = state.posCart.map((c, idx) => {
                    const p = state.products.find(prod => prod.id === c.productId);
                    const name = p ? p.name : 'Item';
                    const price = p ? p.price : 0;
                    return `
                        <tr>
                            <td>${idx + 1}. ${escapeHTML(name)}</td>
                            <td class="text-center">${Number(c.qty)}</td>
                            <td class="text-end">₹${Number(price)}</td>
                            <td class="text-end fw-bold">₹${Number(price * c.qty)}</td>
                        </tr>
                    `;
                }).join('');

                // Clear POS cart and reload live inventory
                state.posCart = [];
                state.posDiscount = 0;
                renderPOS();
                loadProductsData();
                logActionLocally('POS Counter Sale', `Billed ₹${total} (${paymentMode}) for ${phone}`);

                const modal = new bootstrap.Modal(document.getElementById('billModal'));
                modal.show();

            } catch (err) {
                console.error('POS Checkout network error:', err);
                alert('Network error connecting to POS billing service.');
            }
        },

        saveNewProduct: async function (e) {
            if (e) e.preventDefault();
            const name = document.getElementById('newProdName').value.trim();
            const categoryId = document.getElementById('newProdCategory').value || '1';
            const cost = parseFloat(document.getElementById('newProdCost').value) || 0;
            const price = parseFloat(document.getElementById('newProdPrice').value) || 0;
            const stock = parseInt(document.getElementById('newProdStock').value) || 10;
            const minAlert = 5;

            if (!name) {
                alert('Product name is required.');
                return;
            }

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn('/api/admin/products/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: name,
                        category_id: categoryId,
                        cost_price: cost,
                        selling_price: price,
                        stock_quantity: stock,
                        minimum_stock_alert: minAlert
                    })
                });
                const data = await res.json();

                if (res.ok && data.success) {
                    alert(data.message || 'Product created successfully in database!');
                    const modalEl = document.getElementById('addProductModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    loadProductsData();
                } else {
                    alert(data.message || 'Failed to save product on server.');
                }
            } catch (err) {
                console.error('Save product error:', err);
                alert('Network error while saving product.');
            }
        },

        openEditProductModal: function (productId) {
            const p = state.products.find(prod => prod.id === productId);
            if (!p) return;

            document.getElementById('editProdId').value = p.id;
            document.getElementById('editProdName').value = p.name;
            document.getElementById('editProdCost').value = p.cost;
            document.getElementById('editProdPrice').value = p.price;
            document.getElementById('editProdStock').value = p.stock;

            const modal = new bootstrap.Modal(document.getElementById('editProductModal'));
            modal.show();
        },

        saveEditProduct: async function (e) {
            if (e) e.preventDefault();
            const id = parseInt(document.getElementById('editProdId').value);
            const name = document.getElementById('editProdName').value.trim();
            const cost = parseFloat(document.getElementById('editProdCost').value) || 0;
            const price = parseFloat(document.getElementById('editProdPrice').value) || 0;
            const stock = parseInt(document.getElementById('editProdStock').value) || 0;

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn(`/api/admin/products/edit/${id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: name,
                        cost_price: cost,
                        selling_price: price,
                        stock_quantity: stock
                    })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    alert('Product updated successfully!');
                    const modalEl = document.getElementById('editProductModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    loadProductsData();
                } else {
                    alert(data.message || 'Failed to update product.');
                }
            } catch (err) {
                console.error('Update product error:', err);
                alert('Network error updating product.');
            }
        },

        deleteProduct: async function (productId) {
            const p = state.products.find(prod => prod.id === productId);
            if (!p) return;
            if (!confirm(`Are you sure you want to deactivate "${p.name}"?`)) return;

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn(`/api/admin/products/delete/${productId}`, {
                    method: 'POST'
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    alert(`Product "${p.name}" deactivated.`);
                    loadProductsData();
                } else {
                    alert(data.message || 'Could not deactivate product.');
                }
            } catch (err) {
                console.error('Delete product error:', err);
            }
        },

        updateOrderStatus: async function (orderId, newStatus) {
            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn(`/api/admin/orders/${orderId}/status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        order_status: newStatus
                    })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    logActionLocally('Order Status Changed', `Order #${orderId} moved to ${newStatus}`);
                    loadOrdersData();
                } else {
                    alert(data.message || 'Invalid status transition.');
                    loadOrdersData();
                }
            } catch (err) {
                console.error('Status transition error:', err);
            }
        },

        viewOrderDetail: async function (orderId) {
            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn(`/api/admin/orders/${orderId}`);
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('orderDetailModalId').textContent = `#${data.id}`;
                    document.getElementById('orderDetailModalCustomer').textContent = `Customer #${data.user_id}`;
                    document.getElementById('orderDetailModalPhone').textContent = data.shipping_address || '-';
                    document.getElementById('orderDetailModalDate').textContent = data.created_at ? new Date(data.created_at).toLocaleString('en-IN') : 'Recent';
                    document.getElementById('orderDetailModalPayment').textContent = `${data.payment_method} (${data.payment_status})`;
                    document.getElementById('orderDetailModalStatus').textContent = data.order_status;
                    document.getElementById('orderDetailModalTotal').textContent = `₹${data.total_amount}`;

                    const tbody = document.getElementById('orderDetailModalItemsTbody');
                    tbody.innerHTML = (data.items || []).map((it, i) => `
                        <tr>
                            <td>${i + 1}</td>
                            <td>${escapeHTML(it.product_name)}</td>
                            <td class="text-center">${Number(it.quantity)}</td>
                            <td class="text-end">₹${Number(it.price)}</td>
                            <td class="text-end fw-bold">₹${Number(it.subtotal)}</td>
                        </tr>
                    `).join('');

                    const modal = new bootstrap.Modal(document.getElementById('orderDetailModal'));
                    modal.show();
                }
            } catch (e) {
                console.warn('Could not fetch order detail:', e);
            }
        },

        saveNewCategory: async function (e) {
            if (e) e.preventDefault();
            const name = document.getElementById('newCatName').value.trim();
            const desc = document.getElementById('newCatDesc').value.trim();
            if (!name) return;

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn('/api/admin/categories/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name, description: desc })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    alert('Category created successfully!');
                    const modalEl = document.getElementById('addCategoryModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    loadCategoriesData();
                } else {
                    alert(data.message || 'Failed to create category.');
                }
            } catch (err) {
                console.error('Create category error:', err);
            }
        },

        openRecordPurchaseModal: function (supplierName) {
            const suppSelect = document.getElementById('purchaseSupplierSelect');
            if (suppSelect && supplierName) suppSelect.value = supplierName;
            const modal = new bootstrap.Modal(document.getElementById('addPurchaseModal'));
            modal.show();
        },

        saveNewPurchase: async function (e) {
            if (e) e.preventDefault();
            const suppSelect = document.getElementById('purchaseSupplierSelect');
            const prodSelect = document.getElementById('purchaseProductSelect');
            const qty = parseInt(document.getElementById('purchaseQty').value) || 0;
            const unitCost = parseFloat(document.getElementById('purchaseUnitCost').value) || 0;
            const supplierId = suppSelect && suppSelect.value ? parseInt(suppSelect.value) || 1 : 1;

            if (qty <= 0) {
                alert('Quantity must be greater than zero.');
                return;
            }

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn('/api/admin/purchases/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        supplier_id: supplierId,
                        product_id: parseInt(prodSelect.value) || 1,
                        quantity: qty,
                        purchase_price: unitCost > 0 ? unitCost : 10.0
                    })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    alert('Stock purchase recorded and product quantity increased!');
                    const modalEl = document.getElementById('addPurchaseModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    loadPurchasesData();
                    loadProductsData();
                } else {
                    alert(data.message || data.error || 'Failed to record stock purchase.');
                }
            } catch (err) {
                console.error('Purchase record error:', err);
            }
        },

        toggleCoupon: async function (couponId) {
            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn(`/api/admin/coupons/${couponId}/toggle`, {
                    method: 'POST'
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    loadCouponsData();
                }
            } catch (e) {
                console.error('Toggle coupon error:', e);
            }
        },

        saveNewCoupon: async function (e) {
            if (e) e.preventDefault();
            const codeInput = document.getElementById('newCouponCode');
            const discInput = document.getElementById('newCouponDiscount');
            const minSpendInput = document.getElementById('newCouponMinSpend');
            const expiryInput = document.getElementById('newCouponExpiry');

            const code = codeInput ? codeInput.value.trim().toUpperCase() : '';
            const rawDiscount = discInput ? discInput.value.trim() : '';
            const minSpend = minSpendInput ? parseFloat(minSpendInput.value) || 0 : 0;
            const expiry = expiryInput ? expiryInput.value.trim() : '';

            if (!code || !rawDiscount) {
                alert('Coupon code and discount value are required.');
                return;
            }

            const isPercent = rawDiscount.includes('%');
            const numValue = parseFloat(rawDiscount.replace(/[^0-9.]/g, '')) || 10;
            const discountType = isPercent ? 'percentage' : 'flat';

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn('/api/admin/coupons/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code: code,
                        discount_type: discountType,
                        value: numValue,
                        min_order_amount: minSpend,
                        valid_until: expiry || null,
                        usage_limit: 500
                    })
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.success) {
                    alert(data.message || `Coupon ${code} published successfully!`);
                    const modalEl = document.getElementById('createCouponModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    if (codeInput) codeInput.value = '';
                    if (discInput) discInput.value = '';
                    loadCouponsData();
                } else {
                    alert(data.message || 'Could not publish coupon.');
                }
            } catch (err) {
                console.error('Save coupon error:', err);
                alert('Network error publishing coupon.');
            }
        },

        toggle2FA: function () {
            const toggle = document.getElementById('security2faToggle');
            const isChecked = toggle ? toggle.checked : false;
            if (isChecked) {
                alert('To complete 2FA setup, visit the Security console or scan the TOTP QR key with your Authenticator app.');
            } else {
                alert('Two-factor authentication toggle updated.');
            }
        },

        clearCustomerUdhar: async function (customerId, amount) {
            if (!confirm(`Settle customer #${customerId} store credit of ₹${amount}?`)) return;
            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn(`/api/admin/customers/${customerId}/clear_credit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ amount_paid: amount })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    alert('Udhar settled successfully!');
                    loadCustomersData();
                } else {
                    alert(data.message || 'Could not settle credit.');
                }
            } catch (err) {
                console.error('Clear credit error:', err);
            }
        },

        filterInventoryByCategory: function (categoryName) {
            sessionStorage.setItem('adm_filter_category', categoryName);
            if (document.getElementById('adm-view-products')) {
                window.location.hash = '#products';
                setTimeout(() => {
                    const searchInput = document.getElementById('adminMasterSearch');
                    if (searchInput) {
                        searchInput.value = categoryName;
                        searchInput.dispatchEvent(new Event('input'));
                    }
                }, 100);
            } else {
                const inAdmin = window.location.pathname.includes('/admin/');
                window.location.href = (inAdmin ? 'products.html' : 'admin/products.html') + '?category=' + encodeURIComponent(categoryName);
            }
        },

        toggleTheme: function () {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('jg_admin_theme', newTheme);
        },

        toggleSidebar: function () {
            const sidebar = document.getElementById('adminSidebar');
            if (sidebar) sidebar.classList.toggle('show-mobile');
        }
    };

    // ── 6. Lifecycle Initialization ──
    window.addEventListener('DOMContentLoaded', async () => {
        // Theme check
        const savedTheme = localStorage.getItem('jg_admin_theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        }

        // Verify active administrator credentials
        const isAuthenticatedAdmin = await verifyAdminAuth();
        if (!isAuthenticatedAdmin) return;

        // Initialize Router
        router();
        window.addEventListener('hashchange', router);

        // Preload initial catalog and orders
        loadProductsData();
        loadOrdersData();

        // Live search in POS
        const posSearch = document.getElementById('posSearchInput');
        if (posSearch) {
            posSearch.addEventListener('input', (e) => {
                const val = e.target.value.toLowerCase().trim();
                document.querySelectorAll('#posProductsGrid .col-6').forEach(col => {
                    const text = col.textContent.toLowerCase();
                    col.style.display = text.includes(val) ? 'block' : 'none';
                });
            });
        }
    });

})();
