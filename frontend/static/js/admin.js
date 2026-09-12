/**
 * E-GROSSARY — CONSOLIDATED ADMIN ERP CONSOLE ENGINE (admin.js)
 * Enterprise state management, multi-module hash router, Chart.js analytics, POS billing, and inventory controls.
 */

(function () {
    'use strict';

    // ── Pre-Seeded ERP Data ──
    const DEFAULT_PRODUCTS = [
        { id: 1, sku: 'JG-STA-001', name: 'Aashirvaad Superior MP Atta 5kg', category: 'Staples & Grains', cost: 240, price: 279, stock: 50, image: 'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=300&q=80' },
        { id: 2, sku: 'JG-SPI-001', name: 'Tata Salt Vacuum Evaporated 1kg', category: 'Masala & Spices', cost: 28, price: 36, stock: 100, image: 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=300&q=80' },
        { id: 3, sku: 'JG-DAI-001', name: 'Amul Taaza Fresh Toned Milk 1L', category: 'Dairy & Breakfast', cost: 48, price: 56, stock: 60, image: 'https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=300&q=80' },
        { id: 4, sku: 'JG-SNK-001', name: 'Maggi 2-Minute Masala Instant Noodles 280g', category: 'Snacks & Biscuits', cost: 34, price: 42, stock: 80, image: 'https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=300&q=80' },
        { id: 5, sku: 'JG-BEV-001', name: 'Tata Tea Premium Desh Ki Chai 250g', category: 'Beverages', cost: 110, price: 132, stock: 45, image: 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=300&q=80' },
        { id: 6, sku: 'JG-SNK-002', name: 'Cadbury Dairy Milk Silk Chocolate 120g', category: 'Snacks & Biscuits', cost: 80, price: 98, stock: 75, image: 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?auto=format&fit=crop&w=300&q=80' },
        { id: 7, sku: 'JG-STA-002', name: 'Fortune Sunlite Refined Sunflower Oil 1L', category: 'Staples & Grains', cost: 165, price: 199, stock: 45, image: 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=300&q=80' },
        { id: 8, sku: 'JG-DAI-002', name: 'Amul Pasteurised Salted Butter 500g', category: 'Dairy & Breakfast', cost: 125, price: 145, stock: 50, image: 'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?auto=format&fit=crop&w=300&q=80' },
        { id: 9, sku: 'JG-SNK-003', name: 'Britannia Good Day Cashew Cookies 100g', category: 'Snacks & Biscuits', cost: 32, price: 40, stock: 90, image: 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?auto=format&fit=crop&w=300&q=80' },
        { id: 10, sku: 'JG-STA-003', name: 'Tata Sampann Unpolished Toor Dal 1kg', category: 'Staples & Grains', cost: 72, price: 89, stock: 60, image: 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=300&q=80' },
        { id: 11, sku: 'JG-HOU-001', name: 'Surf Excel Easy Wash Detergent Powder 1kg', category: 'Household', cost: 135, price: 165, stock: 55, image: 'https://images.unsplash.com/photo-1583947215259-38e31be8751f?auto=format&fit=crop&w=300&q=80' },
        { id: 12, sku: 'JG-HOU-002', name: 'Harpic Power Plus Toilet Cleaner 500ml', category: 'Household', cost: 78, price: 99, stock: 40, image: 'https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=300&q=80' },
        { id: 13, sku: 'JG-VEG-001', name: 'Fresh Farm Crisp Organic Tomatoes 1kg', category: 'Fruits & Vegetables', cost: 25, price: 35, stock: 50, image: 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=300&q=80' },
        { id: 14, sku: 'JG-VEG-002', name: 'Fresh Farm Green Spinach (Palak) 250g', category: 'Fruits & Vegetables', cost: 15, price: 22, stock: 30, image: 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=300&q=80' },
        { id: 15, sku: 'JG-VEG-003', name: 'Ratnagiri Alphonso Mangoes (1 Dozen)', category: 'Fruits & Vegetables', cost: 450, price: 599, stock: 25, image: 'https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&w=300&q=80' },
        { id: 16, sku: 'JG-PER-001', name: 'Dabur Red Ayurvedic Toothpaste 300g', category: 'Personal Care', cost: 115, price: 140, stock: 45, image: 'https://images.unsplash.com/photo-1559650656-5d1d42e99e69?auto=format&fit=crop&w=300&q=80' }
    ];

    const DEFAULT_CATEGORIES = [
        { id: 1, name: 'Fruits & Vegetables', desc: 'Fresh farm produce, fruits, leafy greens and organic vegetables', icon: '🥦' },
        { id: 2, name: 'Dairy & Breakfast', desc: 'Pure cow milk, butter, ghee, curd, paneer and breakfast spreads', icon: '🥛' },
        { id: 3, name: 'Staples & Grains', desc: 'Stone-ground flours, premium basmati rice, lentils and cold-pressed oils', icon: '🌾' },
        { id: 4, name: 'Snacks & Biscuits', desc: 'Cookies, healthy roasted snacks, dry fruits and chocolates', icon: '🍿' },
        { id: 5, name: 'Beverages', desc: 'Premium teas, artisanal coffees, fruit juices and healthy drinks', icon: '🧃' },
        { id: 6, name: 'Personal Care', desc: 'Natural soaps, oral care, shampoos and grooming essentials', icon: '✨' },
        { id: 7, name: 'Household', desc: 'Detergents, surface cleaners, dishwash and kitchen essentials', icon: '🧼' },
        { id: 8, name: 'Masala & Spices', desc: 'Pure hand-pounded spices, rock salt, turmeric and whole seeds', icon: '🌶️' }
    ];

    const DEFAULT_ORDERS = [
        { id: 'JG-849201', customer: 'Priya Patel', phone: '+91 98251 22334', date: 'Today, 07:45 PM', status: 'Out for Delivery', total: 244, payment: 'UPI (GPay)', items: [{ name: 'Amul Taaza Milk 1L', qty: 2, price: 56 }, { name: 'Fresh Organic Tomatoes 1kg', qty: 1, price: 35 }, { name: 'Tata Tea Premium 250g', qty: 1, price: 132 }] },
        { id: 'JG-849195', customer: 'Rahul Sharma', phone: '+91 98765 43210', date: 'Yesterday, 06:12 PM', status: 'Delivered', total: 514, payment: 'Cash on Delivery', items: [{ name: 'Aashirvaad Atta 5kg', qty: 1, price: 279 }, { name: 'Fortune Sunflower Oil 1L', qty: 1, price: 199 }, { name: 'Tata Salt 1kg', qty: 1, price: 36 }] },
        { id: 'JG-849182', customer: 'Amit Choudhary', phone: '+91 97240 55667', date: '3 days ago', status: 'Delivered', total: 402, payment: 'UPI (PhonePe)', items: [{ name: 'Maggi Instant Noodles 280g', qty: 3, price: 42 }, { name: 'Cadbury Silk 120g', qty: 2, price: 98 }, { name: 'Good Day Cookies 100g', qty: 2, price: 40 }] },
        { id: 'JG-849150', customer: 'Ramesh Bhai Patel', phone: '+91 99090 77889', date: '5 days ago', status: 'Delivered', total: 442, payment: 'UDHAR (Khata)', items: [{ name: 'Tata Toor Dal 1kg', qty: 2, price: 89 }, { name: 'Surf Excel Powder 1kg', qty: 1, price: 165 }, { name: 'Harpic Cleaner 500ml', qty: 1, price: 99 }] },
        { id: 'JG-849090', customer: 'Priya Patel', phone: '+91 98251 22334', date: '8 days ago', status: 'Delivered', total: 788, payment: 'UPI (GPay)', items: [{ name: 'Amul Salted Butter 500g', qty: 1, price: 145 }, { name: 'Alphonso Mangoes (1 Dozen)', qty: 1, price: 599 }, { name: 'Fresh Green Spinach 250g', qty: 2, price: 22 }] }
    ];

    const DEFAULT_CUSTOMERS = [
        { id: 1, name: 'Priya Patel', email: 'customer@mart.com', phone: '+91 98251 22334', city: 'Mehsana', orders: 14, spend: 6840 },
        { id: 2, name: 'Rahul Sharma', email: 'rahul.sharma@gmail.com', phone: '+91 98765 43210', city: 'Unjha', orders: 9, spend: 4320 },
        { id: 3, name: 'Amit Choudhary', email: 'amit.choudhary@yahoo.com', phone: '+91 97240 55667', city: 'Pali', orders: 6, spend: 3150 },
        { id: 4, name: 'Ramesh Bhai Patel', email: 'rameshbhai.patel@gmail.com', phone: '+91 99090 77889', city: 'Unjha', orders: 18, spend: 9400 }
    ];

    const DEFAULT_SUPPLIERS = [
        { id: 1, name: 'Gujarat Co-operative (Amul)', contact: 'Ramesh Bhai Patel', phone: '+91 2692 258506', email: 'orders@amul.coop', category: 'Dairy & Milk' },
        { id: 2, name: 'ITC Limited Food Distribution', contact: 'Vikram Mehta', phone: '+91 79 2656 4300', email: 'ahmedabad.sales@itc.in', category: 'Atta & Staples' },
        { id: 3, name: 'Tata Consumer Products Hub', contact: 'Suresh Joshi', phone: '+91 265 233 1140', email: 'west.orders@tataconsumer.com', category: 'Tea, Salt & Dals' },
        { id: 4, name: 'Unjha APMC Mandi Spices Traders', contact: 'Rameshwar Lal Patel', phone: '+91 2767 254210', email: 'trade@unjhaspices.com', category: 'Pure Spices & Seeds' },
        { id: 5, name: 'Hindustan Unilever Depot Mehsana', contact: 'Sanjay Rawat', phone: '+91 2762 251120', email: 'mehsana.supply@hul.com', category: 'Soaps & Detergents' },
        { id: 6, name: 'Adani Wilmar (Fortune Foods)', contact: 'Dhaval Shah', phone: '+91 79 2656 5555', email: 'sales@adaniwilmar.in', category: 'Cooking Oils & Grains' },
        { id: 7, name: 'Britannia Sanand Logistics Hub', contact: 'Ankit Verma', phone: '+91 2717 618000', email: 'orders.gujarat@britindia.com', category: 'Cookies & Biscuits' },
        { id: 8, name: 'Nestle India Distribution Centre', contact: 'Pooja Nair', phone: '+91 22 2497 0000', email: 'consumer.care@in.nestle.com', category: 'Noodles & Beverages' }
    ];

    const DEFAULT_PURCHASES = [
        { id: 'PO-9201', invoice: 'INV-AMUL-4820', supplier: 'Gujarat Co-operative (Amul)', date: '09 Sep 2026', itemsCount: 150, total: 11050 },
        { id: 'PO-9188', invoice: 'INV-ITC-1092', supplier: 'ITC Limited Food Distribution', date: '07 Sep 2026', itemsCount: 80, total: 19200 },
        { id: 'PO-9162', invoice: 'INV-TATA-3341', supplier: 'Tata Consumer Products Hub', date: '05 Sep 2026', itemsCount: 285, total: 16200 },
        { id: 'PO-9140', invoice: 'INV-HUL-8890', supplier: 'Hindustan Unilever Depot Mehsana', date: '02 Sep 2026', itemsCount: 70, total: 9450 }
    ];

    const DEFAULT_COUPONS = [
        { id: 1, code: 'WELCOME50', discount: '₹50 OFF', minSpend: 299, expiry: '31 Dec 2026', used: 48, active: true },
        { id: 2, code: 'JAYGOGA100', discount: '₹100 OFF', minSpend: 499, expiry: '31 Dec 2026', used: 135, active: true },
        { id: 3, code: 'FRESH15', discount: '15% OFF', minSpend: 199, expiry: '31 Dec 2026', used: 74, active: true },
        { id: 4, code: 'GROCERY10', discount: '10% OFF', minSpend: 399, expiry: '31 Dec 2026', used: 92, active: true }
    ];

    const DEFAULT_ACTIVITY = [
        { id: 1, time: 'Today, 07:45 PM', actor: 'Admin (Dispatch)', action: 'Order Dispatched', details: 'Assigned order #JG-849201 for 15-min delivery to Priya Patel' },
        { id: 2, time: 'Today, 06:30 PM', actor: 'Admin (Counter POS)', action: 'POS Counter Sale', details: 'Billed 3 items worth ₹480 (UPI Payment)' },
        { id: 3, time: 'Yesterday, 04:15 PM', actor: 'Admin (Inventory)', action: 'Stock Inward Recorded', details: 'Received 100 units Amul Taaza Milk from Amul Anand Hub' },
        { id: 4, time: 'Yesterday, 02:00 PM', actor: 'Admin (System)', action: 'Price Updated', details: 'Adjusted seasonal Alphonso Mangoes selling price to ₹599/Dozen' },
        { id: 5, time: '07 Sep, 11:20 AM', actor: 'Admin (Promotions)', action: 'Coupon Published', details: 'Active promo voucher code JAYGOGA100 enabled' }
    ];

    // ── Local State Engine & Version Migration ──
    const DATA_VERSION = '2026-v2-real';
    if (localStorage.getItem('jg_admin_data_ver') !== DATA_VERSION) {
        localStorage.setItem('jg_admin_data_ver', DATA_VERSION);
        localStorage.setItem('jg_admin_products', JSON.stringify(DEFAULT_PRODUCTS));
        localStorage.setItem('jg_admin_categories', JSON.stringify(DEFAULT_CATEGORIES));
        localStorage.setItem('jg_orders', JSON.stringify(DEFAULT_ORDERS));
        localStorage.setItem('jg_admin_customers', JSON.stringify(DEFAULT_CUSTOMERS));
        localStorage.setItem('jg_admin_suppliers', JSON.stringify(DEFAULT_SUPPLIERS));
        localStorage.setItem('jg_admin_purchases', JSON.stringify(DEFAULT_PURCHASES));
        localStorage.setItem('jg_admin_coupons', JSON.stringify(DEFAULT_COUPONS));
        localStorage.setItem('jg_admin_activity', JSON.stringify(DEFAULT_ACTIVITY));
    }

    let state = {
        products: JSON.parse(localStorage.getItem('jg_admin_products')) || DEFAULT_PRODUCTS,
        categories: JSON.parse(localStorage.getItem('jg_admin_categories')) || DEFAULT_CATEGORIES,
        orders: JSON.parse(localStorage.getItem('jg_orders')) || DEFAULT_ORDERS,
        customers: JSON.parse(localStorage.getItem('jg_admin_customers')) || DEFAULT_CUSTOMERS,
        suppliers: JSON.parse(localStorage.getItem('jg_admin_suppliers')) || DEFAULT_SUPPLIERS,
        purchases: JSON.parse(localStorage.getItem('jg_admin_purchases')) || DEFAULT_PURCHASES,
        coupons: JSON.parse(localStorage.getItem('jg_admin_coupons')) || DEFAULT_COUPONS,
        activity: JSON.parse(localStorage.getItem('jg_admin_activity')) || DEFAULT_ACTIVITY,
        posCart: [],
        posDiscount: 0,
        posCustomerPhone: '',
        twoFactorEnabled: JSON.parse(localStorage.getItem('jg_admin_2fa')) || false
    };

    function persistState() {
        localStorage.setItem('jg_admin_products', JSON.stringify(state.products));
        localStorage.setItem('jg_admin_categories', JSON.stringify(state.categories));
        localStorage.setItem('jg_orders', JSON.stringify(state.orders));
        localStorage.setItem('jg_admin_customers', JSON.stringify(state.customers));
        localStorage.setItem('jg_admin_suppliers', JSON.stringify(state.suppliers));
        localStorage.setItem('jg_admin_purchases', JSON.stringify(state.purchases));
        localStorage.setItem('jg_admin_coupons', JSON.stringify(state.coupons));
        localStorage.setItem('jg_admin_activity', JSON.stringify(state.activity));
        localStorage.setItem('jg_admin_2fa', JSON.stringify(state.twoFactorEnabled));
    }

    function logAction(action, details) {
        state.activity.unshift({
            id: Date.now(),
            time: new Date().toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' }),
            actor: 'Admin',
            action: action,
            details: details
        });
        persistState();
    }

    // ── Router Engine ──
    function router() {
        const rawHash = window.location.hash || '#dashboard';
        const route = rawHash.split('?')[0].replace('#', '') || 'dashboard';

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

        // Route specific renderer
        if (route === 'dashboard') renderDashboard();
        else if (route === 'pos') renderPOS();
        else if (route === 'products') renderProducts();
        else if (route === 'categories') renderCategories();
        else if (route === 'orders') renderOrders();
        else if (route === 'customers') renderCustomers();
        else if (route === 'sales') renderSales();
        else if (route === 'purchases') renderPurchases();
        else if (route === 'suppliers') renderSuppliers();
        else if (route === 'coupons') renderCoupons();
        else if (route === 'activity') renderActivity();
        else if (route === 'security') renderSecurity();

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // ── Module 1: Dashboard Renderer ──
    let salesChartInstance = null;
    let orderStatusChartInstance = null;

    function renderDashboard() {
        const todayRevenue = state.orders.reduce((sum, o) => sum + (o.status !== 'Cancelled' ? o.total : 0), 0);
        const lowStockItems = state.products.filter(p => p.stock <= 5);

        document.getElementById('dashKpiRevenue').textContent = `₹${todayRevenue.toLocaleString()}`;
        document.getElementById('dashKpiOrders').textContent = state.orders.length;
        document.getElementById('dashKpiProducts').textContent = state.products.length;
        document.getElementById('dashKpiLowStock').textContent = lowStockItems.length;

        // Low stock warning banner
        const lowStockBanner = document.getElementById('dashLowStockBanner');
        if (lowStockBanner) {
            lowStockBanner.style.display = lowStockItems.length > 0 ? 'flex' : 'none';
            document.getElementById('dashLowStockCount').textContent = lowStockItems.length;
        }

        // Recent Orders Table
        const recentOrdersTbody = document.getElementById('dashRecentOrdersTbody');
        if (recentOrdersTbody) {
            recentOrdersTbody.innerHTML = state.orders.slice(0, 5).map(o => `
                <tr>
                    <td class="fw-bold text-dark">#${o.id}</td>
                    <td>${o.customer || 'Customer'}</td>
                    <td>${o.date}</td>
                    <td class="fw-bold">₹${o.total}</td>
                    <td><span class="badge ${getStatusBadgeClass(o.status)}">${o.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-success rounded-pill px-3" onclick="window.Adm.viewOrderDetail('${o.id}')">
                            View
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        // Charts Rendering with Chart.js
        if (typeof Chart !== 'undefined') {
            const ctxSales = document.getElementById('dashSalesChart');
            if (ctxSales) {
                if (salesChartInstance) salesChartInstance.destroy();
                salesChartInstance = new Chart(ctxSales, {
                    type: 'line',
                    data: {
                        labels: ['04 Sep', '05 Sep', '06 Sep', '07 Sep', '08 Sep', '09 Sep', '10 Sep'],
                        datasets: [{
                            label: 'Revenue (₹)',
                            data: [3850, 4200, 5120, 4890, 6300, 7100, todayRevenue > 0 ? todayRevenue : 8450],
                            borderColor: '#059669',
                            backgroundColor: 'rgba(5, 150, 105, 0.1)',
                            fill: true,
                            tension: 0.35,
                            borderWidth: 3,
                            pointRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: { y: { beginAtZero: false } }
                    }
                });
            }

            const ctxStatus = document.getElementById('dashOrderStatusChart');
            if (ctxStatus) {
                if (orderStatusChartInstance) orderStatusChartInstance.destroy();
                const counts = {
                    Delivered: state.orders.filter(o => o.status === 'Delivered').length,
                    Shipped: state.orders.filter(o => o.status === 'Shipped' || o.status === 'Out for Delivery').length,
                    Confirmed: state.orders.filter(o => o.status === 'Confirmed' || o.status === 'Order Placed').length,
                    Cancelled: state.orders.filter(o => o.status === 'Cancelled').length
                };
                orderStatusChartInstance = new Chart(ctxStatus, {
                    type: 'doughnut',
                    data: {
                        labels: ['Delivered', 'Shipped/Out', 'Confirmed/Placed', 'Cancelled'],
                        datasets: [{
                            data: [counts.Delivered, counts.Shipped, counts.Confirmed, counts.Cancelled],
                            backgroundColor: ['#10b981', '#0284c7', '#f59e0b', '#ef4444']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { position: 'bottom' } }
                    }
                });
            }
        }
    }

    function getStatusBadgeClass(status) {
        if (status === 'Delivered') return 'bg-success';
        if (status === 'Shipped' || status === 'Out for Delivery') return 'bg-primary';
        if (status === 'Confirmed' || status === 'Order Placed') return 'bg-warning text-dark';
        return 'bg-danger';
    }

    // ── Module 2: POS Terminal ──
    function renderPOS() {
        const grid = document.getElementById('posProductsGrid');
        if (!grid) return;

        grid.innerHTML = state.products.map(p => `
            <div class="col-6 col-md-4 col-xl-3">
                <div class="pos-product-tile" onclick="window.Adm.posAddToCart(${p.id})">
                    <img src="${p.image}" alt="${p.name}" class="pos-product-img">
                    <div class="fw-bold text-dark text-truncate small">${p.name}</div>
                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <span class="fw-bold text-success">₹${p.price}</span>
                        <span class="smallest badge ${p.stock <= 5 ? 'bg-danger' : 'bg-light text-dark border'}">
                            Qty: ${p.stock}
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
                        <div class="fw-bold text-dark small text-truncate">${p.name}</div>
                        <div class="smallest text-muted">₹${p.price} x ${item.qty}</div>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-secondary btn-sm px-2" onclick="window.Adm.posUpdateQty(${p.id}, -1)">-</button>
                            <span class="btn btn-light btn-sm fw-bold disabled text-dark" style="width: 32px;">${item.qty}</span>
                            <button class="btn btn-outline-secondary btn-sm px-2" onclick="window.Adm.posUpdateQty(${p.id}, 1)">+</button>
                        </div>
                        <div class="fw-bold text-dark small text-end" style="min-width: 50px;">₹${lineTotal}</div>
                        <button class="btn btn-link text-danger p-0 ms-1" onclick="window.Adm.posRemoveItem(${p.id})">
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

    // ── Module 3: Products / Inventory ──
    function renderProducts() {
        const tbody = document.getElementById('productsTableTbody');
        if (!tbody) return;

        tbody.innerHTML = state.products.map(p => {
            const margin = Math.round(((p.price - p.cost) / p.price) * 100);
            return `
                <tr>
                    <td class="text-muted smallest font-monospace">${p.sku}</td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <img src="${p.image}" alt="${p.name}" class="rounded" style="width: 36px; height: 36px; object-fit: contain; background:#f8fafc; border:1px solid #e2e8f0;">
                            <span class="fw-bold text-dark">${p.name}</span>
                        </div>
                    </td>
                    <td><span class="badge bg-light text-dark border">${p.category}</span></td>
                    <td>₹${p.cost}</td>
                    <td class="fw-bold text-dark">₹${p.price}</td>
                    <td><span class="badge bg-success-subtle text-success fw-bold">${margin}%</span></td>
                    <td>
                        <span class="badge ${p.stock <= 5 ? 'bg-danger' : 'bg-success'}">
                            ${p.stock} units
                        </span>
                    </td>
                    <td>
                        <div class="d-flex gap-1">
                            <button class="btn btn-sm btn-outline-primary rounded-pill px-2" title="Edit" onclick="window.Adm.openEditProductModal(${p.id})">
                                <i class="bi bi-pencil-square"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger rounded-pill px-2" title="Delete" onclick="window.Adm.deleteProduct(${p.id})">
                                <i class="bi bi-trash3"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // ── Module 4: Categories ──
    function renderCategories() {
        const grid = document.getElementById('categoriesGrid');
        if (!grid) return;

        grid.innerHTML = state.categories.map(c => {
            const prodCount = state.products.filter(p => p.category.toLowerCase() === c.name.toLowerCase()).length;
            return `
                <div class="col-md-6 col-xl-4">
                    <div class="kpi-card p-4">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <div class="fs-1">${c.icon || '📦'}</div>
                            <span class="badge bg-success text-white px-3 py-1 rounded-pill">${prodCount} Products</span>
                        </div>
                        <h4 class="fw-bold brand-font text-dark mb-1">${c.name}</h4>
                        <p class="text-muted small mb-3">${c.desc || 'Category items collection'}</p>
                        <button class="btn btn-sm btn-outline-secondary rounded-pill px-3" onclick="window.Adm.filterInventoryByCategory('${c.name}')">
                            <i class="bi bi-eye me-1"></i> View Items
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ── Module 5: Orders ──
    function renderOrders() {
        const tbody = document.getElementById('ordersTableTbody');
        if (!tbody) return;

        tbody.innerHTML = state.orders.map(o => `
            <tr>
                <td class="fw-bold text-dark">#${o.id}</td>
                <td>
                    <div class="fw-bold">${o.customer || 'Customer'}</div>
                    <div class="smallest text-muted">${o.phone || ''}</div>
                </td>
                <td class="small">${o.date}</td>
                <td class="text-center">${o.items ? o.items.length : 1} items</td>
                <td class="fw-bold text-dark">₹${o.total}</td>
                <td><span class="badge bg-light text-dark border small">${o.payment || 'UPI'}</span></td>
                <td>
                    <select class="form-select form-select-sm rounded-pill" style="width: 140px;" onchange="window.Adm.updateOrderStatus('${o.id}', this.value)">
                        <option value="Confirmed" ${o.status === 'Confirmed' || o.status === 'Order Placed' ? 'selected' : ''}>Confirmed</option>
                        <option value="Shipped" ${o.status === 'Shipped' || o.status === 'Out for Delivery' ? 'selected' : ''}>Shipped</option>
                        <option value="Delivered" ${o.status === 'Delivered' ? 'selected' : ''}>Delivered</option>
                        <option value="Cancelled" ${o.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                    </select>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-success rounded-pill px-3" onclick="window.Adm.viewOrderDetail('${o.id}')">
                        <i class="bi bi-file-text me-1"></i>Detail
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // ── Module 6: Customers ──
    function renderCustomers() {
        const tbody = document.getElementById('customersTableTbody');
        if (!tbody) return;

        tbody.innerHTML = state.customers.map((c, i) => `
            <tr>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <div class="bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center fw-bold" style="width: 32px; height: 32px; font-size: 0.8rem;">
                            ${c.name.substring(0, 2).toUpperCase()}
                        </div>
                        <span class="fw-bold text-dark">${c.name}</span>
                    </div>
                </td>
                <td>${c.email}</td>
                <td>${c.phone}</td>
                <td><span class="badge bg-light text-dark border">${c.city}</span></td>
                <td class="text-center fw-bold">${c.orders}</td>
                <td class="fw-bold text-success">₹${c.spend.toLocaleString()}</td>
            </tr>
        `).join('');
    }

    // ── Module 7: Sales ──
    function renderSales() {
        const tbody = document.getElementById('salesTableTbody');
        if (!tbody) return;

        tbody.innerHTML = state.orders.filter(o => o.status !== 'Cancelled').map(o => `
            <tr>
                <td class="fw-bold text-dark">#BILL-${o.id.replace('JG-', '')}</td>
                <td>${o.date}</td>
                <td>${o.customer || 'Walk-in Customer'}</td>
                <td><span class="badge bg-light text-dark border">${o.payment}</span></td>
                <td class="fw-bold text-dark">₹${o.total}</td>
                <td class="fw-bold text-success">₹${Math.round(o.total * 0.22)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-secondary rounded-pill px-2" onclick="window.Adm.viewOrderDetail('${o.id}')">
                        <i class="bi bi-printer me-1"></i>Invoice
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // ── Module 8: Purchases (Stock In) ──
    function renderPurchases() {
        const tbody = document.getElementById('purchasesTableTbody');
        if (!tbody) return;

        tbody.innerHTML = state.purchases.map(p => `
            <tr>
                <td class="fw-bold text-dark">#${p.id}</td>
                <td class="font-monospace text-muted small">${p.invoice}</td>
                <td class="fw-bold">${p.supplier}</td>
                <td>${p.date}</td>
                <td class="text-center">${p.itemsCount} units</td>
                <td class="fw-bold text-dark">₹${p.total.toLocaleString()}</td>
                <td><span class="badge bg-success">Received</span></td>
            </tr>
        `).join('');
    }

    // ── Module 9: Suppliers ──
    function renderSuppliers() {
        const grid = document.getElementById('suppliersGrid');
        if (!grid) return;

        grid.innerHTML = state.suppliers.map(s => `
            <div class="col-md-6 col-xl-4">
                <div class="kpi-card p-4">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge bg-light text-dark border">${s.category}</span>
                        <i class="bi bi-building text-success fs-4"></i>
                    </div>
                    <h5 class="fw-bold brand-font text-dark mb-1">${s.name}</h5>
                    <div class="small text-muted mb-2"><i class="bi bi-person me-1"></i>Contact: <strong>${s.contact}</strong></div>
                    <div class="small text-muted mb-2"><i class="bi bi-telephone me-1"></i>${s.phone}</div>
                    <div class="small text-muted mb-3"><i class="bi bi-envelope me-1"></i>${s.email}</div>
                    <button class="btn btn-sm btn-outline-success rounded-pill px-3" onclick="window.Adm.openRecordPurchaseModal('${s.name}')">
                        + Record Stock In
                    </button>
                </div>
            </div>
        `).join('');
    }

    // ── Module 10: Coupons ──
    function renderCoupons() {
        const tbody = document.getElementById('couponsTableTbody');
        if (!tbody) return;

        tbody.innerHTML = state.coupons.map(c => `
            <tr>
                <td class="fw-bold text-success font-monospace">${c.code}</td>
                <td class="fw-bold">${c.discount}</td>
                <td>₹${c.minSpend}</td>
                <td>${c.expiry}</td>
                <td class="text-center">${c.used} times</td>
                <td>
                    <span class="badge ${c.active ? 'bg-success' : 'bg-secondary'}">
                        ${c.active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-danger rounded-pill px-2" onclick="window.Adm.toggleCoupon(${c.id})">
                        ${c.active ? 'Deactivate' : 'Activate'}
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // ── Module 11: Activity Log ──
    function renderActivity() {
        const list = document.getElementById('activityLogList');
        if (!list) return;

        list.innerHTML = state.activity.map(a => `
            <div class="d-flex align-items-start gap-3 py-3 border-bottom">
                <div class="bg-success-subtle text-success p-2 rounded-circle" style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center;">
                    <i class="bi bi-clock-history"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="badge bg-dark text-white fw-bold">${a.action}</span>
                        <span class="smallest text-muted">${a.time}</span>
                    </div>
                    <div class="small text-dark mb-1">${a.details}</div>
                    <div class="smallest text-muted">Actor: <strong>${a.actor}</strong></div>
                </div>
            </div>
        `).join('');
    }

    // ── Module 12: Security & 2FA ──
    function renderSecurity() {
        const toggle = document.getElementById('security2faToggle');
        const badge = document.getElementById('security2faStatusBadge');
        if (toggle && badge) {
            toggle.checked = state.twoFactorEnabled;
            badge.className = `badge ${state.twoFactorEnabled ? 'bg-success' : 'bg-secondary'}`;
            badge.textContent = state.twoFactorEnabled ? '2FA Active & Enforced' : '2FA Disabled';
        }
    }

    // ── Public Global Adm API ──
    window.Adm = {
        posAddToCart: function (productId) {
            const p = state.products.find(prod => prod.id === productId);
            if (!p || p.stock <= 0) {
                alert('Item is currently out of stock!');
                return;
            }

            const existing = state.posCart.find(i => i.productId === productId);
            if (existing) {
                if (existing.qty < p.stock) {
                    existing.qty += 1;
                } else {
                    alert(`Cannot add more than available stock (${p.stock})!`);
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

        posCompleteSale: function () {
            if (state.posCart.length === 0) {
                alert('POS cart is empty! Select products first.');
                return;
            }

            const phone = document.getElementById('posCustomerPhoneInput').value.trim() || 'Walk-in';
            const paymentMode = document.getElementById('posPaymentModeSelect').value || 'Cash';
            const billId = `BILL-${Math.floor(100000 + Math.random() * 900000)}`;
            const dateStr = new Date().toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' });

            let subtotal = 0;
            const billedItems = state.posCart.map(c => {
                const p = state.products.find(prod => prod.id === c.productId);
                const line = p.price * c.qty;
                subtotal += line;
                // Decrement inventory stock
                p.stock = Math.max(0, p.stock - c.qty);
                return { name: p.name, qty: c.qty, price: p.price, total: line };
            });

            const tax = Math.round(subtotal * 0.05);
            const total = Math.max(0, subtotal + tax - state.posDiscount);

            // Record into master orders
            const newOrder = {
                id: billId.replace('BILL-', 'JG-'),
                customer: `Counter (${phone})`,
                phone: phone,
                date: dateStr,
                status: 'Delivered',
                total: total,
                payment: paymentMode,
                items: billedItems
            };

            state.orders.unshift(newOrder);
            logAction('POS Bill Generated', `Counter sale ${billId} for ₹${total} (${paymentMode})`);
            persistState();

            // Populate thermal bill modal
            document.getElementById('billModalNumber').textContent = billId;
            document.getElementById('billModalDate').textContent = dateStr;
            document.getElementById('billModalCustomer').textContent = phone;
            document.getElementById('billModalPayment').textContent = paymentMode;
            document.getElementById('billModalSubtotal').textContent = `₹${subtotal}`;
            document.getElementById('billModalTax').textContent = `₹${tax}`;
            document.getElementById('billModalTotal').textContent = `₹${total}`;

            const tbody = document.getElementById('billModalItemsTbody');
            tbody.innerHTML = billedItems.map((it, idx) => `
                <tr>
                    <td>${idx + 1}. ${it.name}</td>
                    <td class="text-center">${it.qty}</td>
                    <td class="text-end">₹${it.price}</td>
                    <td class="text-end fw-bold">₹${it.total}</td>
                </tr>
            `).join('');

            // Reset POS cart
            state.posCart = [];
            state.posDiscount = 0;
            renderPOS();

            // Open thermal bill modal
            const modal = new bootstrap.Modal(document.getElementById('billModal'));
            modal.show();
        },

        saveNewProduct: function (e) {
            if (e) e.preventDefault();
            const name = document.getElementById('newProdName').value.trim();
            const sku = document.getElementById('newProdSku').value.trim() || `JG-PRD-${Math.floor(100 + Math.random() * 900)}`;
            const category = document.getElementById('newProdCategory').value;
            const cost = parseFloat(document.getElementById('newProdCost').value) || 0;
            const price = parseFloat(document.getElementById('newProdPrice').value) || 0;
            const stock = parseInt(document.getElementById('newProdStock').value) || 10;
            const image = document.getElementById('newProdImg').value.trim() || 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=300&q=80';

            const newProd = {
                id: Date.now(),
                sku: sku,
                name: name,
                category: category,
                cost: cost,
                price: price,
                stock: stock,
                image: image
            };

            state.products.unshift(newProd);
            logAction('Product Added', `Added new product ${name} (${sku})`);
            persistState();
            renderProducts();

            const modalEl = document.getElementById('addProductModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            alert('Product added successfully!');
        },

        openEditProductModal: function (productId) {
            const p = state.products.find(prod => prod.id === productId);
            if (!p) return;

            document.getElementById('editProdId').value = p.id;
            document.getElementById('editProdName').value = p.name;
            document.getElementById('editProdCategory').value = p.category;
            document.getElementById('editProdCost').value = p.cost;
            document.getElementById('editProdPrice').value = p.price;
            document.getElementById('editProdStock').value = p.stock;

            const modal = new bootstrap.Modal(document.getElementById('editProductModal'));
            modal.show();
        },

        saveEditProduct: function (e) {
            if (e) e.preventDefault();
            const id = parseInt(document.getElementById('editProdId').value);
            const p = state.products.find(prod => prod.id === id);
            if (!p) return;

            p.name = document.getElementById('editProdName').value.trim();
            p.category = document.getElementById('editProdCategory').value;
            p.cost = parseFloat(document.getElementById('editProdCost').value) || p.cost;
            p.price = parseFloat(document.getElementById('editProdPrice').value) || p.price;
            p.stock = parseInt(document.getElementById('editProdStock').value) || p.stock;

            logAction('Product Edited', `Updated specifications for ${p.name}`);
            persistState();
            renderProducts();

            const modalEl = document.getElementById('editProductModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        },

        deleteProduct: function (productId) {
            const p = state.products.find(prod => prod.id === productId);
            if (!p) return;
            if (confirm(`Are you sure you want to delete "${p.name}"?`)) {
                state.products = state.products.filter(prod => prod.id !== productId);
                logAction('Product Deleted', `Removed ${p.name} (${p.sku})`);
                persistState();
                renderProducts();
            }
        },

        updateOrderStatus: function (orderId, newStatus) {
            const order = state.orders.find(o => o.id === orderId);
            if (order) {
                order.status = newStatus;
                if (newStatus === 'Delivered') order.step = 4;
                else if (newStatus === 'Shipped') order.step = 3;
                else if (newStatus === 'Confirmed') order.step = 2;

                logAction('Order Status Changed', `Order #${order.id} marked as ${newStatus}`);
                persistState();
                renderOrders();
            }
        },

        viewOrderDetail: function (orderId) {
            const order = state.orders.find(o => o.id === orderId);
            if (!order) return;

            document.getElementById('orderDetailModalId').textContent = `#${order.id}`;
            document.getElementById('orderDetailModalCustomer').textContent = order.customer || 'Customer';
            document.getElementById('orderDetailModalPhone').textContent = order.phone || '-';
            document.getElementById('orderDetailModalDate').textContent = order.date;
            document.getElementById('orderDetailModalPayment').textContent = order.payment;
            document.getElementById('orderDetailModalStatus').textContent = order.status;
            document.getElementById('orderDetailModalTotal').textContent = `₹${order.total}`;

            const tbody = document.getElementById('orderDetailModalItemsTbody');
            tbody.innerHTML = (order.items || []).map((it, i) => `
                <tr>
                    <td>${i + 1}</td>
                    <td>${it.name}</td>
                    <td class="text-center">${it.qty}</td>
                    <td class="text-end">₹${it.price}</td>
                    <td class="text-end fw-bold">₹${it.qty * it.price}</td>
                </tr>
            `).join('');

            const modal = new bootstrap.Modal(document.getElementById('orderDetailModal'));
            modal.show();
        },

        saveNewCategory: function (e) {
            if (e) e.preventDefault();
            const name = document.getElementById('newCatName').value.trim();
            const desc = document.getElementById('newCatDesc').value.trim();
            const icon = document.getElementById('newCatIcon').value.trim() || '📦';

            state.categories.push({ id: Date.now(), name: name, desc: desc, icon: icon });
            logAction('Category Added', `Created category ${name}`);
            persistState();
            renderCategories();

            const modalEl = document.getElementById('addCategoryModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        },

        openRecordPurchaseModal: function (supplierName) {
            const suppSelect = document.getElementById('purchaseSupplierSelect');
            if (suppSelect) suppSelect.value = supplierName;
            const modal = new bootstrap.Modal(document.getElementById('addPurchaseModal'));
            modal.show();
        },

        saveNewPurchase: function (e) {
            if (e) e.preventDefault();
            const supplier = document.getElementById('purchaseSupplierSelect').value;
            const prodId = parseInt(document.getElementById('purchaseProductSelect').value);
            const qty = parseInt(document.getElementById('purchaseQty').value) || 0;
            const unitCost = parseFloat(document.getElementById('purchaseUnitCost').value) || 0;
            const invoice = document.getElementById('purchaseInvoiceNum').value.trim() || `INV-${Math.floor(1000 + Math.random() * 9000)}`;

            const prod = state.products.find(p => p.id === prodId);
            if (prod) {
                prod.stock += qty;
                prod.cost = unitCost;
            }

            const totalCost = qty * unitCost;
            state.purchases.unshift({
                id: `PO-${Math.floor(1000 + Math.random() * 9000)}`,
                invoice: invoice,
                supplier: supplier,
                date: new Date().toLocaleString('en-IN', { dateStyle: 'medium' }),
                itemsCount: qty,
                total: totalCost
            });

            logAction('Stock In Recorded', `Added ${qty} units of ${prod ? prod.name : 'item'} from ${supplier}`);
            persistState();
            renderPurchases();
            renderProducts();

            const modalEl = document.getElementById('addPurchaseModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            alert(`Stock successfully incremented by ${qty} units!`);
        },

        saveNewCoupon: function (e) {
            if (e) e.preventDefault();
            const code = document.getElementById('newCouponCode').value.trim().toUpperCase();
            const discount = document.getElementById('newCouponDiscount').value.trim();
            const minSpend = parseFloat(document.getElementById('newCouponMinSpend').value) || 0;
            const expiry = document.getElementById('newCouponExpiry').value.trim() || '31 Dec 2026';

            state.coupons.unshift({
                id: Date.now(),
                code: code,
                discount: discount,
                minSpend: minSpend,
                expiry: expiry,
                used: 0,
                active: true
            });

            logAction('Coupon Created', `Created discount code ${code} (${discount})`);
            persistState();
            renderCoupons();

            const modalEl = document.getElementById('createCouponModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        },

        toggleCoupon: function (couponId) {
            const c = state.coupons.find(coup => coup.id === couponId);
            if (c) {
                c.active = !c.active;
                logAction('Coupon Toggled', `${c.code} is now ${c.active ? 'Active' : 'Inactive'}`);
                persistState();
                renderCoupons();
            }
        },

        toggle2FA: function () {
            state.twoFactorEnabled = !state.twoFactorEnabled;
            logAction('Security Setting Changed', `2FA is now ${state.twoFactorEnabled ? 'Enabled' : 'Disabled'}`);
            persistState();
            renderSecurity();
            alert(`Two-Factor Authentication is now ${state.twoFactorEnabled ? 'ACTIVATED' : 'DEACTIVATED'}!`);
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

    async function syncAdminWithServer() {
        try {
            const res = await (window.apiFetch || fetch)('/api/products?per_page=100');
            if (res.ok) {
                const data = await res.json();
                if (data.success && data.products && data.products.length > 0) {
                    state.products = data.products.map(p => ({
                        id: p.id,
                        sku: `JG-${(p.category_name || 'GEN').substring(0,3).toUpperCase()}-${String(p.id).padStart(3, '0')}`,
                        name: p.name,
                        category: p.category_name || 'General',
                        cost: parseFloat(p.cost_price || p.selling_price * 0.8),
                        price: parseFloat(p.selling_price),
                        stock: p.stock_quantity,
                        image: p.image_path || 'static/images/logo-icon.png'
                    }));
                    persistState();
                    const currentView = (window.location.hash || '#dashboard').replace('#', '');
                    if (currentView === 'dashboard') renderDashboardView();
                    else if (currentView === 'products') renderProductsView();
                    else if (currentView === 'pos') renderPOSView();
                }
            }
        } catch (e) {
            console.debug('Admin live sync deferred (running in offline/static mode):', e);
        }
    }

    // ── Lifecycle Init ──
    window.addEventListener('DOMContentLoaded', () => {
        // Authentication Guard for Admin ERP Console
        const authUser = JSON.parse(localStorage.getItem('jg_auth_user') || 'null');
        if (!authUser || authUser.role !== 'admin') {
            console.warn('Admin access required. Redirecting to storefront.');
            window.location.href = 'index.html';
            return;
        }

        // Theme check
        const savedTheme = localStorage.getItem('jg_admin_theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        }

        router();
        window.addEventListener('hashchange', router);
        syncAdminWithServer();

        // Populate product select options in modals
        const purchaseProdSelect = document.getElementById('purchaseProductSelect');
        if (purchaseProdSelect) {
            purchaseProdSelect.innerHTML = state.products.map(p => `
                <option value="${p.id}">${p.name} (Current stock: ${p.stock})</option>
            `).join('');
        }

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
