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

    // ── Modern Non-blocking Toast Notification Engine ──
    function showToast(message, type = 'success', duration = 3500) {
        let container = document.getElementById('admToastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'admToastContainer';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `adm-toast toast-${type}`;
        
        let iconClass = 'bi-check-circle-fill text-success';
        if (type === 'danger') iconClass = 'bi-x-circle-fill text-danger';
        else if (type === 'warning') iconClass = 'bi-exclamation-triangle-fill text-warning';
        else if (type === 'info') iconClass = 'bi-info-circle-fill text-primary';

        toast.innerHTML = `
            <i class="bi ${iconClass} fs-5 flex-shrink-0"></i>
            <div class="flex-grow-1">${escapeHTML(message)}</div>
            <button type="button" class="btn-close ms-2" style="font-size: 0.65rem;" aria-label="Close"></button>
        `;

        toast.querySelector('.btn-close').onclick = () => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-8px)';
            setTimeout(() => toast.remove(), 200);
        };

        container.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-8px)';
                setTimeout(() => toast.remove(), 200);
            }
        }, duration);
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
        expenses: [],
        intelligence: null,
        posCart: [],
        posDiscount: 0,
        twoFactorEnabled: false,
        user: null,
        lastDashboardData: null
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
            if (document.documentElement) document.documentElement.style.display = 'none';
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
                    if (document.documentElement) document.documentElement.style.display = '';
                    if (document.body) document.body.style.display = '';
                    updateAdminHeaderUI(data.user);
                    return true;
                } else if (data && data.authenticated === false) {
                    // Explicitly unauthenticated by server
                    localStorage.removeItem('jg_auth_user');
                }
            } else if (res.status === 401) {
                // Explicit 401 Unauthorized
                localStorage.removeItem('jg_auth_user');
            } else if (res.status === 429 || res.status >= 500) {
                // Rate limit or server error: retain verified local session if available
                console.warn(`[Admin ERP] Server returned status ${res.status} on /api/auth/me, keeping local session.`);
                if (localAuth && localAuth.role === 'admin') {
                    state.user = localAuth;
                    if (document.documentElement) document.documentElement.style.display = '';
                    if (document.body) document.body.style.display = '';
                    updateAdminHeaderUI(localAuth);
                    return true;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Auth verification error:', e);
            if (localAuth && localAuth.role === 'admin') {
                state.user = localAuth;
                if (document.documentElement) document.documentElement.style.display = '';
                if (document.body) document.body.style.display = '';
                updateAdminHeaderUI(localAuth);
                return true;
            }
        }

        // Unauthorized access: strictly purge stale client state and redirect to login
        localStorage.removeItem('jg_auth_user');
        console.warn('[Admin ERP] Unauthorized access detected. Redirecting to login.');
        const inAdmin = window.location.pathname.includes('/admin/');
        const targetPage = window.location.pathname.split('/').pop() || 'index.html';
        const redirectParam = encodeURIComponent(inAdmin ? `admin/${targetPage}` : targetPage);
        const loginUrl = inAdmin ? `../auth/login.html?redirect=${redirectParam}` : `auth/login.html?redirect=${redirectParam}`;

        if (document.documentElement) document.documentElement.style.display = 'none';
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
                        customer: o.customer_name || `Customer #${o.user_id}`,
                        customer_name: o.customer_name || `Customer #${o.user_id}`,
                        customer_phone: o.customer_phone || '',
                        customer_email: o.customer_email || '',
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
                        address: s.address || '',
                        gstin: s.gstin || '',
                        bank_details: s.bank_details || '',
                        outstanding_balance: parseFloat(s.outstanding_balance || 0)
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

    async function loadExpensesData() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/admin/expenses');
            if (res.ok) {
                const data = await res.json();
                if (data && data.expenses) {
                    state.expenses = data.expenses;
                    renderExpenses(data);
                    return;
                }
            }
        } catch (e) {
            console.warn('[Admin ERP] Expenses load error:', e);
        }
        renderExpenses();
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
            const knownAdminPages = ['dashboard', 'expenses', 'pos', 'products', 'categories', 'orders', 'customers', 'sales', 'purchases', 'suppliers', 'coupons', 'activity', 'security'];
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
        else if (route === 'expenses') loadExpensesData();
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

    // Dynamic Vertical Linear Gradient Builder for Chart.js
    function createVerticalLinearGradient(ctx, colorRgb, startAlpha, endAlpha, height = 280) {
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, `rgba(${colorRgb}, ${startAlpha})`);
        gradient.addColorStop(1, `rgba(${colorRgb}, ${endAlpha})`);
        return gradient;
    }

    function renderModernSalesChart(chartData) {
        if (typeof Chart === 'undefined' || !chartData) return;
        const ctxSales = document.getElementById('dashSalesChart');
        if (!ctxSales) return;

        const isDark = (document.documentElement.getAttribute('data-theme') === 'dark');
        const ctx = ctxSales.getContext('2d');
        const emeraldGradient = createVerticalLinearGradient(ctx, '5, 150, 105', 0.28, 0.0);
        const skyGradient = createVerticalLinearGradient(ctx, '2, 132, 199', 0.20, 0.0);

        const rawLabels = chartData.labels || ['1', '2', '3', '4', '5', '6', '7'];
        const formattedLabels = rawLabels.map(lbl => {
            try {
                const parts = String(lbl).split('-');
                if (parts.length === 3) {
                    const d = new Date(lbl);
                    if (!isNaN(d.getTime())) {
                        return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
                    }
                }
            } catch (e) {}
            return lbl;
        });

        if (salesChartInstance) salesChartInstance.destroy();
        salesChartInstance = new Chart(ctxSales, {
            type: 'line',
            data: {
                labels: formattedLabels,
                datasets: [
                    {
                        label: 'Revenue (₹)',
                        data: chartData.revenue || [],
                        borderColor: '#059669',
                        backgroundColor: emeraldGradient,
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2.5,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#059669',
                        pointBorderWidth: 2,
                        pointRadius: 3.5,
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: '#059669',
                        pointHoverBorderColor: '#ffffff',
                        pointHoverBorderWidth: 2
                    },
                    {
                        label: 'Profit (₹)',
                        data: chartData.profit || [],
                        borderColor: '#0284c7',
                        backgroundColor: skyGradient,
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#0284c7',
                        pointBorderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        pointHoverBackgroundColor: '#0284c7',
                        pointHoverBorderColor: '#ffffff',
                        pointHoverBorderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 8,
                            boxHeight: 8,
                            padding: 14,
                            font: { family: "'Inter', sans-serif", size: 11, weight: '600' },
                            color: isDark ? '#94a3b8' : '#64748b'
                        }
                    },
                    tooltip: {
                        backgroundColor: isDark ? 'rgba(17, 24, 39, 0.96)' : 'rgba(255, 255, 255, 0.98)',
                        titleColor: isDark ? '#f8fafc' : '#0f172a',
                        bodyColor: isDark ? '#cbd5e1' : '#334155',
                        borderColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 8,
                        boxPadding: 4,
                        usePointStyle: true,
                        titleFont: { family: "'Outfit', sans-serif", size: 12, weight: '700' },
                        bodyFont: { family: "'Inter', sans-serif", size: 11, weight: '500' },
                        callbacks: {
                            label: function (context) {
                                const val = context.parsed.y !== null ? context.parsed.y : context.raw;
                                return ` ${context.dataset.label}: ₹${Number(val).toLocaleString('en-IN')}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            font: { family: "'Inter', sans-serif", size: 11 },
                            color: isDark ? '#64748b' : '#94a3b8',
                            maxTicksLimit: 7,
                            maxRotation: 0,
                            autoSkip: true
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.04)'
                        },
                        ticks: {
                            font: { family: "'Inter', sans-serif", size: 11 },
                            color: isDark ? '#64748b' : '#94a3b8',
                            callback: (v) => '₹' + Number(v).toLocaleString('en-IN')
                        }
                    }
                }
            }
        });
    }

    function renderModernOrderStatusChart() {
        if (typeof Chart === 'undefined') return;
        const ctxOrder = document.getElementById('dashOrderStatusChart');
        if (!ctxOrder) return;

        const statusCounts = {
            'Delivered': 0,
            'Shipped': 0,
            'Out for Delivery': 0,
            'Processing': 0,
            'Pending': 0,
            'Cancelled': 0
        };

        if (state.orders && state.orders.length > 0) {
            state.orders.forEach(o => {
                const st = o.status || 'Pending';
                if (statusCounts[st] !== undefined) {
                    statusCounts[st]++;
                } else if (st.toLowerCase().includes('deliv')) {
                    statusCounts['Delivered']++;
                } else {
                    statusCounts['Processing']++;
                }
            });
        } else {
            statusCounts['Delivered'] = 14;
            statusCounts['Shipped'] = 6;
            statusCounts['Processing'] = 5;
            statusCounts['Pending'] = 3;
            statusCounts['Cancelled'] = 1;
        }

        const labels = Object.keys(statusCounts).filter(k => statusCounts[k] > 0);
        const dataVals = labels.map(k => statusCounts[k]);
        const colorMap = {
            'Delivered': '#059669',
            'Shipped': '#0284c7',
            'Out for Delivery': '#06b6d4',
            'Processing': '#f59e0b',
            'Pending': '#8b5cf6',
            'Cancelled': '#ef4444'
        };
        const bgColors = labels.map(l => colorMap[l] || '#64748b');
        const isDark = (document.documentElement.getAttribute('data-theme') === 'dark');

        if (orderStatusChartInstance) orderStatusChartInstance.destroy();
        orderStatusChartInstance = new Chart(ctxOrder, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: dataVals,
                    backgroundColor: bgColors,
                    borderColor: isDark ? '#111827' : '#ffffff',
                    borderWidth: 2,
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 8,
                            boxHeight: 8,
                            padding: 12,
                            font: { family: "'Inter', sans-serif", size: 11, weight: '500' },
                            color: isDark ? '#94a3b8' : '#64748b'
                        }
                    },
                    tooltip: {
                        backgroundColor: isDark ? 'rgba(17, 24, 39, 0.94)' : 'rgba(255, 255, 255, 0.96)',
                        titleColor: isDark ? '#f8fafc' : '#0f172a',
                        bodyColor: isDark ? '#cbd5e1' : '#334155',
                        borderColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 10,
                        usePointStyle: true,
                        titleFont: { family: "'Outfit', sans-serif", size: 12, weight: '700' },
                        bodyFont: { family: "'Inter', sans-serif", size: 11, weight: '500' },
                        callbacks: {
                            label: function (ctx) {
                                return ` ${ctx.label}: ${ctx.raw} orders`;
                            }
                        }
                    }
                }
            }
        });
    }

    function renderDashboardWithData(data) {
        const fin = data.financials || {};
        const stats30 = data.stats_30_days || {};

        // 1. Total Revenue
        const totalRev = Number(fin.total_revenue ?? data.total_revenue ?? data.total_order_revenue ?? stats30.revenue ?? 0);
        const onlineRev = Number(fin.online_revenue ?? data.total_order_revenue ?? 0);
        const posRev = Number(fin.pos_revenue ?? 0);
        const revEl = document.getElementById('dashKpiRevenue');
        if (revEl) revEl.textContent = `₹${totalRev.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;

        const revSplitEl = document.getElementById('dashKpiRevSplit');
        if (revSplitEl) {
            if (onlineRev > 0 || posRev > 0) {
                revSplitEl.innerHTML = `<i class="bi bi-arrow-up-right"></i> Online ₹${onlineRev.toLocaleString('en-IN')} &bull; POS ₹${posRev.toLocaleString('en-IN')}`;
            } else {
                revSplitEl.innerHTML = `<i class="bi bi-arrow-up-right"></i> Online &bull; POS Live Feed`;
            }
        }

        // 2. Total Sales & Volume
        const salesCount = Number(fin.total_sales_count ?? data.total_sales ?? data.total_orders ?? stats30.count ?? 0);
        const unitsSold = Number(fin.total_units_sold ?? data.total_units_sold ?? 0);
        const salesEl = document.getElementById('dashKpiSalesCount');
        if (salesEl) salesEl.textContent = salesCount.toLocaleString('en-IN');
        const unitsEl = document.getElementById('dashKpiUnitsSold');
        if (unitsEl) unitsEl.innerHTML = `<i class="bi bi-cart-check"></i> ${unitsSold.toLocaleString('en-IN')} units sold`;

        // 3. Net Profit & Margin
        const netProfit = Number(fin.net_profit ?? data.net_profit ?? data.total_order_profit ?? 0);
        const marginPct = Number(fin.profit_margin_pct ?? data.profit_margin_pct ?? 0);
        const profitEl = document.getElementById('dashKpiProfit');
        if (profitEl) {
            const isNeg = netProfit < 0;
            profitEl.textContent = `${isNeg ? '-' : ''}₹${Math.abs(netProfit).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
            profitEl.className = `fw-bold mt-1 mb-0 ${isNeg ? 'text-danger' : 'text-dark'}`;
        }
        const marginEl = document.getElementById('dashKpiMargin');
        if (marginEl) {
            marginEl.className = `smallest fw-semibold ${marginPct >= 0 ? 'text-success' : 'text-danger'}`;
            marginEl.innerHTML = `<i class="bi ${marginPct >= 0 ? 'bi-graph-up-arrow' : 'bi-graph-down-arrow'}"></i> ${marginPct.toFixed(1)}% Margin`;
        }

        // 4. Total Expenses
        const totalExpenses = Number(fin.total_expenses ?? data.total_expenses ?? 0);
        const monthlyExpenses = Number(fin.monthly_expenses ?? data.monthly_expenses ?? 0);
        const expensesEl = document.getElementById('dashKpiExpenses');
        if (expensesEl) expensesEl.textContent = `₹${totalExpenses.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
        const expMonthEl = document.getElementById('dashKpiExpenseMonth');
        if (expMonthEl) {
            expMonthEl.innerHTML = monthlyExpenses > 0 
                ? `<i class="bi bi-receipt"></i> Month: ₹${monthlyExpenses.toLocaleString('en-IN')}`
                : `<i class="bi bi-receipt"></i> Store Overhead`;
        }

        // 5. Total Orders & Pending Queue
        const totalOrders = Number(data.total_orders || fin.total_sales_count || 0);
        const pendingOrders = Number(fin.pending_orders ?? data.pending_orders ?? 0);
        const ordersEl = document.getElementById('dashKpiOrders');
        if (ordersEl) ordersEl.textContent = totalOrders.toLocaleString('en-IN');
        const pendingEl = document.getElementById('dashKpiPendingOrders');
        if (pendingEl) pendingEl.textContent = pendingOrders;

        // 6. Inventory Valuation & Active Catalog
        const invVal = Number(fin.inventory_valuation ?? data.inventory_valuation ?? 0);
        const totalProducts = Number(fin.active_catalog_count ?? data.stock_stats?.total_products ?? state.products.length);
        const invValEl = document.getElementById('dashKpiInvVal');
        if (invValEl) invValEl.textContent = `₹${invVal.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
        const productsEl = document.getElementById('dashKpiProducts');
        if (productsEl) productsEl.textContent = totalProducts;

        // 7. Critical Low Stock
        const lowStockCount = Number(fin.critical_low_stock ?? data.stock_stats?.low_stock_count ?? 0);
        const lowStockEl = document.getElementById('dashKpiLowStock');
        if (lowStockEl) lowStockEl.textContent = lowStockCount;

        // 8. Customer Udhar
        const totalUdhar = Number(fin.total_udhar ?? data.total_udhar ?? 0);
        const udharEl = document.getElementById('dashKpiUdhar');
        if (udharEl) udharEl.textContent = `₹${totalUdhar.toLocaleString('en-IN')}`;

        const lowStockBanner = document.getElementById('dashLowStockBanner');
        if (lowStockBanner) {
            lowStockBanner.style.display = lowStockCount > 0 ? 'flex' : 'none';
            const bannerCount = document.getElementById('dashLowStockCount');
            if (bannerCount) bannerCount.textContent = lowStockCount;
        }

        // Save dashboard state for theme re-renders
        state.lastDashboardData = data;

        // Recent Orders
        loadOrdersData();

        // Modern Chart.js Sales Graph with Dynamic Vertical Linear Gradients
        if (typeof Chart !== 'undefined' && data.chart_data) {
            renderModernSalesChart(data.chart_data);
            renderModernOrderStatusChart();
        }

        // Render Decision Intelligence Layer
        const intel = data.intelligence || {};
        if (intel.health_score) renderHealthScore(intel.health_score);
        if (intel.cash_flow || intel.forecast) renderTodayCashFlow(intel.cash_flow, intel.forecast);
        if (intel.action_center) renderActionCenter(intel.action_center);
        if (intel.ai_insights) renderAIInsights(intel.ai_insights);
        if (intel.inventory_intelligence) renderLockedCapital(intel.inventory_intelligence);
        if (intel.profitability_matrix) renderProfitabilityMatrix(intel.profitability_matrix);
    }

    function renderHealthScore(hs) {
        if (!hs) return;
        const numEl = document.getElementById('healthScoreNum');
        const badgeEl = document.getElementById('healthStatusBadge');
        const sumEl = document.getElementById('healthSummaryText');

        if (numEl) numEl.textContent = hs.overall_score;
        if (badgeEl) {
            badgeEl.className = `badge bg-${hs.badge_class}-subtle text-${hs.badge_class} fs-6 fw-bold px-3 py-2 rounded-pill`;
            badgeEl.textContent = `${hs.overall_score}/100 • ${hs.status}`;
        }
        if (sumEl) sumEl.textContent = hs.summary || '';

        const comps = hs.components || {};
        const setComp = (key, barId, valId) => {
            const bar = document.getElementById(barId);
            const val = document.getElementById(valId);
            const score = comps[key]?.score ?? 0;
            if (bar) bar.style.width = `${Math.min(100, Math.max(0, score))}%`;
            if (val) val.textContent = `${score}%`;
        };

        setComp('sales', 'healthBarSales', 'healthValSales');
        setComp('inventory', 'healthBarInventory', 'healthValInventory');
        setComp('profit', 'healthBarProfit', 'healthValProfit');
        setComp('customers', 'healthBarCustomers', 'healthValCustomers');
        setComp('credit', 'healthBarCredit', 'healthValCredit');
    }

    function renderTodayCashFlow(cf, fc) {
        if (cf && cf.today) {
            const inEl = document.getElementById('cfTodayIn');
            const outEl = document.getElementById('cfTodayOut');
            const netEl = document.getElementById('cfTodayNet');
            const statusEl = document.getElementById('cfTodayStatusBadge');

            if (inEl) inEl.textContent = `₹${Number(cf.today.money_in || 0).toLocaleString('en-IN')}`;
            if (outEl) outEl.textContent = `₹${Number(cf.today.money_out || 0).toLocaleString('en-IN')}`;
            if (netEl) {
                const netVal = Number(cf.today.net_cash_flow || 0);
                netEl.textContent = `₹${netVal.toLocaleString('en-IN')}`;
                netEl.className = netVal >= 0 ? 'text-success fw-bold' : 'text-danger fw-bold';
            }
            if (statusEl) {
                const isPos = cf.today.net_cash_flow >= 0;
                statusEl.className = `badge ${isPos ? 'bg-success-subtle text-success' : 'bg-danger-subtle text-danger'} border px-2 py-1 smallest`;
                statusEl.textContent = isPos ? 'Positive Cash Flow' : 'Deficit Outflow';
            }
        }

        if (cf && cf.expected_receivables) {
            const udharEl = document.getElementById('cfUdharVal');
            if (udharEl) udharEl.textContent = `₹${Number(cf.expected_receivables.customer_udhar || 0).toLocaleString('en-IN')}`;
        }

        if (fc) {
            const confEl = document.getElementById('forecastConfidenceBadge');
            const tomEl = document.getElementById('forecastTomorrowVal');
            const monEl = document.getElementById('forecastMonthlyVal');

            if (confEl) confEl.textContent = fc.confidence_label || `${fc.confidence_score}% Confidence`;
            if (tomEl) tomEl.textContent = `₹${Number(fc.tomorrow_sales_forecast || 0).toLocaleString('en-IN')}`;
            if (monEl) monEl.textContent = `₹${Number(fc.expected_monthly_revenue || 0).toLocaleString('en-IN')}`;
        }
    }

    function renderActionCenter(ac) {
        if (!ac) return;
        const cCount = document.getElementById('actCountCrit');
        const wCount = document.getElementById('actCountWarn');
        const oCount = document.getElementById('actCountOpp');

        if (cCount) cCount.textContent = ac.critical?.length || 0;
        if (wCount) wCount.textContent = ac.warnings?.length || 0;
        if (oCount) oCount.textContent = ac.opportunities?.length || 0;

        const colCrit = document.getElementById('actionColCritical');
        if (colCrit) {
            if (!ac.critical || ac.critical.length === 0) {
                colCrit.innerHTML = `<div class="smallest text-muted py-2">No urgent critical items today.</div>`;
            } else {
                colCrit.innerHTML = ac.critical.map(item => `
                    <div class="p-2 bg-white rounded border shadow-sm">
                        <div class="fw-bold text-danger smallest">${escapeHTML(item.title)}</div>
                        <div class="smallest text-muted mb-2">${escapeHTML(item.subtitle)}</div>
                        <a href="${escapeHTML(item.action_url)}" class="btn btn-sm btn-danger rounded-pill px-3 py-0 smallest fw-semibold">${escapeHTML(item.action_label)} &rarr;</a>
                    </div>
                `).join('');
            }
        }

        const colWarn = document.getElementById('actionColWarnings');
        if (colWarn) {
            if (!ac.warnings || ac.warnings.length === 0) {
                colWarn.innerHTML = `<div class="smallest text-muted py-2">Stock levels are currently balanced.</div>`;
            } else {
                colWarn.innerHTML = ac.warnings.map(item => `
                    <div class="p-2 bg-white rounded border shadow-sm">
                        <div class="fw-bold text-dark smallest">${escapeHTML(item.title)}</div>
                        <div class="smallest text-muted mb-2">${escapeHTML(item.subtitle)}</div>
                        <a href="${escapeHTML(item.action_url)}" class="btn btn-sm btn-outline-dark rounded-pill px-3 py-0 smallest fw-semibold">${escapeHTML(item.action_label)} &rarr;</a>
                    </div>
                `).join('');
            }
        }

        const colOpp = document.getElementById('actionColOpportunities');
        if (colOpp) {
            if (!ac.opportunities || ac.opportunities.length === 0) {
                colOpp.innerHTML = `<div class="smallest text-muted py-2">No active growth prompts today.</div>`;
            } else {
                colOpp.innerHTML = ac.opportunities.map(item => `
                    <div class="p-2 bg-white rounded border shadow-sm">
                        <div class="fw-bold text-success smallest">${escapeHTML(item.title)}</div>
                        <div class="smallest text-muted mb-2">${escapeHTML(item.subtitle)}</div>
                        <a href="${escapeHTML(item.action_url)}" class="btn btn-sm btn-success rounded-pill px-3 py-0 smallest fw-semibold">${escapeHTML(item.action_label)} &rarr;</a>
                    </div>
                `).join('');
            }
        }
    }

    function renderAIInsights(insights) {
        const grid = document.getElementById('aiInsightsGrid');
        if (!grid) return;

        if (!insights || insights.length === 0) {
            grid.innerHTML = `<div class="col-12 text-center text-muted small py-3">Store metrics are operating within baseline parameters.</div>`;
            return;
        }

        grid.innerHTML = insights.map(ins => {
            const borderCol = ins.severity === 'danger' ? 'border-danger' : ins.severity === 'warning' ? 'border-warning' : ins.severity === 'success' ? 'border-success' : 'border-info';
            const bgBadge = ins.severity === 'danger' ? 'bg-danger' : ins.severity === 'warning' ? 'bg-warning text-dark' : ins.severity === 'success' ? 'bg-success' : 'bg-info text-dark';
            return `
                <div class="col-md-6 col-xl-4">
                    <div class="p-3 bg-light rounded-3 border ${borderCol} h-100 d-flex flex-column justify-content-between">
                        <div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="badge ${bgBadge} smallest">${escapeHTML(ins.type.toUpperCase())}</span>
                                <i class="bi ${escapeHTML(ins.icon || 'bi-lightbulb')} fs-5 text-${ins.severity}"></i>
                            </div>
                            <h6 class="fw-bold text-dark mb-1 small">${escapeHTML(ins.headline)}</h6>
                            <p class="smallest text-muted mb-3">${escapeHTML(ins.explanation)}</p>
                        </div>
                        <div class="p-2 bg-white rounded border">
                            <div class="smallest fw-bold text-dark mb-2">${escapeHTML(ins.action_title)}</div>
                            <a href="${escapeHTML(ins.action_url)}" class="btn btn-sm btn-outline-success rounded-pill px-3 py-0 smallest fw-bold">
                                ${escapeHTML(ins.btn_label)} &rarr;
                            </a>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderLockedCapital(invIntel) {
        if (!invIntel) return;
        const lockedEl = document.getElementById('lockedCapitalVal');
        const totEl = document.getElementById('invTotalVal');
        const toEl = document.getElementById('invTurnoverVal');

        if (lockedEl) lockedEl.textContent = `₹${Number(invIntel.slow_moving_locked_capital || invIntel.dead_stock_value || 0).toLocaleString('en-IN')}`;
        if (totEl) totEl.textContent = `₹${Number(invIntel.total_inventory_value || 0).toLocaleString('en-IN')}`;
        if (toEl) toEl.textContent = `${Number(invIntel.stock_turnover_ratio || 0).toFixed(1)}x`;
    }

    function renderProfitabilityMatrix(mat) {
        if (!mat) return;
        const cStars = document.getElementById('countStars');
        const cRev = document.getElementById('countReview');
        const cProm = document.getElementById('countPromote');
        const cDead = document.getElementById('countDeadStock');

        if (cStars) cStars.textContent = mat.counts?.stars || 0;
        if (cRev) cRev.textContent = mat.counts?.review_price || 0;
        if (cProm) cProm.textContent = mat.counts?.promote || 0;
        if (cDead) cDead.textContent = mat.counts?.dead_stock || 0;

        const renderRows = (items, tbodyId, actionLabel, actionUrl) => {
            const tbody = document.getElementById(tbodyId);
            if (!tbody) return;
            if (!items || items.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted small py-3">No products in this quadrant.</td></tr>`;
                return;
            }
            tbody.innerHTML = items.map(p => `
                <tr>
                    <td class="fw-bold text-dark">${escapeHTML(p.name)}</td>
                    <td><span class="badge bg-light text-dark border">${escapeHTML(p.category)}</span></td>
                    <td>${Number(p.units_sold)} units</td>
                    <td class="fw-bold text-success">${Number(p.margin_pct)}%</td>
                    <td>${Number(p.stock)}</td>
                    <td>
                        <a href="${actionUrl}?product_id=${p.id}" class="btn btn-sm btn-outline-secondary rounded-pill px-2 py-0 smallest">${actionLabel}</a>
                    </td>
                </tr>
            `).join('');
        };

        renderRows(mat.stars, 'matrixStarsTbody', 'Restock', 'purchases.html');
        renderRows(mat.review_price, 'matrixReviewTbody', 'Edit Price', 'products.html');
        renderRows(mat.promote, 'matrixPromoteTbody', 'Create Promo', 'coupons.html');
        renderRows(mat.dead_stock, 'matrixDeadStockTbody', 'Clearance', 'coupons.html');
    }

    function renderExpenses(data) {
        const tbody = document.getElementById('expensesTableTbody');
        if (tbody) {
            if (!state.expenses || state.expenses.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4 small">No operating expenses recorded this period.</td></tr>`;
            } else {
                tbody.innerHTML = state.expenses.map(e => {
                    const isRecovery = (e.expense_type === 'Debt Recovery' || (e.category && e.category.includes('Debt Recovery')));
                    const isApPayout = (e.expense_type === 'Supplier Payment' || (e.category && e.category.includes('Supplier Payment')));
                    const isCapEx = (e.expense_type === 'CapEx');
                    
                    let typeBadge = '<span class="badge bg-secondary-subtle text-secondary border">OpEx</span>';
                    if (isRecovery) typeBadge = '<span class="badge bg-success-subtle text-success border border-success">Debt Recovery (Inflow)</span>';
                    else if (isApPayout) typeBadge = '<span class="badge bg-primary-subtle text-primary border">AP Payout</span>';
                    else if (isCapEx) typeBadge = '<span class="badge bg-warning-subtle text-warning-emphasis border">CapEx</span>';

                    const amountColor = isRecovery ? 'text-success' : 'text-danger';
                    const amountPrefix = isRecovery ? '+₹' : '₹';

                    return `
                    <tr>
                        <td class="text-muted small tabular-nums">#${Number(e.id)}</td>
                        <td class="tabular-nums">${escapeHTML(e.expense_date || '-')}</td>
                        <td>
                            <span class="badge bg-light text-dark border">${escapeHTML(e.category)}</span>
                            <div class="mt-1">${typeBadge}</div>
                        </td>
                        <td>${escapeHTML(e.description || '-')}</td>
                        <td><span class="badge bg-secondary-subtle text-secondary">${escapeHTML(e.payment_mode || 'Cash')}</span></td>
                        <td class="fw-bold ${amountColor} tabular-nums">${amountPrefix}${Number(e.amount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                        <td>${e.is_recurring ? '<span class="badge bg-primary">Recurring</span>' : '<span class="badge bg-light text-dark border">One-off</span>'}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-danger rounded-pill px-2 py-0 smallest" title="Archive / Soft Delete" onclick="window.Adm.deleteExpense(${Number(e.id)})">
                                <i class="bi bi-archive me-1"></i>Archive
                            </button>
                        </td>
                    </tr>
                    `;
                }).join('');
            }
        }

        // Summary KPI cards in expenses.html
        if (data && data.summary) {
            const monthlyEl = document.getElementById('expKpiMonthly');
            if (monthlyEl) monthlyEl.textContent = `₹${Number(data.summary.monthly_total || 0).toLocaleString('en-IN')}`;

            // Category bars in expenses.html
            const catContainer = document.getElementById('expenseCategoryBars');
            if (catContainer && data.summary.categories) {
                const total = Number(data.summary.monthly_total || 1);
                catContainer.innerHTML = data.summary.categories.map(c => {
                    const pct = Math.round((c.total / total) * 100);
                    return `
                        <div>
                            <div class="d-flex justify-content-between small fw-bold mb-1">
                                <span>${escapeHTML(c.category)}</span>
                                <span>₹${Number(c.total).toLocaleString('en-IN')} (${pct}%)</span>
                            </div>
                            <div class="progress" style="height: 8px;">
                                <div class="progress-bar bg-danger" role="progressbar" style="width: ${pct}%"></div>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }
    }

    function renderDashboardFallback() {
        const todayRevenue = state.orders.reduce((sum, o) => sum + (o.status !== 'Cancelled' ? o.total : 0), 0);
        const lowStockItems = state.products.filter(p => p.stock <= 5);
        const totalSales = state.orders.length;
        const totalProfit = todayRevenue * 0.25; // Estimated 25% fallback margin
        const totalExpenses = 0;
        const totalInvVal = state.products.reduce((sum, p) => sum + ((p.stock || 0) * (p.price || 0)), 0);

        const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        setVal('dashKpiRevenue', `₹${todayRevenue.toLocaleString('en-IN')}`);
        setVal('dashKpiSalesCount', totalSales);
        setVal('dashKpiProfit', `₹${totalProfit.toLocaleString('en-IN')}`);
        setVal('dashKpiExpenses', `₹${totalExpenses.toLocaleString('en-IN')}`);
        setVal('dashKpiOrders', state.orders.length);
        setVal('dashKpiProducts', state.products.length);
        setVal('dashKpiLowStock', lowStockItems.length);
        setVal('dashKpiInvVal', `₹${totalInvVal.toLocaleString('en-IN')}`);
        setVal('dashKpiPendingOrders', state.orders.filter(o => o.status === 'Pending').length);
        setVal('dashKpiUdhar', '₹0');
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
                    <div class="fw-bold text-dark">${escapeHTML(o.customer || 'Customer')}</div>
                    ${o.customer_phone ? `<div class="smallest text-success fw-semibold"><i class="bi bi-telephone me-1"></i>${escapeHTML(o.customer_phone)}</div>` : ''}
                    <div class="smallest text-muted">${escapeHTML(o.shipping_address ? o.shipping_address.substring(0, 30) + '...' : '')}</div>
                </td>
                <td class="small">${escapeHTML(o.date)}</td>
                <td class="text-center">${o.items ? o.items.length : 1} items</td>
                <td class="fw-bold text-dark">₹${escapeHTML(o.total)}</td>
                <td><span class="badge bg-light text-dark border small">${escapeHTML(o.payment || 'COD')}</span></td>
                <td>
                    <select class="form-select form-select-sm rounded-pill" style="width: 155px;" onchange="window.Adm.updateOrderStatus('${escapeHTML(o.id)}', this.value)">
                        <option value="Pending" ${o.status === 'Pending' ? 'selected' : ''}>Pending</option>
                        <option value="Processing" ${o.status === 'Processing' ? 'selected' : ''}>Processing</option>
                        <option value="Packed" ${o.status === 'Packed' ? 'selected' : ''}>Packed</option>
                        <option value="Out for Delivery" ${o.status === 'Out for Delivery' ? 'selected' : ''}>Out for Delivery</option>
                        <option value="Delivered" ${o.status === 'Delivered' ? 'selected' : ''}>Delivered</option>
                        <option value="Cancelled" ${o.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                        <option value="Returned" ${o.status === 'Returned' ? 'selected' : ''}>Returned</option>
                    </select>
                </td>
                <td>
                    <div class="d-flex gap-1">
                        <button class="btn btn-sm btn-outline-success rounded-pill px-2" onclick="window.Adm.viewOrderDetail('${escapeHTML(o.id)}')">
                            <i class="bi bi-file-text me-1"></i>Detail
                        </button>
                        <button class="btn btn-sm btn-outline-dark rounded-pill px-2" title="Thermal Receipt Slip" onclick="window.Adm.viewOrderReceipt('${escapeHTML(o.id)}')">
                            <i class="bi bi-receipt"></i> Slip
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
                <td>
                    <span class="fw-bold font-monospace text-dark">${escapeHTML(s.bill_number || ('#SAL-' + s.id))}</span>
                    <div class="smallest text-muted">${escapeHTML(s.product_name || 'Item')} &times; ${Number(s.quantity)}</div>
                </td>
                <td><span class="small text-muted tabular-nums">${s.sale_date ? new Date(s.sale_date).toLocaleString('en-IN') : 'Recent'}</span></td>
                <td>
                    <div class="fw-semibold text-dark">${escapeHTML(s.customer_name || 'Walk-in Counter')}</div>
                    ${s.customer_phone ? `<div class="smallest text-muted font-monospace">${escapeHTML(s.customer_phone)}</div>` : ''}
                </td>
                <td>
                    <span class="badge ${s.payment_method === 'Cash' ? 'bg-success-subtle text-success border border-success' : (s.payment_method && s.payment_method.includes('UPI')) ? 'bg-primary-subtle text-primary border border-primary' : 'bg-secondary-subtle text-secondary border'}">
                        ${escapeHTML(s.payment_method || 'Cash')}
                    </span>
                </td>
                <td class="num-cell fw-bold text-dark tabular-nums">₹${Number(s.total_price).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                <td class="num-cell fw-bold tabular-nums ${Number(s.profit) >= 0 ? 'text-success' : 'text-danger'}">₹${Number(s.profit).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                <td>
                    <button class="btn btn-sm btn-outline-secondary rounded-pill px-2 py-0 smallest d-inline-flex align-items-center gap-1" onclick="window.Adm.viewReceipt(${Number(s.id)})">
                        <i class="bi bi-receipt"></i>
                        <span>Slip</span>
                    </button>
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

        const totalAP = state.suppliers.reduce((sum, s) => sum + (s.outstanding_balance || 0), 0);
        const apBadge = document.getElementById('totalSupplierApBadge');
        if (apBadge) {
            apBadge.innerHTML = `<i class="bi bi-wallet2 me-1"></i> Total AP Payable: ₹${totalAP.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        }

        grid.innerHTML = state.suppliers.map(s => {
            const hasDue = (s.outstanding_balance || 0) > 0;
            return `
            <div class="col-md-6 col-xl-4">
                <div class="kpi-card p-4 h-100 d-flex flex-column justify-content-between">
                    <div>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="badge bg-light text-dark border">${escapeHTML(s.category)}</span>
                            <i class="bi bi-building text-success fs-4"></i>
                        </div>
                        <h5 class="fw-bold brand-font text-dark mb-1">${escapeHTML(s.name)}</h5>
                        ${s.gstin ? `<div class="smallest text-muted mb-2 font-monospace"><i class="bi bi-card-text me-1"></i>GSTIN: <strong>${escapeHTML(s.gstin)}</strong></div>` : ''}
                        <div class="small text-muted mb-1"><i class="bi bi-person me-1"></i>Contact: <strong>${escapeHTML(s.contact || 'Direct')}</strong></div>
                        <div class="small text-muted mb-1"><i class="bi bi-telephone me-1"></i>${escapeHTML(s.phone || '-')}</div>
                        <div class="small text-muted mb-2"><i class="bi bi-envelope me-1"></i>${escapeHTML(s.email || '-')}</div>
                        
                        <!-- Accounts Payable Balance Card -->
                        <div class="p-2 rounded-2 ${hasDue ? 'bg-danger-subtle text-danger border border-danger-subtle' : 'bg-success-subtle text-success border border-success-subtle'} mb-3">
                            <div class="d-flex justify-content-between align-items-center small">
                                <span class="fw-semibold">Accounts Payable (Due):</span>
                                <span class="fw-bold fs-6 tabular-nums">₹${Number(s.outstanding_balance || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
                            </div>
                        </div>
                    </div>

                    <div class="d-flex gap-2 pt-2 border-top align-items-center">
                        <button class="btn btn-sm btn-outline-success rounded-2 px-2 flex-grow-1 d-inline-flex align-items-center justify-content-center gap-1" onclick="window.Adm.openRecordPurchaseModal(${Number(s.id)})" title="Record Inward Delivery">
                            <i class="bi bi-box-arrow-in-down"></i>
                            <span>Stock In</span>
                        </button>
                        ${hasDue ? `
                        <button class="btn btn-sm btn-danger rounded-2 px-2 d-inline-flex align-items-center gap-1" onclick="window.Adm.paySupplier(${Number(s.id)}, '${escapeHTML(s.name).replace(/'/g, "\\'")}', ${Number(s.outstanding_balance)})" title="Pay AP Due">
                            <i class="bi bi-cash"></i>Pay AP
                        </button>
                        ` : ''}
                        <button class="btn btn-sm btn-outline-primary rounded-2 px-2" onclick="window.Adm.openEditSupplierModal(${Number(s.id)})" title="Edit Supplier Details">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger rounded-2 px-2" onclick="window.Adm.deleteSupplier(${Number(s.id)}, '${escapeHTML(s.name).replace(/'/g, "\\'")}')" title="Delete Supplier">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
            `;
        }).join('');
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
                <td class="tabular-nums">₹${Number(c.minSpend)}</td>
                <td class="tabular-nums">${escapeHTML(c.expiry)}</td>
                <td class="text-center tabular-nums">${Number(c.used)} times</td>
                <td>
                    <span class="badge ${c.active ? 'bg-success' : 'bg-secondary'}">
                        ${c.active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-danger rounded-2 px-2" onclick="window.Adm.toggleCoupon(${Number(c.id)})">
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
                        <span class="smallest text-muted tabular-nums">${a.created_at ? new Date(a.created_at).toLocaleString('en-IN') : 'Recent'}</span>
                    </div>
                    <div class="small text-dark mb-1">${escapeHTML(a.details || '')}</div>
                    <div class="smallest text-muted">Entity: <strong>${escapeHTML(a.entity_type || 'System')} <span class="tabular-nums">#${escapeHTML(a.entity_id || '')}</span></strong></div>
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
        showToast: showToast,

        posAddToCart: function (productId) {
            const p = state.products.find(prod => prod.id === productId);
            if (!p || p.stock <= 0) {
                showToast('Item is currently out of stock in warehouse!', 'danger');
                return;
            }

            const existing = state.posCart.find(i => i.productId === productId);
            if (existing) {
                if (existing.qty < p.stock) {
                    existing.qty += 1;
                } else {
                    showToast(`Cannot exceed available warehouse stock (${p.stock})!`, 'warning');
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
                    showToast(`Maximum available stock reached (${p.stock})!`, 'warning');
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

        posPaymentModeChanged: function () {
            const mode = document.getElementById('posPaymentModeSelect')?.value || 'Cash';
            const notice = document.getElementById('posUdharNotice');
            if (notice) {
                if (mode.toLowerCase().includes('udhar')) {
                    notice.classList.remove('d-none');
                    const phoneInput = document.getElementById('posCustomerPhoneInput');
                    if (phoneInput && !phoneInput.value.trim()) {
                        phoneInput.focus();
                    }
                } else {
                    notice.classList.add('d-none');
                }
            }
        },

        posCompleteSale: async function () {
            if (state.posCart.length === 0) {
                showToast('POS cart is empty! Select products first.', 'warning');
                return;
            }

            const phone = (document.getElementById('posCustomerPhoneInput')?.value || '').trim();
            const customerName = phone ? `Walk-in (${phone})` : 'Walk-in Counter';
            const paymentMode = document.getElementById('posPaymentModeSelect')?.value || 'Cash';
            const isUdhar = paymentMode.toLowerCase().includes('udhar');

            if (isUdhar && !phone) {
                showToast('Customer Mobile Number or Name is required for Udhar (Store Credit / Khata) billing!', 'warning');
                const phoneInput = document.getElementById('posCustomerPhoneInput');
                if (phoneInput) phoneInput.focus();
                return;
            }

            const discount = parseFloat(state.posDiscount) || 0;
            const fetchFn = window.apiFetch || fetch;

            // Prepare POS checkout payload
            const payload = {
                customer_phone: phone,
                customer_name: customerName,
                payment_mode: paymentMode,
                discount_amount: discount,
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
                    showToast(data.error || data.message || 'POS Checkout failed on server.', 'danger');
                    return;
                }

                const total = Number(data.total || 0);
                const subtotal = Number(data.subtotal || total);
                const discAmt = Number(data.discount || 0);
                const cgst = Number(data.cgst || ((data.tax || 0) / 2));
                const sgst = Number(data.sgst || ((data.tax || 0) / 2));
                const billId = data.bill_number || `BILL-${data.bill_id || '0000'}`;
                const dateStr = new Date().toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' });

                // Populate thermal bill modal
                const billNumEl = document.getElementById('billModalNumber');
                if (billNumEl) billNumEl.textContent = billId;

                const billDateEl = document.getElementById('billModalDate');
                if (billDateEl) billDateEl.textContent = dateStr;

                const billCustEl = document.getElementById('billModalCustomer');
                if (billCustEl) billCustEl.textContent = (data.customer_name || phone || 'Walk-in');

                const billPayEl = document.getElementById('billModalPayment');
                if (billPayEl) billPayEl.textContent = data.payment_mode || paymentMode;

                const subtotalEl = document.getElementById('billModalSubtotal');
                if (subtotalEl) subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;

                const discRow = document.getElementById('billModalDiscountRow');
                const discEl = document.getElementById('billModalDiscount');
                if (discRow && discEl) {
                    if (discAmt > 0) {
                        discRow.style.display = 'flex';
                        discEl.textContent = `-₹${discAmt.toFixed(2)}`;
                    } else {
                        discRow.style.display = 'none';
                    }
                }

                const taxableEl = document.getElementById('billModalTaxable');
                if (taxableEl) taxableEl.textContent = `₹${Number(data.taxable_amount || (subtotal - discAmt)).toFixed(2)}`;

                const cgstEl = document.getElementById('billModalCGST');
                if (cgstEl) cgstEl.textContent = `₹${cgst.toFixed(2)}`;

                const sgstEl = document.getElementById('billModalSGST');
                if (sgstEl) sgstEl.textContent = `₹${sgst.toFixed(2)}`;

                const taxEl = document.getElementById('billModalTax');
                if (taxEl) taxEl.textContent = `₹${Number(data.tax || (cgst + sgst)).toFixed(2)}`;

                const totalEl = document.getElementById('billModalTotal');
                if (totalEl) totalEl.textContent = `₹${total.toFixed(2)}`;

                // Udhar breakdown in thermal receipt slip
                const udharRow = document.getElementById('billModalUdharRow');
                const udharBalEl = document.getElementById('billModalUdharBalance');
                if (udharRow) {
                    if (data.is_udhar || isUdhar) {
                        udharRow.style.display = 'block';
                        if (udharBalEl) {
                            udharBalEl.textContent = `₹${Number(data.customer_credit || total).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
                        }
                    } else {
                        udharRow.style.display = 'none';
                    }
                }

                const tbody = document.getElementById('billModalItemsTbody');
                if (tbody) {
                    tbody.innerHTML = state.posCart.map((c, idx) => {
                        const p = state.products.find(prod => prod.id === c.productId);
                        const name = p ? p.name : 'Item';
                        const price = p ? Number(p.price) : 0;
                        return `
                            <tr>
                                <td>${idx + 1}. ${escapeHTML(name)}</td>
                                <td class="text-center">${Number(c.qty)}</td>
                                <td class="text-end">₹${price.toFixed(2)}</td>
                                <td class="text-end fw-bold">₹${(price * c.qty).toFixed(2)}</td>
                            </tr>
                        `;
                    }).join('');
                }

                // Clear POS cart and reload live inventory
                state.posCart = [];
                state.posDiscount = 0;
                const discInput = document.getElementById('posDiscountInput');
                if (discInput) discInput.value = '';
                const phoneInput = document.getElementById('posCustomerPhoneInput');
                if (phoneInput) phoneInput.value = '';
                const notice = document.getElementById('posUdharNotice');
                if (notice) notice.classList.add('d-none');
                const paySelect = document.getElementById('posPaymentModeSelect');
                if (paySelect) paySelect.value = 'Cash';

                renderPOS();
                loadProductsData();
                loadCustomersData();
                logActionLocally('POS Counter Sale', `Billed #${billId} for ₹${total} (${data.payment_mode || paymentMode})`);
                showToast(`POS Sale completed! Bill #${billId}`, 'success');

                const modalEl = document.getElementById('billModal');
                if (modalEl && typeof bootstrap !== 'undefined') {
                    const modal = new bootstrap.Modal(modalEl);
                    modal.show();
                }

            } catch (err) {
                console.error('POS Checkout network error:', err);
                showToast('Network error connecting to POS billing service.', 'danger');
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
                showToast('Product name is required.', 'warning');
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
                    showToast(data.message || 'Product created successfully in database!', 'success');
                    const modalEl = document.getElementById('addProductModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    loadProductsData();
                } else {
                    showToast(data.message || 'Failed to save product on server.', 'danger');
                }
            } catch (err) {
                console.error('Save product error:', err);
                showToast('Network error while saving product.', 'danger');
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
                    showToast('Product updated successfully!', 'success');
                    const modalEl = document.getElementById('editProductModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    loadProductsData();
                } else {
                    showToast(data.message || 'Failed to update product.', 'danger');
                }
            } catch (err) {
                console.error('Update product error:', err);
                showToast('Network error updating product.', 'danger');
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
                    showToast(`Product "${p.name}" deactivated.`, 'info');
                    loadProductsData();
                } else {
                    showToast(data.message || 'Could not deactivate product.', 'danger');
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
                    showToast(`Order #${orderId} moved to ${newStatus}`, 'success');
                    loadOrdersData();
                } else {
                    showToast(data.message || 'Invalid status transition.', 'danger');
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
                    document.getElementById('orderDetailModalCustomer').textContent = data.customer_name || `Customer #${data.user_id}`;
                    document.getElementById('orderDetailModalPhone').textContent = data.customer_phone || (data.shipping_address ? data.shipping_address.substring(0, 35) : '-');
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

                    const slipBtn = document.getElementById('orderDetailPrintSlipBtn');
                    if (slipBtn) {
                        slipBtn.onclick = () => {
                            const detailModalEl = document.getElementById('orderDetailModal');
                            const detailModal = bootstrap.Modal.getInstance(detailModalEl);
                            if (detailModal) detailModal.hide();
                            window.Adm.viewOrderReceipt(orderId);
                        };
                    }

                    const modalEl = document.getElementById('orderDetailModal');
                    const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
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
            if (!name) {
                showToast('Category name is required.', 'warning');
                return;
            }

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn('/api/admin/categories/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name, description: desc })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    showToast('Category created successfully!', 'success');
                    const modalEl = document.getElementById('addCategoryModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    loadCategoriesData();
                } else {
                    showToast(data.message || 'Failed to create category.', 'danger');
                }
            } catch (err) {
                console.error('Create category error:', err);
                showToast('Network error creating category.', 'danger');
            }
        },

        openRecordPurchaseModal: function (supplierArg) {
            const suppSelect = document.getElementById('purchaseSupplierSelect');
            if (suppSelect && state.suppliers && state.suppliers.length > 0) {
                suppSelect.innerHTML = state.suppliers.map(s => `
                    <option value="${s.id}">${escapeHTML(s.name)} (AP Due: ₹${Number(s.outstanding_balance || 0).toLocaleString('en-IN')})</option>
                `).join('');
                if (supplierArg) {
                    if (typeof supplierArg === 'number' || !isNaN(Number(supplierArg))) {
                        suppSelect.value = String(supplierArg);
                    } else {
                        const found = state.suppliers.find(s => s.name === supplierArg);
                        if (found) suppSelect.value = String(found.id);
                    }
                }
            }

            const prodSelect = document.getElementById('purchaseProductSelect');
            if (prodSelect && state.products && state.products.length > 0) {
                prodSelect.innerHTML = state.products.map(p => `
                    <option value="${p.id}">${escapeHTML(p.name)} [Stock: ${p.stock}, WAC Cost: ₹${p.cost}]</option>
                `).join('');
            }

            const modalEl = document.getElementById('addPurchaseModal');
            if (modalEl && typeof bootstrap !== 'undefined') {
                const modal = new bootstrap.Modal(modalEl);
                modal.show();
            }
        },

        saveNewPurchase: async function (e) {
            if (e) e.preventDefault();
            const suppSelect = document.getElementById('purchaseSupplierSelect');
            const prodSelect = document.getElementById('purchaseProductSelect');
            const qty = parseInt(document.getElementById('purchaseQty')?.value) || 0;
            const unitCost = parseFloat(document.getElementById('purchaseUnitCost')?.value) || 0;
            const supplierId = parseInt(suppSelect?.value) || 1;
            const productId = parseInt(prodSelect?.value) || 1;
            const invoiceNum = (document.getElementById('purchaseInvoiceNum')?.value || '').trim();
            const paymentStatus = document.getElementById('purchasePaymentStatus')?.value || 'Credit';
            const paymentMode = document.getElementById('purchasePaymentMode')?.value || 'Credit';

            if (qty <= 0) {
                showToast('Quantity must be greater than zero.', 'warning');
                return;
            }
            if (unitCost <= 0) {
                showToast('Wholesale unit price must be greater than zero.', 'warning');
                return;
            }

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn('/api/admin/purchases/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        supplier_id: supplierId,
                        product_id: productId,
                        quantity: qty,
                        purchase_price: unitCost,
                        invoice_number: invoiceNum,
                        payment_status: paymentStatus.includes('Paid') ? 'Paid' : 'Credit',
                        payment_mode: paymentMode
                    })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    showToast(data.message || 'Stock purchase recorded with blended WAC cost!', 'success');
                    const modalEl = document.getElementById('addPurchaseModal');
                    if (modalEl && typeof bootstrap !== 'undefined') {
                        const modal = bootstrap.Modal.getInstance(modalEl);
                        if (modal) modal.hide();
                    }
                    loadPurchasesData();
                    loadProductsData();
                    loadSuppliersData();
                } else {
                    showToast(data.message || data.error || 'Failed to record stock purchase.', 'danger');
                }
            } catch (err) {
                console.error('Purchase record error:', err);
                showToast('Network error recording purchase.', 'danger');
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
                    showToast('Coupon status updated.', 'success');
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
                showToast('Coupon code and discount value are required.', 'warning');
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
                    showToast(data.message || `Coupon ${code} published successfully!`, 'success');
                    const modalEl = document.getElementById('createCouponModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    if (codeInput) codeInput.value = '';
                    if (discInput) discInput.value = '';
                    loadCouponsData();
                } else {
                    showToast(data.message || 'Could not publish coupon.', 'danger');
                }
            } catch (err) {
                console.error('Save coupon error:', err);
                showToast('Network error publishing coupon.', 'danger');
            }
        },

        toggle2FA: function () {
            const toggle = document.getElementById('security2faToggle');
            const isChecked = toggle ? toggle.checked : false;
            if (isChecked) {
                showToast('To complete 2FA setup, visit the Security console or scan the TOTP QR key.', 'info');
            } else {
                showToast('Two-factor authentication toggle updated.', 'info');
            }
        },

        clearCustomerUdhar: async function (customerId, amount) {
            const entered = prompt(`Enter amount to settle for Customer #${customerId} (Balance: ₹${amount}):`, amount);
            if (entered === null) return;
            const amountPaid = parseFloat(entered);
            if (isNaN(amountPaid) || amountPaid <= 0 || amountPaid > amount) {
                showToast('Please enter a valid amount within current credit balance.', 'warning');
                return;
            }

            const modeChoice = prompt('Payment Method:\n1. Cash Register\n2. UPI / QR\n3. Bank Transfer', '1');
            if (modeChoice === null) return;
            let paymentMode = 'Cash';
            if (modeChoice.trim() === '2' || modeChoice.toLowerCase().includes('upi')) paymentMode = 'UPI';
            else if (modeChoice.trim() === '3' || modeChoice.toLowerCase().includes('bank')) paymentMode = 'Bank Transfer';

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn(`/api/admin/customers/${customerId}/clear_credit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ amount_paid: amountPaid, payment_mode: paymentMode })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    showToast(data.message || 'Udhar collected and ledger updated!', 'success');
                    loadCustomersData();
                    if (state.expenses) loadExpensesData();
                } else {
                    showToast(data.message || 'Could not settle credit.', 'danger');
                }
            } catch (err) {
                console.error('Clear credit error:', err);
                showToast('Network error settling credit.', 'danger');
            }
        },

        paySupplier: async function (supplierId, supplierName, currentDue) {
            const entered = prompt(`Disburse AP payment to ${supplierName}\nCurrent Accounts Payable (AP) Due: ₹${currentDue}\nEnter disbursement amount (₹):`, currentDue);
            if (entered === null) return;
            const amountPaid = parseFloat(entered);
            if (isNaN(amountPaid) || amountPaid <= 0) {
                showToast('Please enter a valid disbursement amount greater than zero.', 'warning');
                return;
            }

            const modeChoice = prompt('Disbursement Payment Mode:\n1. Bank Transfer (NEFT/IMPS)\n2. Store UPI / QR\n3. Cash Register\n4. Bank Cheque', '1');
            if (modeChoice === null) return;
            let paymentMode = 'Bank Transfer';
            if (modeChoice.trim() === '2' || modeChoice.toLowerCase().includes('upi')) paymentMode = 'UPI';
            else if (modeChoice.trim() === '3' || modeChoice.toLowerCase().includes('cash')) paymentMode = 'Cash';
            else if (modeChoice.trim() === '4' || modeChoice.toLowerCase().includes('cheque')) paymentMode = 'Cheque';

            const notes = prompt('Enter reference / bank transaction UTR (optional):', `Vendor settlement for ${supplierName}`) || '';

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn(`/api/admin/suppliers/${supplierId}/pay`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ amount_paid: amountPaid, payment_mode: paymentMode, notes: notes })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    showToast(data.message || 'Vendor AP settled and cash outflow logged!', 'success');
                    loadSuppliersData();
                    if (state.expenses) loadExpensesData();
                } else {
                    showToast(data.message || 'Could not disburse payment.', 'danger');
                }
            } catch (err) {
                console.error('Disburse AP error:', err);
                showToast('Network error processing payment.', 'danger');
            }
        },

        openAddSupplierModal: function () {
            const form = document.getElementById('supplierForm');
            if (form) form.reset();
            const idInput = document.getElementById('supplierFormId');
            if (idInput) idInput.value = '';
            const title = document.getElementById('supplierModalLabel');
            if (title) title.innerHTML = '<i class="bi bi-building-add me-2 text-success"></i>Add New Supplier';
            const submitBtn = document.getElementById('supplierFormSubmitBtn');
            if (submitBtn) submitBtn.textContent = 'Save Supplier';

            const modalEl = document.getElementById('supplierModal');
            if (modalEl && typeof bootstrap !== 'undefined') {
                const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                modal.show();
            }
        },

        openEditSupplierModal: function (supplierId) {
            const s = state.suppliers.find(sup => sup.id === Number(supplierId));
            if (!s) {
                showToast('Supplier not found in local cache.', 'warning');
                return;
            }
            const idInput = document.getElementById('supplierFormId');
            if (idInput) idInput.value = s.id;
            const nameInput = document.getElementById('supplierFormName');
            if (nameInput) nameInput.value = s.name || '';
            const contactInput = document.getElementById('supplierFormContact');
            if (contactInput) contactInput.value = s.contact || '';
            const phoneInput = document.getElementById('supplierFormPhone');
            if (phoneInput) phoneInput.value = s.phone || '';
            const emailInput = document.getElementById('supplierFormEmail');
            if (emailInput) emailInput.value = s.email || '';
            const gstinInput = document.getElementById('supplierFormGstin');
            if (gstinInput) gstinInput.value = s.gstin || '';
            const addressInput = document.getElementById('supplierFormAddress');
            if (addressInput) addressInput.value = s.address || '';
            const bankInput = document.getElementById('supplierFormBank');
            if (bankInput) bankInput.value = s.bank_details || '';

            const title = document.getElementById('supplierModalLabel');
            if (title) title.innerHTML = `<i class="bi bi-pencil-square me-2 text-primary"></i>Edit Supplier: ${escapeHTML(s.name)}`;
            const submitBtn = document.getElementById('supplierFormSubmitBtn');
            if (submitBtn) submitBtn.textContent = 'Update Supplier';

            const modalEl = document.getElementById('supplierModal');
            if (modalEl && typeof bootstrap !== 'undefined') {
                const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                modal.show();
            }
        },

        saveSupplier: async function (e) {
            if (e && e.preventDefault) e.preventDefault();
            const id = (document.getElementById('supplierFormId')?.value || '').trim();
            const name = (document.getElementById('supplierFormName')?.value || '').trim();
            if (!name) {
                showToast('Supplier Name is required.', 'warning');
                return;
            }

            const payload = {
                name: name,
                contact_person: (document.getElementById('supplierFormContact')?.value || '').trim(),
                phone: (document.getElementById('supplierFormPhone')?.value || '').trim(),
                email: (document.getElementById('supplierFormEmail')?.value || '').trim(),
                gstin: (document.getElementById('supplierFormGstin')?.value || '').trim(),
                address: (document.getElementById('supplierFormAddress')?.value || '').trim(),
                bank_details: (document.getElementById('supplierFormBank')?.value || '').trim()
            };

            const isEdit = Boolean(id);
            const url = isEdit ? `/api/admin/suppliers/${id}` : '/api/admin/suppliers/add';
            const method = isEdit ? 'PUT' : 'POST';
            const fetchFn = window.apiFetch || fetch;

            try {
                const res = await fetchFn(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    showToast(data.message || (isEdit ? 'Supplier updated successfully!' : 'Supplier added successfully!'), 'success');
                    const modalEl = document.getElementById('supplierModal');
                    if (modalEl && typeof bootstrap !== 'undefined') {
                        const modal = bootstrap.Modal.getInstance(modalEl);
                        if (modal) modal.hide();
                    }
                    loadSuppliersData();
                } else {
                    showToast(data.message || data.error || 'Failed to save supplier.', 'danger');
                }
            } catch (err) {
                console.error('Save supplier error:', err);
                showToast('Network error saving supplier.', 'danger');
            }
        },

        deleteSupplier: async function (supplierId, supplierName) {
            if (!confirm(`Are you sure you want to delete supplier "${supplierName}"?\n\nNote: If this supplier has past purchase orders or outstanding Accounts Payable, deletion will be safely blocked.`)) {
                return;
            }

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn(`/api/admin/suppliers/${supplierId}`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    showToast(data.message || `Supplier "${supplierName}" deleted successfully!`, 'success');
                    loadSuppliersData();
                } else {
                    showToast(data.message || data.error || 'Could not delete supplier.', 'danger');
                }
            } catch (err) {
                console.error('Delete supplier error:', err);
                showToast('Network error deleting supplier.', 'danger');
            }
        },

        populateThermalModal: function (data) {
            if (!data) return;

            // 1. Bill Number
            const billNumEl = document.getElementById('billModalNumber');
            if (billNumEl) {
                billNumEl.textContent = data.bill_number || (data.bill_id ? `#SAL-${String(data.bill_id).padStart(4, '0')}` : '#BILL-0000');
            }

            // 2. Date
            const billDateEl = document.getElementById('billModalDate');
            if (billDateEl) {
                let formattedDate = 'Recent';
                if (data.sale_date) {
                    try {
                        const d = new Date(data.sale_date);
                        formattedDate = isNaN(d.getTime()) ? String(data.sale_date) : d.toLocaleString('en-IN', {
                            dateStyle: 'short',
                            timeStyle: 'medium'
                        });
                    } catch (e) {
                        formattedDate = String(data.sale_date);
                    }
                }
                billDateEl.textContent = formattedDate;
            }

            // 3. Customer
            const billCustEl = document.getElementById('billModalCustomer');
            if (billCustEl) {
                const cName = data.customer_name && data.customer_name !== 'undefined' ? data.customer_name : 'Walk-in Counter';
                const cPhone = data.customer_phone && data.customer_phone !== 'undefined' ? ` (${data.customer_phone})` : '';
                billCustEl.textContent = `${cName}${cPhone}`;
            }

            // 4. Payment Mode
            const billPayEl = document.getElementById('billModalPayment');
            if (billPayEl) {
                billPayEl.textContent = data.payment_method || data.payment_mode || 'Cash';
            }

            // 5. Pricing & Taxes
            const totalVal = Number(data.total_price !== undefined ? data.total_price : (data.total || 0));
            const subtotalVal = Number(data.subtotal !== undefined ? data.subtotal : totalVal);
            const discVal = Number(data.discount || 0);
            const taxableVal = Number(data.taxable_amount !== undefined ? data.taxable_amount : (subtotalVal - discVal));
            const cgstVal = Number(data.cgst !== undefined ? data.cgst : ((data.tax || 0) / 2));
            const sgstVal = Number(data.sgst !== undefined ? data.sgst : ((data.tax || 0) / 2));

            const subtotalEl = document.getElementById('billModalSubtotal');
            if (subtotalEl) subtotalEl.textContent = `₹${subtotalVal.toFixed(2)}`;

            const discRow = document.getElementById('billModalDiscountRow');
            const discEl = document.getElementById('billModalDiscount');
            if (discRow && discEl) {
                if (discVal > 0) {
                    discRow.style.display = 'flex';
                    discEl.textContent = `-₹${discVal.toFixed(2)}`;
                } else {
                    discRow.style.display = 'none';
                }
            }

            const taxableEl = document.getElementById('billModalTaxable');
            if (taxableEl) taxableEl.textContent = `₹${taxableVal.toFixed(2)}`;

            const cgstEl = document.getElementById('billModalCGST');
            if (cgstEl) cgstEl.textContent = `₹${cgstVal.toFixed(2)}`;

            const sgstEl = document.getElementById('billModalSGST');
            if (sgstEl) sgstEl.textContent = `₹${sgstVal.toFixed(2)}`;

            const totalEl = document.getElementById('billModalTotal');
            if (totalEl) totalEl.textContent = `₹${totalVal.toFixed(2)}`;

            // Udhar Breakdown (if applicable)
            const udharRow = document.getElementById('billModalUdharRow');
            const udharBalEl = document.getElementById('billModalUdharBalance');
            if (udharRow) {
                if (data.is_udhar || (data.payment_method && data.payment_method.toUpperCase().includes('UDHAR'))) {
                    udharRow.style.display = 'block';
                    if (udharBalEl) {
                        udharBalEl.textContent = `₹${Number(data.customer_credit || totalVal).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
                    }
                } else {
                    udharRow.style.display = 'none';
                }
            }

            // 6. Items Table
            const tbody = document.getElementById('billModalItemsTbody');
            if (tbody) {
                let itemsList = data.items;
                if (!itemsList || itemsList.length === 0) {
                    if (data.product_name) {
                        itemsList = [{
                            product_name: data.product_name,
                            quantity: data.quantity || 1,
                            unit_price: data.unit_price || (totalVal / (data.quantity || 1)),
                            total_price: totalVal
                        }];
                    } else {
                        itemsList = [];
                    }
                }
                tbody.innerHTML = itemsList.map((item, idx) => `
                    <tr>
                        <td class="text-start py-1">${idx + 1}. ${escapeHTML(item.product_name || 'Item')}</td>
                        <td class="text-center py-1">${Number(item.quantity || 1)}</td>
                        <td class="text-end py-1">₹${Number(item.unit_price || (item.total_price / (item.quantity || 1))).toFixed(2)}</td>
                        <td class="text-end py-1 fw-bold">₹${Number(item.total_price).toFixed(2)}</td>
                    </tr>
                `).join('');
            }

            const modalEl = document.getElementById('billModal');
            if (modalEl && typeof bootstrap !== 'undefined') {
                const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                modal.show();
            }
        },

        viewReceipt: async function (saleId) {
            const fetchFn = window.apiFetch || fetch;
            let data = null;
            try {
                const res = await fetchFn(`/api/admin/sales/bill/${saleId}`);
                if (res.ok) {
                    data = await res.json();
                }
            } catch (err) {
                console.warn('Could not fetch receipt from API, trying local state fallback:', err);
            }

            // Fallback from local state if API request failed
            if (!data && state.sales) {
                const localSale = state.sales.find(s => String(s.id) === String(saleId));
                if (localSale) {
                    const tot = Number(localSale.total_price || 0);
                    const qty = Number(localSale.quantity || 1);
                    data = {
                        bill_number: localSale.bill_number || `#SAL-${String(localSale.id).padStart(4, '0')}`,
                        customer_name: localSale.customer_name || 'Walk-in Counter',
                        customer_phone: localSale.customer_phone || '',
                        payment_method: localSale.payment_method || 'Cash',
                        sale_date: localSale.sale_date,
                        total_price: tot,
                        subtotal: tot,
                        discount: 0,
                        taxable_amount: (tot / 1.05),
                        cgst: ((tot - (tot / 1.05)) / 2),
                        sgst: ((tot - (tot / 1.05)) / 2),
                        items: [
                            {
                                product_name: localSale.product_name || 'Grocery Item',
                                quantity: qty,
                                unit_price: tot / qty,
                                total_price: tot
                            }
                        ]
                    };
                }
            }

            if (!data) {
                showToast('Could not load receipt data for this transaction.', 'danger');
                return;
            }

            window.Adm.populateThermalModal(data);
        },

        viewOrderReceipt: async function (orderId) {
            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn(`/api/orders/${orderId}/slip`);
                if (!res.ok) {
                    showToast('Could not load order receipt slip.', 'danger');
                    return;
                }
                const data = await res.json();
                window.Adm.populateThermalModal(data);
            } catch (err) {
                console.error('View order receipt error:', err);
                showToast('Network error loading order slip.', 'danger');
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
            if (state.lastDashboardData && typeof Chart !== 'undefined') {
                renderModernSalesChart(state.lastDashboardData.chart_data);
                renderModernOrderStatusChart();
            }
        },

        toggleSidebar: function (forceState) {
            const sidebar = document.getElementById('adminSidebar');
            let backdrop = document.getElementById('admSidebarBackdrop');
            if (!backdrop) {
                backdrop = document.createElement('div');
                backdrop.id = 'admSidebarBackdrop';
                backdrop.className = 'adm-sidebar-backdrop';
                backdrop.onclick = () => window.Adm.toggleSidebar(false);
                document.body.appendChild(backdrop);
            }
            if (typeof forceState === 'boolean') {
                if (forceState) {
                    if (sidebar) sidebar.classList.add('show-mobile');
                    backdrop.classList.add('show');
                } else {
                    if (sidebar) sidebar.classList.remove('show-mobile');
                    backdrop.classList.remove('show');
                }
            } else {
                if (sidebar) {
                    const isOpen = sidebar.classList.toggle('show-mobile');
                    backdrop.classList.toggle('show', isOpen);
                }
            }
        },

        saveNewExpense: async function (event) {
            if (event) event.preventDefault();
            const category = document.getElementById('expCategoryInput')?.value;
            const amount = parseFloat(document.getElementById('expAmountInput')?.value || 0);
            const paymentMode = document.getElementById('expPaymentModeInput')?.value;
            const expenseType = document.getElementById('expTypeInput')?.value || 'OpEx';
            const expenseDate = document.getElementById('expDateInput')?.value;
            const isRecurring = document.getElementById('expRecurringInput')?.checked || false;
            const description = document.getElementById('expDescInput')?.value?.trim();

            if (!amount || amount <= 0) {
                showToast('Please enter a valid expense amount greater than zero.', 'warning');
                return;
            }

            try {
                const fetchFn = window.apiFetch || fetch;
                const res = await fetchFn('/api/admin/expenses/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        category: category,
                        amount: amount,
                        payment_mode: paymentMode,
                        expense_type: expenseType,
                        expense_date: expenseDate,
                        is_recurring: isRecurring,
                        description: description
                    })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    showToast(`Expense of ₹${amount} recorded under ${category} (${expenseType})!`, 'success');
                    const modalEl = document.getElementById('recordExpenseModal');
                    if (modalEl && typeof bootstrap !== 'undefined') {
                        const modalInstance = bootstrap.Modal.getInstance(modalEl);
                        if (modalInstance) modalInstance.hide();
                    }
                    loadExpensesData();
                    loadDashboardData();
                } else {
                    showToast(data.message || 'Failed to record expense.', 'danger');
                }
            } catch (err) {
                console.error('Save expense error:', err);
                showToast('Server error while saving expense.', 'danger');
            }
        },

        deleteExpense: async function (expenseId) {
            if (!confirm(`Archive / soft-delete expense record #${expenseId}?\nThis will retain the transaction in audit history while safely excluding it from active operating totals.`)) return;
            try {
                const fetchFn = window.apiFetch || fetch;
                const res = await fetchFn(`/api/admin/expenses/${expenseId}`, {
                    method: 'DELETE'
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    showToast(data.message || 'Expense archived successfully.', 'info');
                    loadExpensesData();
                    loadDashboardData();
                } else {
                    showToast(data.message || 'Failed to archive expense.', 'danger');
                }
            } catch (err) {
                console.error('Delete expense error:', err);
                showToast('Error archiving expense.', 'danger');
            }
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
