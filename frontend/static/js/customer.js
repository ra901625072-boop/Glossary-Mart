/**
 * E-GROSSARY — CONSOLIDATED CUSTOMER SUPER-APP ENGINE (customer.js)
 * Enterprise-grade e-commerce client connected directly to live backend REST APIs:
 * - Live product catalog sync from /api/products with dynamic category filtering & search
 * - Persistent server-synchronized shopping cart (/api/cart, /api/cart/add, /api/cart/sync)
 * - Real backend checkout calling /api/orders/checkout with atomic stock deduction
 * - Live customer orders history & tracking via /api/orders with PDF invoice downloads (/api/orders/<id>/invoice)
 * - Profile updates persisted to /api/auth/profile
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

    // ── Pre-Seeded Product Catalog Fallback ──
    const DEFAULT_CATALOG = [
        {
            id: 1,
            name: "Aashirvaad Superior MP Atta 5kg",
            category: "staples",
            categoryName: "Staples & Grains",
            price: 279,
            mrp: 320,
            unit: "5 kg",
            rating: 4.9,
            ratingCount: 520,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=400&q=80",
            description: "100% whole wheat grain chakki atta ground using traditional process. Makes soft, fluffy golden rotis.",
            nutrition: { calories: "360 kcal", carbs: "72g", protein: "12g", fat: "1.5g", fiber: "11g" }
        },
        {
            id: 2,
            name: "Tata Salt Vacuum Evaporated 1kg",
            category: "spices",
            categoryName: "Masala & Spices",
            price: 36,
            mrp: 40,
            unit: "1 kg",
            rating: 4.8,
            ratingCount: 940,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=400&q=80",
            description: "Desh Ka Namak — India's first packaged iodized salt with vacuum evaporation purity.",
            nutrition: { sodium: "38700mg", iodine: "15ppm" }
        },
        {
            id: 3,
            name: "Amul Taaza Fresh Toned Milk 1L",
            category: "dairy",
            categoryName: "Dairy & Breakfast",
            price: 56,
            mrp: 60,
            unit: "1 L",
            rating: 4.9,
            ratingCount: 1420,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=400&q=80",
            description: "Pasteurized homogenized toned milk with 3.0% fat and 8.5% SNF from Gujarat's own Amul dairy.",
            nutrition: { calories: "58 kcal", carbs: "4.7g", protein: "3.1g", fat: "3.0g", calcium: "120mg" }
        },
        {
            id: 4,
            name: "Maggi 2-Minute Masala Instant Noodles 280g",
            category: "snacks",
            categoryName: "Snacks & Biscuits",
            price: 42,
            mrp: 48,
            unit: "4 x 70g Pack",
            rating: 4.8,
            ratingCount: 1850,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=400&q=80",
            description: "Classic Indian favourite noodles made with quality spices and roasted herbs.",
            nutrition: { calories: "312 kcal", carbs: "45g", protein: "6.8g", fat: "12.1g" }
        },
        {
            id: 5,
            name: "Tata Tea Premium Desh Ki Chai 250g",
            category: "beverages",
            categoryName: "Beverages",
            price: 132,
            mrp: 155,
            unit: "250 g",
            rating: 4.9,
            ratingCount: 880,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=400&q=80",
            description: "A unique blend of fine tea leaves with specially crafted aroma grains for a robust kadak taste.",
            nutrition: { caffeine: "Medium", type: "Black Tea Blend" }
        },
        {
            id: 6,
            name: "Cadbury Dairy Milk Silk Chocolate 120g",
            category: "snacks",
            categoryName: "Snacks & Biscuits",
            price: 98,
            mrp: 110,
            unit: "120 g",
            rating: 4.9,
            ratingCount: 2100,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1549007994-cb92caebd54b?auto=format&fit=crop&w=400&q=80",
            description: "Creamier, smoother, and velvet-like milk chocolate made with rich cocoa butter and milk solids.",
            nutrition: { calories: "532 kcal", carbs: "58g", protein: "7.8g", fat: "30.5g" }
        }
    ];

    // ── Safe Cart Loader ──
    function loadInitialCustomerCart() {
        try {
            const raw = localStorage.getItem('egm_cart') || localStorage.getItem('jg_cart');
            const list = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(list)) return [];
            return list.map(item => {
                const id = Number(item.productId || item.id || 0);
                const qty = Number(item.qty || item.quantity || 1);
                const price = Number(item.price || 0);
                return {
                    productId: id,
                    id: id,
                    qty: isNaN(qty) || qty < 1 ? 1 : qty,
                    quantity: isNaN(qty) || qty < 1 ? 1 : qty,
                    price: isNaN(price) ? 0 : price,
                    name: item.name || '',
                    image: item.image || ''
                };
            }).filter(i => i.productId > 0);
        } catch (e) {
            return [];
        }
    }

    function loadInitialAddresses(currentUser) {
        try {
            const raw = localStorage.getItem('jg_saved_addresses');
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed) && parsed.length > 0) return parsed;
            }
        } catch (e) {}

        if (currentUser && currentUser.address && currentUser.address.trim().length >= 10) {
            const defaultAddr = {
                id: 'addr_' + Date.now(),
                tag: 'Home',
                fullName: currentUser.full_name || currentUser.name || currentUser.username || 'Customer',
                phone: currentUser.phone || '',
                fullAddress: currentUser.address.trim(),
                isDefault: true
            };
            localStorage.setItem('jg_saved_addresses', JSON.stringify([defaultAddr]));
            return [defaultAddr];
        }

        return [];
    }

    // ── Local State Initialization ──
    const initialUser = (function () {
        try {
            const u = JSON.parse(localStorage.getItem('jg_auth_user') || 'null');
            return (u && u.id && u.role === 'customer') ? u : null;
        } catch (e) {
            return null;
        }
    })();

    const initialAddresses = loadInitialAddresses(initialUser);
    const initialDef = initialAddresses.find(a => a.isDefault);

    let state = {
        products: DEFAULT_CATALOG,
        selectedCategory: 'all',
        searchQuery: '',
        sortBy: 'popularity',
        cart: loadInitialCustomerCart(),
        wishlist: JSON.parse(localStorage.getItem('jg_wishlist')) || [],
        activeCoupon: JSON.parse(localStorage.getItem('jg_coupon')) || null,
        user: initialUser,
        addresses: initialAddresses,
        selectedAddressId: initialDef ? initialDef.id : (initialAddresses.length > 0 ? initialAddresses[0].id : null),
        orders: [],
        checkoutData: {
            addressType: 'home',
            slot: 'express',
            paymentMethod: 'UPI',
            customAddress: '',
            tip: 20,
            deliveryInstructions: ['Leave at door'],
            customNote: '',
            selectedUpiApp: 'Google Pay',
            bank: 'HDFC'
        }
    };

    function persistState() {
        localStorage.setItem('jg_cart', JSON.stringify(state.cart));
        localStorage.setItem('egm_cart', JSON.stringify(state.cart));
        localStorage.setItem('jg_wishlist', JSON.stringify(state.wishlist));
        localStorage.setItem('jg_coupon', JSON.stringify(state.activeCoupon));
        localStorage.setItem('jg_saved_addresses', JSON.stringify(state.addresses));
        if (state.user && state.user.role === 'customer') {
            localStorage.setItem('jg_auth_user', JSON.stringify(state.user));
        }
        updateNavCounters();
    }

    // ── Update Badge Counters ──
    function updateNavCounters() {
        const totalCartItems = state.cart.reduce((sum, item) => sum + (Number(item.qty || item.quantity) || 1), 0);
        const wishlistCount = state.wishlist.length;

        document.querySelectorAll('.cart-counter-badge').forEach(el => {
            el.textContent = isNaN(totalCartItems) ? 0 : totalCartItems;
            el.style.display = totalCartItems > 0 ? 'inline-block' : 'none';
        });

        document.querySelectorAll('.wishlist-counter-badge').forEach(el => {
            el.textContent = wishlistCount;
            el.style.display = wishlistCount > 0 ? 'inline-block' : 'none';
        });

        const subtotal = calculateCartTotals().subtotal;
        document.querySelectorAll('.cart-total-header-pill').forEach(el => {
            el.textContent = `₹${isNaN(subtotal) ? 0 : subtotal}`;
        });
    }

    // ── Calculate Totals ──
    function calculateCartTotals() {
        let subtotal = 0;
        let originalMrpTotal = 0;

        state.cart.forEach(cartItem => {
            const numId = Number(cartItem.productId || cartItem.id || 0);
            const numQty = Number(cartItem.qty || cartItem.quantity || 1);
            const prod = state.products.find(p => Number(p.id) === numId);
            const price = prod ? Number(prod.price) : Number(cartItem.price || 0);
            const mrp = prod ? Number(prod.mrp || Math.round(price * 1.15)) : (Number(cartItem.mrp) || Math.round(price * 1.15));

            const validPrice = isNaN(price) ? 0 : price;
            const validMrp = isNaN(mrp) ? validPrice : mrp;
            const validQty = isNaN(numQty) || numQty < 1 ? 1 : numQty;

            subtotal += validPrice * validQty;
            originalMrpTotal += validMrp * validQty;
        });

        let couponDiscount = 0;
        if (state.activeCoupon) {
            if (state.activeCoupon.discount_amount !== undefined && state.activeCoupon.discount_amount !== null) {
                couponDiscount = Number(state.activeCoupon.discount_amount) || 0;
            } else if (state.activeCoupon.code === 'FRESH15' || state.activeCoupon.discountPercent) {
                const pct = Number(state.activeCoupon.discountPercent || 15);
                couponDiscount = Math.round((subtotal * pct) / 100);
            } else if (state.activeCoupon.discountFlat) {
                couponDiscount = Math.min(subtotal, Number(state.activeCoupon.discountFlat || 0));
            }
        }

        const deliveryFee = subtotal >= 499 || subtotal === 0 ? 0 : 30;
        const handlingFee = subtotal > 0 ? 5 : 0;
        const isCheckoutPage = document.body && document.body.getAttribute('data-page') === 'checkout';
        const partnerTip = (isCheckoutPage && state.checkoutData && state.checkoutData.tip !== undefined) ? Number(state.checkoutData.tip) : 0;
        const finalTotal = Math.max(0, subtotal - couponDiscount + deliveryFee + handlingFee + (subtotal > 0 ? partnerTip : 0));
        const totalSavings = Math.max(0, (originalMrpTotal - subtotal) + couponDiscount);

        return {
            subtotal: Math.round(subtotal) || 0,
            originalMrpTotal: Math.round(originalMrpTotal) || 0,
            couponDiscount: Math.round(couponDiscount) || 0,
            deliveryFee,
            handlingFee,
            partnerTip: subtotal > 0 ? partnerTip : 0,
            finalTotal: Math.round(finalTotal) || 0,
            totalSavings: Math.round(totalSavings) || 0
        };
    }

    // ── View Router Engine ──
    function router() {
        const pageAttr = document.body ? document.body.getAttribute('data-page') : null;
        const pathFile = window.location.pathname.split('/').pop().replace('.html', '').toLowerCase();
        const rawHash = window.location.hash ? window.location.hash.split('?')[0].replace('#', '') : '';
        const inCustomerDir = window.location.pathname.includes('/customer/');

        // Parse URL Search Parameters (?category=..., ?search=..., ?sort=..., ?id=...)
        const urlParams = new URLSearchParams(window.location.search);
        const catParam = urlParams.get('category');
        const searchParam = urlParams.get('search');
        const sortParam = urlParams.get('sort');

        if (catParam) {
            const raw = decodeURIComponent(catParam).toLowerCase();
            if (raw.includes('fruit') || raw.includes('veg')) state.selectedCategory = 'vegetables';
            else if (raw.includes('dairy') || raw.includes('milk') || raw.includes('breakfast')) state.selectedCategory = 'dairy';
            else if (raw.includes('atta') || raw.includes('staple') || raw.includes('grain') || raw.includes('rice')) state.selectedCategory = 'staples';
            else if (raw.includes('snack') || raw.includes('biscuit') || raw.includes('munchies') || raw.includes('chips')) state.selectedCategory = 'snacks';
            else if (raw.includes('bev') || raw.includes('tea') || raw.includes('drink') || raw.includes('juice')) state.selectedCategory = 'beverages';
            else if (raw.includes('clean') || raw.includes('house') || raw.includes('care') || raw.includes('soap')) state.selectedCategory = 'cleaning';
            else if (raw.includes('spice') || raw.includes('masala')) state.selectedCategory = 'spices';
            else state.selectedCategory = raw;

            document.querySelectorAll('.cat-pill-btn').forEach(btn => {
                btn.classList.toggle('active', btn.getAttribute('data-category') === state.selectedCategory);
            });
        }

        if (searchParam) {
            state.searchQuery = searchParam.trim();
            const inputs = document.querySelectorAll('#masterSearchInput');
            inputs.forEach(input => { input.value = state.searchQuery; });
        }

        if (sortParam) {
            state.sortBy = sortParam;
            const sortSelector = document.getElementById('sortSelector');
            if (sortSelector) sortSelector.value = sortParam;
        }

        // If user is inside /customer/ and navigates to a hash that does not exist on this page, redirect to that dedicated page
        if (rawHash && inCustomerDir && !document.getElementById(`view-${rawHash}`)) {
            const knownPages = ['shop', 'cart', 'checkout', 'payment', 'order-confirmation', 'orders', 'wishlist', 'profile', 'product', 'about', 'contact', 'faq', 'terms'];
            if (knownPages.includes(rawHash)) {
                window.location.href = `${rawHash}.html`;
                return;
            }
        }

        let route = 'shop';
        if (rawHash && document.getElementById(`view-${rawHash}`)) {
            route = rawHash;
        } else if (pageAttr) {
            route = pageAttr;
        } else if (pathFile && pathFile !== 'customer' && pathFile !== 'index') {
            route = pathFile;
        } else if (rawHash) {
            route = rawHash;
        }

        // Protected routes: require authentication before rendering
        const protectedRoutes = ['profile', 'checkout', 'orders', 'wishlist', 'payment', 'order-confirmation'];
        if (protectedRoutes.includes(route)) {
            const isAuthenticated = Boolean(state.user && state.user.id);
            if (!isAuthenticated) {
                const targetPage = `${route}.html`;
                const loginPath = inCustomerDir ? `../auth/login.html?redirect=${targetPage}` : `auth/login.html?redirect=customer/${targetPage}`;
                if (document.body) document.body.style.display = 'none';
                window.location.replace(loginPath);
                return;
            }
        }

        document.querySelectorAll('.app-view').forEach(view => {
            view.classList.remove('active-view');
        });

        const targetView = document.getElementById(`view-${route}`) || document.getElementById('view-shop');
        if (targetView) {
            targetView.classList.add('active-view');
        }

        document.querySelectorAll('[data-route-link]').forEach(link => {
            const linkRoute = link.getAttribute('data-route-link');
            if (linkRoute === route) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        if (route === 'shop') renderShopView();
        else if (route === 'product') renderProductDetailView();
        else if (route === 'cart') renderCartView();
        else if (route === 'checkout') renderCheckoutView();
        else if (route === 'orders') { loadUserOrders(); renderOrdersView(); }
        else if (route === 'wishlist') renderWishlistView();
        else if (route === 'profile') renderProfileView();
        else if (route === 'order-confirmation') renderOrderConfirmationFromStorage();
        else if (route === 'payment') renderPaymentSimulationFromStorage();

        if (document.getElementById('productDetailTitle')) {
            renderProductDetailView();
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function renderOrderConfirmationFromStorage() {
        try {
            const stored = JSON.parse(sessionStorage.getItem('egm_confirmed_order') || 'null');
            if (stored) {
                document.querySelectorAll('.confirmed-order-id-txt').forEach(el => el.textContent = `#${stored.id}`);
                document.querySelectorAll('.confirmed-order-total-txt').forEach(el => el.textContent = `₹${stored.total}`);
                document.querySelectorAll('.confirmed-order-pay-txt').forEach(el => el.textContent = stored.paymentMethod || 'COD');
                const addrEl = document.getElementById('confirmedOrderAddress');
                if (addrEl && stored.address) addrEl.textContent = stored.address;
                const invLink = document.getElementById('orderConfirmInvoiceLink');
                if (invLink) invLink.href = `invoice.html?order_id=${encodeURIComponent(stored.id)}`;
            }
        } catch (e) {}
    }

    function renderPaymentSimulationFromStorage() {
        try {
            const pending = JSON.parse(sessionStorage.getItem('egm_pending_order') || 'null');
            if (pending) {
                initPaymentSimulation(pending);
            }
        } catch (e) {}
    }

    // ── Dedicated Product Details View Renderer ──
    let currentDetailQty = 1;
    let currentDetailProduct = null;

    function renderProductDetailView() {
        if (!document.getElementById('productDetailTitle')) return;

        const urlParams = new URLSearchParams(window.location.search);
        const prodIdParam = urlParams.get('id');
        const prodId = prodIdParam ? Number(prodIdParam) : 1;

        let prod = state.products.find(p => Number(p.id) === prodId);
        if (!prod) {
            prod = state.products[0] || DEFAULT_CATALOG[0];
        }
        if (!prod) return;

        currentDetailProduct = prod;
        currentDetailQty = 1;

        // Breadcrumbs
        const bcCat = document.getElementById('breadcrumbCategory');
        if (bcCat) {
            bcCat.textContent = prod.categoryName || 'Groceries';
            bcCat.href = `shop.html?category=${prod.category || 'all'}`;
        }
        const bcName = document.getElementById('breadcrumbProductName');
        if (bcName) bcName.textContent = prod.name;

        // Product Title, Unit, Category
        const titleEl = document.getElementById('productDetailTitle');
        if (titleEl) titleEl.textContent = prod.name;

        const catTag = document.getElementById('productCategoryTag');
        if (catTag) catTag.textContent = prod.categoryName || 'General Grocery';

        const unitEl = document.getElementById('productDetailUnit');
        if (unitEl) unitEl.textContent = prod.unit || '1 unit';

        const stockTag = document.getElementById('productStockTag');
        if (stockTag) {
            if (prod.inStock) {
                stockTag.className = 'badge bg-success-subtle text-success fw-bold';
                stockTag.innerHTML = '<i class="bi bi-check2-circle me-1"></i>In Stock (15-Min Delivery)';
            } else {
                stockTag.className = 'badge bg-danger-subtle text-danger fw-bold';
                stockTag.innerHTML = '<i class="bi bi-x-circle me-1"></i>Temporarily Out of Stock';
            }
        }

        // Rating & Reviews
        const ratingEl = document.getElementById('productDetailRating');
        if (ratingEl) ratingEl.textContent = prod.rating || 4.8;
        const revEl = document.getElementById('productDetailReviews');
        if (revEl) revEl.textContent = `(${prod.ratingCount || 120} reviews)`;
        const tabRevEl = document.getElementById('tabReviewCount');
        if (tabRevEl) tabRevEl.textContent = prod.ratingCount || 120;
        const summaryRating = document.getElementById('reviewSummaryRating');
        if (summaryRating) summaryRating.textContent = prod.rating || 4.8;

        // Pricing & Savings
        const mrp = prod.mrp || Math.round(prod.price * 1.15);
        const savings = Math.max(0, mrp - prod.price);
        const discountPct = mrp > prod.price ? Math.round(((mrp - prod.price) / mrp) * 100) : 0;

        const priceEl = document.getElementById('productDetailPrice');
        if (priceEl) priceEl.textContent = `₹${prod.price}`;

        const mrpEl = document.getElementById('productDetailMrp');
        if (mrpEl) mrpEl.textContent = `₹${mrp}`;

        const savingsBadge = document.getElementById('productSavingsBadge');
        if (savingsBadge) {
            if (savings > 0) {
                savingsBadge.textContent = `Save ₹${savings} (${discountPct}% OFF)`;
                savingsBadge.style.display = 'inline-block';
            } else {
                savingsBadge.style.display = 'none';
            }
        }

        const discountPill = document.getElementById('productDiscountPill');
        if (discountPill) {
            if (discountPct > 0) {
                discountPill.textContent = `${discountPct}% OFF`;
                discountPill.style.display = 'inline-block';
            } else {
                discountPill.style.display = 'none';
            }
        }

        // Image
        const mainImg = document.getElementById('productMainImage');
        if (mainImg) {
            mainImg.src = prod.image;
            mainImg.alt = prod.name;
        }

        // Description
        const descEl = document.getElementById('productDetailDesc');
        if (descEl) descEl.textContent = prod.description || `${prod.name} — Authentic fresh grocery item sourced for eGrossary customers.`;

        // Wishlist Button state
        updateProductDetailWishlistState(prod.id);

        // Stepper count
        const qtyEl = document.getElementById('productDetailSelectedQty');
        if (qtyEl) qtyEl.textContent = currentDetailQty;

        // Nutrition Table
        if (prod.nutrition) {
            const nutTable = document.getElementById('nutritionTableBody');
            if (nutTable) {
                let nutRows = '';
                for (const [key, val] of Object.entries(prod.nutrition)) {
                    const label = key.charAt(0).toUpperCase() + key.slice(1);
                    nutRows += `<tr><td>${escapeHTML(label)}</td><td class="fw-bold text-dark">${escapeHTML(val)}</td></tr>`;
                }
                if (nutRows) nutTable.innerHTML = nutRows;
            }
        }

        // Related Products
        renderRelatedProducts(prod);

        // Load live reviews & ratings breakdown
        loadProductReviews(prod.id);

        if (window.location.hash.includes('review')) {
            const revTabBtn = document.getElementById('reviews-tab');
            if (revTabBtn && window.bootstrap) {
                try {
                    bootstrap.Tab.getOrCreateInstance(revTabBtn).show();
                } catch (e) {}
            }
        }
    }

    function updateProductDetailWishlistState(prodId) {
        const isWish = state.wishlist.includes(Number(prodId));
        const icon = document.getElementById('productWishlistIcon');
        const btn = document.getElementById('productWishlistToggleBtn');
        if (icon) {
            icon.className = isWish ? 'bi bi-heart-fill text-danger' : 'bi bi-heart';
        }
        if (btn) {
            btn.classList.toggle('btn-danger', isWish);
            btn.classList.toggle('text-white', isWish);
            btn.classList.toggle('btn-outline-danger', !isWish);
        }
    }

    function renderRelatedProducts(currentProd) {
        const container = document.getElementById('relatedProductsGrid');
        if (!container) return;

        const related = state.products
            .filter(p => Number(p.id) !== Number(currentProd.id) && (p.category === currentProd.category || !currentProd.category))
            .slice(0, 4);

        const fallbackList = related.length >= 2 ? related : state.products.filter(p => Number(p.id) !== Number(currentProd.id)).slice(0, 4);

        container.innerHTML = fallbackList.map(p => {
            const mrp = p.mrp || Math.round(p.price * 1.15);
            const discountPercent = mrp > p.price ? Math.round(((mrp - p.price) / mrp) * 100) : 0;
            const inWishlist = state.wishlist.includes(p.id);
            return `
                <div class="col-6 col-md-3">
                    <div class="product-card-customer h-100 d-flex flex-column">
                        <div class="product-thumb-wrapper">
                            ${discountPercent > 0 ? `<span class="discount-badge-pill">${discountPercent}% OFF</span>` : ''}
                            <button class="wishlist-toggle-btn ${inWishlist ? 'active' : ''}" onclick="window.JG.toggleWishlist(${Number(p.id)})">
                                <i class="bi bi-heart${inWishlist ? '-fill' : ''}"></i>
                            </button>
                            <a href="product.html?id=${p.id}">
                                <img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}" class="product-thumb-img">
                            </a>
                        </div>
                        <div class="delivery-eta-tag"><i class="bi bi-stopwatch"></i> ${escapeHTML(p.eta || '15 MINS')}</div>
                        <div class="d-flex align-items-center gap-2 mb-1 mt-1">
                            <span class="veg-icon" title="100% Vegetarian"></span>
                            <span class="product-pack-size mb-0">${escapeHTML(p.unit || '1 unit')}</span>
                        </div>
                        <a href="product.html?id=${p.id}" class="text-decoration-none">
                            <h4 class="product-title-text text-dark">${escapeHTML(p.name)}</h4>
                        </a>
                        <div class="price-box-wrap mt-auto">
                            <div>
                                <span class="curr-price">₹${p.price}</span>
                                ${mrp > p.price ? `<span class="mrp-strike ms-1">₹${mrp}</span>` : ''}
                            </div>
                            <button class="btn-add-cart-init" onclick="window.JG.addToCart(${Number(p.id)})">
                                <i class="bi bi-plus-lg me-1"></i>ADD
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Global wrappers for Product Details page
    window.adjustProductQty = function (delta) {
        currentDetailQty = Math.max(1, currentDetailQty + delta);
        const qtyEl = document.getElementById('productDetailSelectedQty');
        if (qtyEl) qtyEl.textContent = currentDetailQty;
    };

    window.handleDetailAddToCart = function () {
        if (!currentDetailProduct) return;
        window.JG.addToCart(currentDetailProduct.id, currentDetailQty);
        const btn = document.getElementById('btnAddProductBag');
        if (btn) {
            const originalHtml = btn.innerHTML;
            btn.innerHTML = '<i class="bi bi-check-lg fs-5"></i><span>Added to Bag!</span>';
            btn.classList.replace('btn-outline-success', 'btn-success');
            setTimeout(() => {
                btn.innerHTML = originalHtml;
                btn.classList.replace('btn-success', 'btn-outline-success');
            }, 1500);
        }
    };

    window.handleDetailBuyNow = function () {
        if (!currentDetailProduct) return;
        window.JG.buyNow(currentDetailProduct.id, currentDetailQty);
    };

    window.toggleCurrentProductWishlist = function () {
        if (!currentDetailProduct) return;
        window.JG.toggleWishlist(currentDetailProduct.id);
        updateProductDetailWishlistState(currentDetailProduct.id);
    };

    // ══════════════════════════════════════════════════════════════════
    // PRODUCT REVIEWS & INTERACTIVE RATING SUPER-APP ENGINE
    // ══════════════════════════════════════════════════════════════════
    let currentProductReviews = [];
    let currentReviewSummary = null;
    let currentUserProductReview = null;
    let currentSelectedStar = 5;
    let activeReviewFilter = 'all';
    let currentReviewSort = 'newest';
    let targetReviewToDelete = null;
    let selectedReviewTags = new Set();
    let isEditingReview = false;
    let editingReviewId = null;
    let myProfileReviews = [];

    function setReviewRating(val) {
        currentSelectedStar = Math.max(1, Math.min(5, Number(val) || 5));
        updateStarComposerVisuals(currentSelectedStar);
        updateStarReactionBadge(currentSelectedStar);
    }

    function updateStarComposerVisuals(rating) {
        const composer = document.getElementById('modalStarComposer');
        if (!composer) return;
        const stars = composer.querySelectorAll('.star-btn');
        stars.forEach(btn => {
            const s = Number(btn.getAttribute('data-star'));
            btn.classList.toggle('active', s <= rating);
            btn.classList.remove('hovered');
        });
    }

    function updateStarReactionBadge(rating) {
        const badge = document.getElementById('modalStarReaction');
        if (!badge) return;
        const reactions = {
            1: { text: '😞 Poor — Not satisfied', cls: 'star-reaction-1' },
            2: { text: '😐 Fair — Below expectations', cls: 'star-reaction-2' },
            3: { text: '🙂 Average — It\'s okay', cls: 'star-reaction-3' },
            4: { text: '😊 Good — Satisfied with quality', cls: 'star-reaction-4' },
            5: { text: '🤩 Excellent — Highly recommended!', cls: 'star-reaction-5' }
        };
        const r = reactions[rating] || reactions[5];
        badge.className = `star-reaction-badge ${r.cls}`;
        badge.textContent = r.text;
    }

    function initStarComposerEvents() {
        const composer = document.getElementById('modalStarComposer');
        if (!composer || composer.dataset.initialized) return;
        composer.dataset.initialized = 'true';

        const stars = composer.querySelectorAll('.star-btn');
        stars.forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                const s = Number(btn.getAttribute('data-star'));
                stars.forEach(b => {
                    const bs = Number(b.getAttribute('data-star'));
                    b.classList.toggle('hovered', bs <= s);
                });
                updateStarReactionBadge(s);
            });
        });

        composer.addEventListener('mouseleave', () => {
            stars.forEach(b => b.classList.remove('hovered'));
            updateStarComposerVisuals(currentSelectedStar);
            updateStarReactionBadge(currentSelectedStar);
        });
    }

    function toggleReviewTag(element, tagText) {
        if (selectedReviewTags.has(tagText)) {
            selectedReviewTags.delete(tagText);
            element.classList.remove('active');
        } else {
            selectedReviewTags.add(tagText);
            element.classList.add('active');
        }
    }

    async function loadProductReviews(productId) {
        const container = document.getElementById('productReviewsContainer');
        if (!container) return;

        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn(`/api/products/${productId}/reviews`);
            if (res.ok) {
                const data = await res.json();
                if (data.success) {
                    currentReviewSummary = data.summary;
                    currentUserProductReview = data.user_review;
                    currentProductReviews = data.reviews || [];

                    updateProductReviewSummaryDisplay();
                    renderReviewsList();
                    return;
                }
            }
        } catch (e) {
            console.debug('Could not load live reviews:', e);
        }

        renderReviewsList();
    }

    function updateProductReviewSummaryDisplay() {
        const s = currentReviewSummary;
        if (!s) return;

        const ratingVal = s.total_reviews > 0 ? s.average_rating.toFixed(1) : '0.0';
        const countVal = s.total_reviews || 0;

        const heroRating = document.getElementById('reviewSummaryRating');
        if (heroRating) heroRating.textContent = ratingVal;

        const heroCount = document.getElementById('reviewSummaryCount');
        if (heroCount) heroCount.textContent = countVal;

        const filterCountAll = document.getElementById('filterCountAll');
        if (filterCountAll) filterCountAll.textContent = countVal;

        const tabCount = document.getElementById('tabReviewCount');
        if (tabCount) tabCount.textContent = countVal;

        const prodDetailRating = document.getElementById('productDetailRating');
        if (prodDetailRating && s.total_reviews > 0) prodDetailRating.textContent = ratingVal;

        const prodDetailReviews = document.getElementById('productDetailReviews');
        if (prodDetailReviews && s.total_reviews > 0) prodDetailReviews.textContent = `(${countVal} reviews)`;

        const starContainer = document.getElementById('reviewSummaryStars');
        if (starContainer) {
            let starsHtml = '';
            const rounded = Math.round(s.average_rating * 2) / 2;
            for (let i = 1; i <= 5; i++) {
                if (i <= rounded) {
                    starsHtml += '<i class="bi bi-star-fill text-warning me-1"></i>';
                } else if (i - 0.5 === rounded) {
                    starsHtml += '<i class="bi bi-star-half text-warning me-1"></i>';
                } else {
                    starsHtml += '<i class="bi bi-star text-muted text-opacity-25 me-1"></i>';
                }
            }
            starContainer.innerHTML = starsHtml;
        }

        const recEl = document.getElementById('reviewRecommendPercent');
        if (recEl) recEl.textContent = `${s.recommend_percent || 100}%`;

        const total = s.total_reviews || 1;
        for (let star = 1; star <= 5; star++) {
            const count = (s.rating_breakdown && s.rating_breakdown[star]) || 0;
            const pct = s.total_reviews > 0 ? Math.round((count / total) * 100) : 0;
            const fillEl = document.getElementById(`barFill${star}`);
            const countEl = document.getElementById(`barCount${star}`);
            if (fillEl) fillEl.style.width = `${pct}%`;
            if (countEl) countEl.textContent = count;
        }

        const btnWrite = document.getElementById('btnOpenWriteReview');
        if (btnWrite) {
            if (currentUserProductReview) {
                btnWrite.className = 'btn btn-outline-success rounded-pill py-2 px-4 fw-bold w-100 shadow-sm d-flex align-items-center justify-content-center gap-2';
                btnWrite.innerHTML = '<i class="bi bi-pencil-square"></i><span>Edit Your Review</span>';
            } else {
                btnWrite.className = 'btn btn-success rounded-pill py-2 px-4 fw-bold w-100 shadow-sm d-flex align-items-center justify-content-center gap-2';
                btnWrite.innerHTML = '<i class="bi bi-pencil-square"></i><span>Write a Review</span>';
            }
        }

        renderYourReviewCard();
    }

    function renderYourReviewCard() {
        const container = document.getElementById('yourReviewContainer');
        if (!container) return;

        if (!currentUserProductReview) {
            container.style.display = 'none';
            container.innerHTML = '';
            return;
        }

        const r = currentUserProductReview;
        let starsHtml = '';
        for (let i = 1; i <= 5; i++) {
            starsHtml += `<i class="bi bi-star${i <= r.rating ? '-fill text-warning' : ' text-muted opacity-25'} me-1"></i>`;
        }

        const prodName = currentDetailProduct ? currentDetailProduct.name : 'Product';

        container.style.display = 'block';
        container.innerHTML = `
            <div class="your-review-card">
                <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
                    <div class="d-flex align-items-center gap-2">
                        <span class="your-review-badge"><i class="bi bi-star-fill"></i> Your Review</span>
                        ${r.is_verified_buyer ? '<span class="verified-buyer-badge"><i class="bi bi-patch-check-fill"></i> Verified Purchase</span>' : ''}
                    </div>
                    <div class="d-flex gap-2">
                        <button type="button" class="btn btn-sm btn-outline-success rounded-pill px-3 py-1 fw-semibold" onclick="window.JG.openReviewModal(true)">
                            <i class="bi bi-pencil me-1"></i> Edit
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-danger rounded-pill px-3 py-1 fw-semibold" onclick="window.JG.openDeleteReviewModal(${r.id}, '${escapeHTML(prodName)}')">
                            <i class="bi bi-trash3 me-1"></i> Delete
                        </button>
                    </div>
                </div>
                <div class="d-flex align-items-center gap-2 mb-2">
                    <div class="small">${starsHtml}</div>
                    <span class="smallest text-muted">• Reviewed on ${escapeHTML(r.created_at || 'Recently')}</span>
                </div>
                <p class="text-dark small mb-0" style="line-height: 1.6;">${escapeHTML(r.comment)}</p>
            </div>
        `;
    }

    function renderReviewsList() {
        const container = document.getElementById('productReviewsContainer');
        if (!container) return;

        let filtered = [...currentProductReviews];

        if (activeReviewFilter === 'verified') {
            filtered = filtered.filter(r => r.is_verified_buyer);
        } else if (activeReviewFilter !== 'all') {
            const star = Number(activeReviewFilter);
            filtered = filtered.filter(r => r.rating === star);
        }

        if (currentReviewSort === 'highest') {
            filtered.sort((a, b) => b.rating - a.rating);
        } else if (currentReviewSort === 'lowest') {
            filtered.sort((a, b) => a.rating - b.rating);
        } else {
            filtered.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
        }

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5 bg-light rounded-4 border p-4">
                    <i class="bi bi-chat-heart display-4 text-muted opacity-50 mb-3 d-block"></i>
                    <h5 class="fw-bold text-dark">No reviews found</h5>
                    <p class="text-muted small mx-auto mb-3" style="max-width: 380px;">
                        ${activeReviewFilter === 'all' 
                            ? 'Be the first verified customer to share your thoughts on this fresh grocery item!' 
                            : 'No customer reviews found matching the selected star rating filter.'}
                    </p>
                    <button type="button" class="btn btn-success rounded-pill px-4 fw-bold shadow-sm" onclick="window.JG.openReviewModal()">
                        <i class="bi bi-pencil-square me-1"></i> Write a Review
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = filtered.map(r => {
            const initial = (r.user_name || 'U').charAt(0).toUpperCase();
            let starsHtml = '';
            for (let i = 1; i <= 5; i++) {
                starsHtml += `<i class="bi bi-star${i <= r.rating ? '-fill text-warning' : ' text-muted opacity-25'}"></i>`;
            }

            const isOwner = Boolean(r.is_current_user || (state.user && r.user_id === state.user.id));
            const prodName = currentDetailProduct ? currentDetailProduct.name : 'Product';

            return `
                <div class="review-card-item" id="reviewItem-${r.id}">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="d-flex align-items-center gap-3">
                            <div class="reviewer-avatar-circle">${escapeHTML(initial)}</div>
                            <div>
                                <div class="fw-bold text-dark small d-flex align-items-center gap-2">
                                    <span>${escapeHTML(r.user_name || 'Verified Customer')}</span>
                                    ${r.is_verified_buyer ? '<span class="verified-buyer-badge"><i class="bi bi-patch-check-fill"></i> Verified Purchase</span>' : ''}
                                    ${isOwner ? '<span class="badge bg-success bg-opacity-10 text-success fw-bold border border-success-subtle">You</span>' : ''}
                                </div>
                                <div class="smallest text-muted">${escapeHTML(r.created_at || 'Verified Buyer')}</div>
                            </div>
                        </div>
                        <div class="text-warning small">${starsHtml}</div>
                    </div>
                    <p class="small text-dark mb-3" style="line-height: 1.6;">${escapeHTML(r.comment)}</p>
                    <div class="d-flex justify-content-between align-items-center pt-2 border-top">
                        <button type="button" class="btn-helpful" onclick="window.JG.voteHelpful(${r.id}, this)">
                            <i class="bi bi-hand-thumbs-up me-1"></i> Helpful
                        </button>
                        ${isOwner ? `
                            <div class="d-flex gap-2">
                                <button type="button" class="btn btn-sm btn-link text-success p-0 text-decoration-none small fw-semibold" onclick="window.JG.openReviewModal(true)">
                                    <i class="bi bi-pencil me-1"></i>Edit
                                </button>
                                <button type="button" class="btn btn-sm btn-link text-danger p-0 text-decoration-none small fw-semibold" onclick="window.JG.openDeleteReviewModal(${r.id}, '${escapeHTML(prodName)}')">
                                    <i class="bi bi-trash3 me-1"></i>Delete
                                </button>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    function openReviewModal(isEditMode = false) {
        const user = state.user || JSON.parse(localStorage.getItem('jg_auth_user') || 'null');
        if (!user || !user.id) {
            const prodId = currentDetailProduct ? currentDetailProduct.id : 1;
            const inCustomer = window.location.pathname.includes('/customer/');
            const targetLogin = inCustomer ? `../auth/login.html?redirect=customer/product.html?id=${prodId}` : `auth/login.html?redirect=customer/product.html?id=${prodId}`;
            alert('Please sign in with your customer account to rate and review products.');
            window.location.href = targetLogin;
            return;
        }

        const prod = currentDetailProduct || (state.products && state.products[0]) || DEFAULT_CATALOG[0];
        const modalImg = document.getElementById('modalProductImg');
        const modalName = document.getElementById('modalProductName');
        const alertEl = document.getElementById('modalReviewAlert');
        if (alertEl) alertEl.style.display = 'none';

        if (modalImg && prod) modalImg.src = prod.image || '../static/images/logo-icon.png';
        if (modalName && prod) modalName.textContent = prod.name || 'Grocery Item';

        initStarComposerEvents();

        selectedReviewTags.clear();
        document.querySelectorAll('.review-tag-chip').forEach(c => c.classList.remove('active'));

        const modalTitle = document.getElementById('reviewModalLabel');
        const commentInput = document.getElementById('modalReviewComment');
        const submitBtnText = document.getElementById('reviewSubmitBtnText');

        if (isEditMode && currentUserProductReview) {
            isEditingReview = true;
            editingReviewId = currentUserProductReview.id;
            if (modalTitle) modalTitle.textContent = 'Edit Your Review';
            if (submitBtnText) submitBtnText.textContent = 'Update Review';
            setReviewRating(currentUserProductReview.rating || 5);
            if (commentInput) {
                commentInput.value = currentUserProductReview.comment || '';
                handleCommentInput(commentInput);
            }
        } else {
            isEditingReview = false;
            editingReviewId = null;
            if (modalTitle) modalTitle.textContent = `Rate & Review ${prod ? prod.name : 'Product'}`;
            if (submitBtnText) submitBtnText.textContent = 'Submit Review';
            setReviewRating(5);
            if (commentInput) {
                commentInput.value = '';
                handleCommentInput(commentInput);
            }
        }

        const modalEl = document.getElementById('reviewModal');
        if (modalEl && window.bootstrap) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
        }
    }

    function handleCommentInput(el) {
        const counter = document.getElementById('modalCharCounter');
        if (counter && el) {
            counter.textContent = `${el.value.length} / 1000`;
        }
    }

    async function submitReview() {
        const commentInput = document.getElementById('modalReviewComment');
        const alertEl = document.getElementById('modalReviewAlert');
        const spinner = document.getElementById('reviewSubmitSpinner');
        const btn = document.getElementById('btnSubmitReview');

        if (!commentInput) return;
        const comment = commentInput.value.trim();

        if (comment.length < 5) {
            if (alertEl) {
                alertEl.textContent = 'Please write a review comment with at least 5 characters.';
                alertEl.style.display = 'block';
            }
            return;
        }

        const prodId = currentDetailProduct ? currentDetailProduct.id : 1;
        let fullComment = comment;
        if (selectedReviewTags.size > 0) {
            const tagsArr = Array.from(selectedReviewTags);
            fullComment += `\n[Highlights: ${tagsArr.join(', ')}]`;
        }

        if (spinner) spinner.style.display = 'inline-block';
        if (btn) btn.disabled = true;

        try {
            const fetchFn = window.apiFetch || fetch;
            let endpoint = `/api/products/${prodId}/reviews`;
            let method = 'POST';

            if (isEditingReview && editingReviewId) {
                endpoint = `/api/reviews/${editingReviewId}`;
                method = 'PUT';
            }

            const res = await fetchFn(endpoint, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    rating: currentSelectedStar,
                    comment: fullComment
                })
            });

            const data = await res.json();
            if (res.ok && data.success) {
                const modalEl = document.getElementById('reviewModal');
                if (modalEl && window.bootstrap) {
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                }

                const toastFn = window.EG?.utils?.showToast || window.showToast || alert;
                toastFn(data.message || 'Review submitted successfully!', 'success');

                await loadProductReviews(prodId);
                if (window.location.pathname.includes('profile')) {
                    loadMyReviews();
                }
            } else {
                if (alertEl) {
                    alertEl.textContent = data.message || 'Could not submit review. Please try again.';
                    alertEl.style.display = 'block';
                }
            }
        } catch (err) {
            if (alertEl) {
                alertEl.textContent = 'A network error occurred. Please try again.';
                alertEl.style.display = 'block';
            }
        } finally {
            if (spinner) spinner.style.display = 'none';
            if (btn) btn.disabled = false;
        }
    }

    function openDeleteReviewModal(reviewId, prodName) {
        targetReviewToDelete = reviewId;
        const nameEl = document.getElementById('deleteReviewProdName');
        if (nameEl) nameEl.textContent = prodName || 'this item';

        const modalEl = document.getElementById('deleteReviewModal');
        if (modalEl && window.bootstrap) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
        }
    }

    async function confirmDeleteReview() {
        if (!targetReviewToDelete) return;

        const spinner = document.getElementById('reviewDeleteSpinner');
        const btn = document.getElementById('btnConfirmDeleteReview');
        if (spinner) spinner.style.display = 'inline-block';
        if (btn) btn.disabled = true;

        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn(`/api/reviews/${targetReviewToDelete}`, {
                method: 'DELETE'
            });
            const data = await res.json();
            if (res.ok && data.success) {
                const modalEl = document.getElementById('deleteReviewModal');
                if (modalEl && window.bootstrap) {
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                }

                const toastFn = window.EG?.utils?.showToast || window.showToast || alert;
                toastFn('Your review was successfully deleted.', 'info');

                currentUserProductReview = null;
                const prodId = currentDetailProduct ? currentDetailProduct.id : 1;
                await loadProductReviews(prodId);

                if (window.location.pathname.includes('profile')) {
                    loadMyReviews();
                }
            } else {
                alert(data.message || 'Could not delete review.');
            }
        } catch (e) {
            alert('Network error while deleting review.');
        } finally {
            if (spinner) spinner.style.display = 'none';
            if (btn) btn.disabled = false;
            targetReviewToDelete = null;
        }
    }

    function filterReviewsByStar(star) {
        activeReviewFilter = String(star);
        document.querySelectorAll('.review-filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-filter') === String(star));
        });
        document.querySelectorAll('.rating-bar-row').forEach(row => {
            row.classList.remove('active-filter');
        });
        renderReviewsList();
    }

    function filterReviewsByVerified() {
        activeReviewFilter = 'verified';
        document.querySelectorAll('.review-filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-filter') === 'verified');
        });
        renderReviewsList();
    }

    function sortReviews(criterion) {
        currentReviewSort = criterion;
        renderReviewsList();
    }

    function voteHelpful(reviewId, btn) {
        if (btn.classList.contains('voted')) {
            btn.classList.remove('voted');
            btn.innerHTML = '<i class="bi bi-hand-thumbs-up me-1"></i> Helpful';
        } else {
            btn.classList.add('voted');
            btn.innerHTML = '<i class="bi bi-hand-thumbs-up-fill text-success me-1"></i> Helpful (1)';
        }
    }

    async function loadMyReviews() {
        const container = document.getElementById('profileReviewsContainer');
        if (!container) return;

        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/customer/my-reviews');
            if (res.ok) {
                const data = await res.json();
                if (data.success) {
                    myProfileReviews = data.reviews || [];
                    renderMyReviewsList(myProfileReviews);
                    return;
                }
            }
        } catch (e) {
            console.debug('Could not load my-reviews:', e);
        }

        renderMyReviewsList([]);
    }

    function renderMyReviewsList(reviews) {
        const container = document.getElementById('profileReviewsContainer');
        if (!container) return;

        if (reviews.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-star display-3 text-muted opacity-50 mb-3 d-block"></i>
                    <h5 class="fw-bold">You haven't reviewed any products yet</h5>
                    <p class="text-muted small mx-auto mb-3" style="max-width: 400px;">
                        Share your experience with fresh grocery items you have received to help the local community.
                    </p>
                    <a href="orders.html" class="btn btn-success rounded-pill px-4 fw-bold">
                        <i class="bi bi-box-seam me-1"></i> Review from Orders
                    </a>
                </div>
            `;
            return;
        }

        container.innerHTML = reviews.map(r => {
            let starsHtml = '';
            for (let i = 1; i <= 5; i++) {
                starsHtml += `<i class="bi bi-star${i <= r.rating ? '-fill text-warning' : ' text-muted opacity-25'}"></i>`;
            }

            const prodImg = r.product_image ? (window.apiUrl ? window.apiUrl(r.product_image) : r.product_image) : '../static/images/logo-icon.png';

            return `
                <div class="my-review-card d-flex flex-wrap gap-3 align-items-center justify-content-between">
                    <div class="d-flex align-items-center gap-3">
                        <img src="${escapeHTML(prodImg)}" alt="${escapeHTML(r.product_name)}" class="my-review-prod-img">
                        <div>
                            <h6 class="fw-bold text-dark mb-1">${escapeHTML(r.product_name)}</h6>
                            <div class="d-flex align-items-center gap-2 mb-1">
                                <span class="text-warning small">${starsHtml}</span>
                                <span class="smallest text-muted">• ${escapeHTML(r.created_at || 'Recently')}</span>
                            </div>
                            <p class="small text-muted mb-0" style="max-width: 500px;">${escapeHTML(r.comment)}</p>
                        </div>
                    </div>
                    <div class="d-flex flex-wrap gap-2 align-items-center">
                        <a href="product.html?id=${r.product_id}" class="btn btn-sm btn-outline-secondary rounded-pill px-3">
                            <i class="bi bi-box-arrow-up-right me-1"></i> View
                        </a>
                        <button type="button" class="btn btn-sm btn-outline-success rounded-pill px-3 fw-semibold" onclick="window.JG.openProfileEditReview(${r.id}, ${r.product_id}, '${escapeHTML(r.product_name)}', ${r.rating}, '${escapeHTML(r.comment)}')">
                            <i class="bi bi-pencil me-1"></i> Edit
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-danger rounded-pill px-3 fw-semibold" onclick="window.JG.openDeleteReviewModal(${r.id}, '${escapeHTML(r.product_name)}')">
                            <i class="bi bi-trash3 me-1"></i> Delete
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function showProfileSection(section) {
        const secSettings = document.getElementById('profileSectionSettings');
        const secReviews = document.getElementById('profileSectionReviews');
        const navItem = document.getElementById('navItemMyReviews');

        if (section === 'reviews') {
            if (secSettings) secSettings.style.display = 'none';
            if (secReviews) secReviews.style.display = 'block';
            if (navItem) navItem.classList.add('active');
            document.querySelectorAll('.profile-nav-item').forEach(el => {
                if (el !== navItem) el.classList.remove('active');
            });
            loadMyReviews();
        } else {
            if (secSettings) secSettings.style.display = 'block';
            if (secReviews) secReviews.style.display = 'none';
            if (navItem) navItem.classList.remove('active');
            document.querySelectorAll('.profile-nav-item').forEach(el => {
                if (el.getAttribute('href') === 'profile.html') el.classList.add('active');
            });
        }
    }

    // ── Shop View Renderer ──
    function renderShopView() {
        const grid = document.getElementById('productsGrid');
        if (!grid) return;

        let filtered = state.products.filter(p => {
            const matchCat = state.selectedCategory === 'all' || p.category === state.selectedCategory;
            const matchSearch = !state.searchQuery ||
                p.name.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
                (p.categoryName && p.categoryName.toLowerCase().includes(state.searchQuery.toLowerCase()));
            return matchCat && matchSearch;
        });

        if (state.sortBy === 'price-low') {
            filtered.sort((a, b) => a.price - b.price);
        } else if (state.sortBy === 'price-high') {
            filtered.sort((a, b) => b.price - a.price);
        } else if (state.sortBy === 'rating') {
            filtered.sort((a, b) => b.rating - a.rating);
        } else if (state.sortBy === 'discount') {
            filtered.sort((a, b) => (b.mrp - b.price) - (a.mrp - a.price));
        }

        const countLabel = document.getElementById('catalogCountLabel');
        if (countLabel) {
            countLabel.textContent = `Showing ${filtered.length} products`;
        }

        if (filtered.length === 0) {
            grid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="bi bi-search display-3 text-muted opacity-50 mb-3 d-block"></i>
                    <h4 class="fw-bold text-dark">No matching items found</h4>
                    <p class="text-muted small">Try searching for vegetables, milk, atta, snacks or spices.</p>
                    <button class="btn btn-outline-success rounded-pill px-4" onclick="window.JG.clearSearch()">Show All Products</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = filtered.map(product => {
            const mrpVal = product.mrp || Math.round(product.price * 1.15);
            const discountPercent = mrpVal > product.price ? Math.round(((mrpVal - product.price) / mrpVal) * 100) : 0;
            const inWishlist = state.wishlist.includes(product.id);
            const cartEntry = state.cart.find(item => item.productId === product.id);
            const qty = cartEntry ? cartEntry.qty : 0;
            const isOutOfStock = product.inStock === false;

            const actionButtonHtml = isOutOfStock ? `
                <button class="btn-add-cart-init disabled" disabled style="background:#f1f5f9; color:#94a3b8; border:1px solid #cbd5e1; cursor:not-allowed; font-size:0.75rem; padding: 4px 10px;">
                    <i class="bi bi-x-circle me-1"></i>OUT OF STOCK
                </button>
            ` : (qty === 0 ? `
                <button class="btn-add-cart-init" onclick="window.JG.addToCart(${Number(product.id)})">
                    <i class="bi bi-plus-lg me-1"></i>ADD
                </button>
            ` : `
                <div class="product-qty-stepper">
                    <button class="stepper-btn" onclick="window.JG.updateCartQty(${Number(product.id)}, -1)">-</button>
                    <span class="stepper-val">${qty}</span>
                    <button class="stepper-btn" onclick="window.JG.updateCartQty(${Number(product.id)}, 1)">+</button>
                </div>
            `);

            return `
                <div class="col-6 col-md-4 col-lg-3">
                    <div class="product-card product-card-customer">
                        <div class="product-thumb-wrapper">
                            ${isOutOfStock ? `<span class="badge bg-danger position-absolute top-0 start-0 m-2 rounded-pill px-2 py-1 small fw-bold" style="z-index: 2;">OUT OF STOCK</span>` : (discountPercent > 0 ? `<span class="discount-badge-pill">${discountPercent}% OFF</span>` : '')}
                            <button class="wishlist-toggle-btn ${inWishlist ? 'active' : ''}" 
                                    title="${inWishlist ? 'Remove from Wishlist' : 'Add to Wishlist'}"
                                    onclick="window.JG.toggleWishlist(${Number(product.id)})">
                                <i class="bi bi-heart${inWishlist ? '-fill' : ''}"></i>
                            </button>
                            <img src="${escapeHTML(product.image)}" alt="${escapeHTML(product.name)}" class="product-thumb-img" 
                                 onclick="window.JG.openProductModal(${Number(product.id)})" style="cursor:pointer;" loading="lazy"
                                 onerror="this.onerror=null; this.src='../static/images/logo-icon.png';">
                        </div>

                        <div class="delivery-eta-tag">
                            <i class="bi bi-stopwatch"></i> ${escapeHTML(product.eta || '15 MINS')}
                        </div>

                        <div class="d-flex align-items-center gap-2 mb-1">
                            <span class="veg-icon" title="100% Vegetarian"></span>
                            <span class="product-pack-size mb-0">${escapeHTML(product.unit || '1 unit')}</span>
                        </div>

                        <h3 class="product-title-text" onclick="window.JG.openProductModal(${Number(product.id)})" style="cursor:pointer;">
                            ${escapeHTML(product.name)}
                        </h3>

                        <div class="product-rating-line">
                            <span>★</span>
                            <span class="text-dark fw-bold">${Number(product.rating || 4.8)}</span>
                            <span class="text-muted">(${Number(product.ratingCount || 120)})</span>
                        </div>

                        <div class="price-box-wrap">
                            <div>
                                <span class="curr-price">₹${Number(product.price)}</span>
                                ${mrpVal > product.price ? `<span class="mrp-strike">₹${Number(mrpVal)}</span>` : ''}
                            </div>
                            <div>
                                ${actionButtonHtml}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ── Cart View Renderer ──
    function renderCartView() {
        const container = document.getElementById('cartItemsContainer');
        const emptyState = document.getElementById('cartEmptyState');
        const contentSection = document.getElementById('cartContentSection');
        if (!container) return;

        if (state.cart.length === 0) {
            if (emptyState) emptyState.style.display = 'block';
            if (contentSection) contentSection.style.display = 'none';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';
        if (contentSection) contentSection.style.display = 'flex';

        const totals = calculateCartTotals();

        // Free shipping progress bar
        const freeShippingFill = document.getElementById('freeShippingBarFill');
        const freeShippingLabel = document.getElementById('freeShippingLabel');
        if (freeShippingFill && freeShippingLabel) {
            const pct = Math.min(100, Math.round((totals.subtotal / 499) * 100));
            freeShippingFill.style.width = `${pct}%`;
            if (totals.subtotal >= 499) {
                freeShippingLabel.innerHTML = `🎉 <strong>Congratulations!</strong> You have unlocked <strong>FREE Express Delivery</strong>!`;
            } else {
                const diff = 499 - totals.subtotal;
                freeShippingLabel.innerHTML = `Add <strong>₹${diff}</strong> more to get <strong>FREE Express 15-Minute Delivery</strong>!`;
            }
        }

        // Cart items table
        container.innerHTML = state.cart.map(cartItem => {
            const prod = state.products.find(p => p.id === cartItem.productId);
            if (!prod) return '';
            const itemTotal = prod.price * cartItem.qty;

            return `
                <div class="cart-item-row">
                    <div class="d-flex align-items-center gap-3">
                        <img src="${escapeHTML(prod.image)}" alt="${escapeHTML(prod.name)}" class="cart-item-img">
                        <div>
                            <div class="fw-bold text-dark mb-1">${escapeHTML(prod.name)}</div>
                            <div class="text-muted small">${escapeHTML(prod.unit || '1 unit')} • ₹${Number(prod.price)} each</div>
                        </div>
                    </div>

                    <div class="d-flex align-items-center gap-4">
                        <div class="product-qty-stepper">
                            <button class="stepper-btn" onclick="window.JG.updateCartQty(${Number(prod.id)}, -1)">-</button>
                            <span class="stepper-val">${Number(cartItem.qty)}</span>
                            <button class="stepper-btn" onclick="window.JG.updateCartQty(${Number(prod.id)}, 1)">+</button>
                        </div>

                        <div class="fw-bold text-dark text-end" style="min-width: 65px;">
                            ₹${Number(itemTotal)}
                        </div>

                        <button class="btn btn-sm btn-link text-danger p-0" title="Remove" onclick="window.JG.removeCartItem(${Number(prod.id)})">
                            <i class="bi bi-trash3 fs-5"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Order Summary Card
        document.querySelectorAll('.cart-subtotal-val').forEach(el => el.textContent = `₹${totals.subtotal}`);
        document.querySelectorAll('.cart-delivery-val').forEach(el => el.textContent = totals.deliveryFee === 0 ? 'FREE' : `₹${totals.deliveryFee}`);
        document.querySelectorAll('.cart-handling-val').forEach(el => el.textContent = `₹${totals.handlingFee}`);
        document.querySelectorAll('.cart-total-val').forEach(el => el.textContent = `₹${totals.finalTotal}`);

        const discountRow = document.getElementById('cartDiscountRow');
        const discountVal = document.getElementById('cartDiscountVal');
        if (discountRow && discountVal) {
            if (totals.couponDiscount > 0) {
                discountRow.style.display = 'flex';
                discountVal.textContent = `-₹${totals.couponDiscount}`;
            } else {
                discountRow.style.display = 'none';
            }
        }

        const savingsBadge = document.getElementById('cartTotalSavingsBadge');
        if (savingsBadge) {
            savingsBadge.textContent = `₹${totals.totalSavings}`;
        }

        const couponChip = document.getElementById('appliedCouponChip');
        if (couponChip) {
            if (state.activeCoupon) {
                couponChip.style.display = 'inline-flex';
                couponChip.querySelector('.coupon-code-txt').textContent = state.activeCoupon.code;
            } else {
                couponChip.style.display = 'none';
            }
        }
    }

    // ── Checkout View Renderer ──
    function renderCheckoutView() {
        const totals = calculateCartTotals();

        // 1. Update Pay Totals across all buttons and summary labels
        document.querySelectorAll('.checkout-pay-total').forEach(el => el.textContent = `₹${totals.finalTotal}`);

        // 2. Render Bag Count
        const bagCountEl = document.getElementById('checkoutBagCountLabel');
        const totalItemsCount = state.cart.reduce((sum, item) => sum + (Number(item.qty || item.quantity) || 1), 0);
        if (bagCountEl) {
            bagCountEl.textContent = `${totalItemsCount} item${totalItemsCount === 1 ? '' : 's'}`;
        }

        // 3. Render Itemized Bag Items inside checkout summary preview
        const itemsContainer = document.getElementById('checkoutItemsContainer');
        if (itemsContainer) {
            if (state.cart.length === 0) {
                itemsContainer.innerHTML = `
                    <div class="text-center py-4">
                        <i class="bi bi-bag-x display-4 text-muted opacity-50 mb-2 d-block"></i>
                        <div class="small fw-bold text-dark">Your shopping bag is empty</div>
                        <a href="shop.html" class="btn btn-sm btn-outline-success rounded-pill mt-2">Go to Shop</a>
                    </div>
                `;
            } else {
                itemsContainer.innerHTML = state.cart.map(c => {
                    const numId = Number(c.productId || c.id || 0);
                    const prod = state.products.find(p => Number(p.id) === numId);
                    const name = (prod && prod.name) || c.name || 'Grocery Item';
                    const unit = (prod && prod.unit) || c.unit || '1 pack';
                    const price = prod ? Number(prod.price) : Number(c.price || 0);
                    const mrp = prod ? Number(prod.mrp || Math.round(price * 1.15)) : (Number(c.mrp) || Math.round(price * 1.15));
                    const img = (prod && prod.image) || c.image || 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=100&q=80';
                    const qty = Number(c.qty || c.quantity) || 1;
                    const itemTotal = price * qty;
                    const itemSavings = (mrp - price) * qty;

                    return `
                        <div class="checkout-item-row">
                            <img src="${img}" alt="${name}" class="checkout-item-thumb" onerror="this.src='https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=100&q=80'">
                            <div class="flex-grow-1 min-w-0">
                                <div class="fw-bold text-dark text-truncate small" title="${name}">${name}</div>
                                <div class="smallest text-muted">${unit} &bull; <span class="badge bg-light text-dark border">Qty: ${qty}</span></div>
                            </div>
                            <div class="text-end">
                                <div class="fw-bold text-dark small">₹${itemTotal}</div>
                                ${itemSavings > 0 ? `<div class="smallest text-success">Save ₹${itemSavings}</div>` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }

        // 4. Update Detailed Bill Breakdown
        const mrpEl = document.getElementById('checkoutMrpTotalVal');
        if (mrpEl) mrpEl.textContent = `₹${totals.originalMrpTotal}`;

        const prodDiscountRow = document.getElementById('checkoutDiscountRow');
        const prodDiscountVal = document.getElementById('checkoutDiscountVal');
        const prodSavings = totals.originalMrpTotal - totals.subtotal;
        if (prodDiscountRow && prodDiscountVal) {
            if (prodSavings > 0) {
                prodDiscountRow.style.display = 'flex';
                prodDiscountVal.textContent = `-₹${prodSavings}`;
            } else {
                prodDiscountRow.style.display = 'none';
            }
        }

        const couponRow = document.getElementById('checkoutCouponDiscountRow');
        const couponVal = document.getElementById('checkoutCouponDiscountVal');
        if (couponRow && couponVal) {
            if (totals.couponDiscount > 0) {
                couponRow.style.display = 'flex';
                couponVal.textContent = `-₹${totals.couponDiscount}`;
            } else {
                couponRow.style.display = 'none';
            }
        }

        const deliveryEl = document.getElementById('checkoutDeliveryVal');
        if (deliveryEl) {
            deliveryEl.textContent = totals.deliveryFee === 0 ? 'FREE' : `₹${totals.deliveryFee}`;
            deliveryEl.className = totals.deliveryFee === 0 ? 'fw-bold text-success' : 'fw-bold text-dark';
        }

        const handlingEl = document.getElementById('checkoutHandlingVal');
        if (handlingEl) handlingEl.textContent = `₹${totals.handlingFee}`;

        const tipRow = document.getElementById('checkoutTipRow');
        const tipVal = document.getElementById('checkoutTipVal');
        if (tipRow && tipVal) {
            if (totals.partnerTip > 0) {
                tipRow.style.display = 'flex';
                tipVal.textContent = `+₹${totals.partnerTip}`;
            } else {
                tipRow.style.display = 'none';
            }
        }

        // 5. Savings Banner & Badges
        const savingsBanner = document.getElementById('checkoutSavingsBanner');
        const totalSavingsBadge = document.getElementById('checkoutTotalSavingsBadge');
        const mobileSavingsBadge = document.getElementById('mobileSavingsBadge');
        if (totalSavingsBadge) totalSavingsBadge.textContent = `₹${totals.totalSavings}`;
        if (mobileSavingsBadge) mobileSavingsBadge.textContent = `Save ₹${totals.totalSavings}`;
        if (savingsBanner) {
            savingsBanner.style.display = totals.totalSavings > 0 ? 'block' : 'none';
        }

        // 6. Active Coupon Chip
        const appliedChip = document.getElementById('checkoutAppliedCouponChip');
        const couponCodeTxt = document.getElementById('checkoutCouponCodeTxt');
        if (appliedChip && couponCodeTxt) {
            if (state.activeCoupon && state.activeCoupon.code) {
                appliedChip.style.display = 'inline-flex';
                couponCodeTxt.textContent = state.activeCoupon.code;
            } else {
                appliedChip.style.display = 'none';
            }
        }

        // 7. Render Address Cards
        renderCheckoutAddresses();

        // 8. Cardholder preview default
        const activeAddr = state.addresses && state.addresses.find(a => a.id === state.selectedAddressId);
        const resolvedName = (activeAddr && activeAddr.fullName) || (state.user && (state.user.full_name || state.user.name || state.user.username)) || 'CUSTOMER';
        const cardHolderPreview = document.getElementById('cardHolderPreview');
        if (cardHolderPreview && (!cardHolderPreview.dataset.edited || cardHolderPreview.dataset.edited === 'false')) {
            cardHolderPreview.textContent = resolvedName.toUpperCase();
        }
    }

    function renderCheckoutAddresses() {
        const container = document.getElementById('checkoutAddressCardsRow');
        if (!container) return;

        if (!state.addresses || state.addresses.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="p-4 text-center border-2 border-dashed rounded-4 bg-light">
                        <i class="bi bi-geo-alt display-4 text-muted opacity-50 mb-2 d-block"></i>
                        <h6 class="fw-bold text-dark mb-1">No Delivery Address Found</h6>
                        <p class="small text-muted mb-3">Please add your delivery address so our riders can bring your order accurately.</p>
                        <button type="button" class="btn btn-success rounded-pill px-4 fw-bold shadow-sm" onclick="window.JG.openAddressModal()">
                            <i class="bi bi-plus-lg me-1"></i> Add Delivery Address
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        // Ensure a selected address exists
        if (!state.selectedAddressId || !state.addresses.some(a => a.id === state.selectedAddressId)) {
            const def = state.addresses.find(a => a.isDefault);
            state.selectedAddressId = def ? def.id : state.addresses[0].id;
        }

        container.innerHTML = state.addresses.map(addr => {
            const isSelected = addr.id === state.selectedAddressId;
            const isDef = Boolean(addr.isDefault);
            const tagIcon = addr.tag === 'Work' ? 'bi-briefcase' : (addr.tag === 'Other' ? 'bi-geo-alt' : 'bi-house-door');
            const tagColor = addr.tag === 'Work' ? 'secondary' : 'success';

            return `
                <div class="col-md-6">
                    <div class="option-select-card checkout-addr-card ${isSelected ? 'selected' : ''}" 
                         data-addr-id="${addr.id}" 
                         onclick="window.JG.selectAddress('${addr.id}')">
                        <div class="d-flex align-items-center justify-content-between mb-2">
                            <div class="d-flex align-items-center gap-1">
                                <span class="badge bg-${tagColor}-subtle text-${tagColor} fw-bold">
                                    <i class="bi ${tagIcon} me-1"></i>${(addr.tag || 'Home').toUpperCase()}
                                </span>
                                ${isDef ? `<span class="badge bg-primary-subtle text-primary fw-bold"><i class="bi bi-star-fill me-1"></i>DEFAULT</span>` : ''}
                            </div>
                            <span class="addr-check-badge"><i class="bi bi-check-circle-fill text-success fs-5"></i></span>
                        </div>
                        <div class="fw-bold text-dark mb-1">${addr.fullName || 'Customer'}</div>
                        <div class="small text-muted mb-1 address-card-text">${addr.fullAddress || ''}</div>
                        <div class="smallest text-muted"><i class="bi bi-telephone me-1"></i>${addr.phone || 'No phone'}</div>
                        
                        <!-- Address Card Quick Actions: Deliver Here, Make Default, Change, Remove -->
                        <div class="addr-actions">
                            ${!isSelected ? `
                                <button type="button" class="btn btn-xs btn-outline-success" onclick="event.stopPropagation(); window.JG.selectAddress('${addr.id}')">
                                    <i class="bi bi-check2 me-1"></i>Deliver Here
                                </button>
                            ` : `
                                <span class="badge bg-success-subtle text-success py-1 px-2 smallest fw-bold"><i class="bi bi-geo-alt-fill me-1"></i>Selected</span>
                            `}
                            ${!isDef ? `
                                <button type="button" class="btn btn-xs btn-light text-secondary border" onclick="event.stopPropagation(); window.JG.setDefaultAddress('${addr.id}')" title="Set as default delivery address">
                                    <i class="bi bi-star me-1"></i>Make Default
                                </button>
                            ` : ''}
                            <button type="button" class="btn btn-xs btn-light text-dark border" onclick="event.stopPropagation(); window.JG.openAddressModal('${addr.id}')" title="Change / Edit address">
                                <i class="bi bi-pencil me-1"></i>Change
                            </button>
                            <button type="button" class="btn btn-xs btn-light text-danger border" onclick="event.stopPropagation(); window.JG.removeAddress('${addr.id}')" title="Remove address">
                                <i class="bi bi-trash me-1"></i>Remove
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ── Orders View Renderer ──
    async function loadUserOrders() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/orders');
            if (res.status === 401) {
                state.ordersAuthRequired = true;
                state.orders = [];
                renderOrdersView();
                return;
            }
            if (res.ok) {
                state.ordersAuthRequired = false;
                const data = await res.json();
                if (data && data.orders) {
                    state.orders = data.orders.map(o => ({
                        id: o.id,
                        date: o.created_at ? new Date(o.created_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) : 'Recent',
                        status: o.order_status || 'Pending',
                        step: getOrderStep(o.order_status),
                        paymentMethod: o.payment_method || 'COD',
                        total: o.total_amount,
                        itemsCount: o.items_count || 1,
                        items: []
                    }));
                    renderOrdersView();
                }
            }
        } catch (e) {
            console.debug('Could not fetch server orders:', e);
        }
    }

    function getOrderStep(status) {
        const clean = String(status || '').toLowerCase();
        if (clean === 'cancelled' || clean === 'returned') return 0;
        if (clean === 'delivered') return 4;
        if (clean === 'shipped' || clean.includes('out for delivery') || clean === 'dispatched') return 3;
        if (clean === 'processing' || clean === 'packed') return 2;
        return 1;
    }

    function renderOrdersView() {
        const container = document.getElementById('ordersListContainer');
        if (!container) return;

        if (state.ordersAuthRequired) {
            const loginLink = window.location.pathname.includes('/customer/') ? '../auth/login.html?redirect=orders.html' : 'auth/login.html?redirect=customer/orders.html';
            container.innerHTML = `
                <div class="text-center py-5 bg-white rounded-4 shadow-sm border p-4">
                    <i class="bi bi-shield-lock display-3 text-warning opacity-75 mb-3 d-block"></i>
                    <h4 class="fw-bold">Sign in to View &amp; Track Orders</h4>
                    <p class="text-muted small mx-auto" style="max-width: 420px;">
                        Sign in with your registered customer account to track live delivery dispatches and download official GST tax invoices.
                    </p>
                    <a href="${loginLink}" class="btn btn-success rounded-pill px-4 fw-bold">
                        <i class="bi bi-box-arrow-in-right me-1"></i> Sign In to Account
                    </a>
                </div>
            `;
            return;
        }

        if (state.orders.length === 0) {
            const shopLink = window.location.pathname.includes('/customer/') ? 'shop.html' : '#shop';
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-bag-x display-3 text-muted opacity-50 mb-3 d-block"></i>
                    <h4 class="fw-bold">No orders placed yet</h4>
                    <p class="text-muted small">Your grocery journey begins now! Order fresh produce in 15 mins.</p>
                    <a href="${shopLink}" class="btn btn-success rounded-pill px-4">Start Shopping</a>
                </div>
            `;
            return;
        }

        container.innerHTML = state.orders.map(order => {
            const isDelivered = order.status === 'Delivered';
            const isCancelled = order.status === 'Cancelled';
            const isReturned = order.status === 'Returned';
            let badgeColor = 'bg-primary';
            if (isDelivered) badgeColor = 'bg-success';
            else if (isCancelled) badgeColor = 'bg-danger';
            else if (isReturned) badgeColor = 'bg-secondary';
            const invoiceUrl = window.apiUrl ? window.apiUrl(`/api/orders/${Number(order.id)}/invoice`) : `/api/orders/${Number(order.id)}/invoice`;

            const stepperHtml = (isCancelled || isReturned) ? `
                <div class="px-3 py-3 mb-3 ${isCancelled ? 'bg-danger bg-opacity-10 text-danger border border-danger-subtle' : 'bg-secondary bg-opacity-10 text-secondary border'} rounded-3 d-flex align-items-center gap-2">
                    <i class="bi ${isCancelled ? 'bi-x-circle-fill' : 'bi-arrow-counterclockwise'} fs-5"></i>
                    <div>
                        <div class="fw-bold">${isCancelled ? 'Order Cancelled' : 'Order Returned'}</div>
                        <div class="small">${isCancelled ? 'This order has been cancelled and items were returned to inventory stock.' : 'Items from this order were returned to the store.'}</div>
                    </div>
                </div>
            ` : `
                <!-- Visual Delivery Stepper -->
                <div class="px-3 py-2 mb-3 bg-light rounded-3">
                    <div class="row text-center g-2">
                        <div class="col-3">
                            <div class="fw-bold small text-${order.step >= 1 ? 'success' : 'muted'}">
                                <i class="bi bi-check-circle-fill"></i> Placed
                            </div>
                        </div>
                        <div class="col-3">
                            <div class="fw-bold small text-${order.step >= 2 ? 'success' : 'muted'}">
                                <i class="bi bi-check-circle-fill"></i> Packed
                            </div>
                        </div>
                        <div class="col-3">
                            <div class="fw-bold small text-${order.step >= 3 ? 'success' : 'muted'}">
                                <i class="bi bi-truck"></i> Out for Delivery
                            </div>
                        </div>
                        <div class="col-3">
                            <div class="fw-bold small text-${order.step >= 4 ? 'success' : 'muted'}">
                                <i class="bi bi-house-door-fill"></i> Delivered
                            </div>
                        </div>
                    </div>
                    <div class="progress mt-2" style="height: 6px;">
                        <div class="progress-bar bg-success progress-bar-striped ${!isDelivered ? 'progress-bar-animated' : ''}" 
                             style="width: ${order.step * 25}%"></div>
                    </div>
                </div>
            `;

            return `
                <div class="ss-surface-card mb-4 p-4 rounded-4 shadow-sm border">
                    <div class="d-flex flex-wrap justify-content-between align-items-center pb-3 border-bottom mb-3 gap-2">
                        <div>
                            <span class="badge ${badgeColor} me-2 px-3 py-2 rounded-pill fw-bold">${escapeHTML(order.status)}</span>
                            <span class="fw-bold text-dark fs-5">#${escapeHTML(order.id)}</span>
                            <span class="text-muted small ms-2">• ${escapeHTML(order.date)}</span>
                        </div>
                        <div class="d-flex flex-wrap gap-2">
                            ${isDelivered ? `
                                <a href="product.html?id=1#reviews" class="btn btn-sm btn-outline-warning rounded-pill px-3 fw-bold text-dark shadow-sm" title="Rate and review products from this order">
                                    <i class="bi bi-star-fill text-warning me-1"></i> Rate &amp; Review
                                </a>
                            ` : ''}
                            <a href="invoice.html?order_id=${encodeURIComponent(order.id)}" class="btn btn-sm btn-outline-success rounded-pill px-3 fw-semibold">
                                <i class="bi bi-receipt-cutoff me-1"></i> View Bill
                            </a>
                            <a href="${invoiceUrl}" target="_blank" class="btn btn-sm btn-outline-secondary rounded-pill px-3">
                                <i class="bi bi-download me-1"></i> PDF
                            </a>
                            <button class="btn btn-sm btn-success rounded-pill px-3 fw-bold" onclick="window.JG.reorder('${escapeHTML(order.id)}')">
                                <i class="bi bi-arrow-repeat me-1"></i> Reorder
                            </button>
                        </div>

                    </div>

                    ${stepperHtml}

                    <div class="row g-2 align-items-center">
                        <div class="col-md-8">
                            <div class="text-muted small mb-1">Status Overview:</div>
                            <div class="fw-semibold small text-success">
                                <i class="bi bi-shield-check me-1"></i> Real-time DB Verified Fulfillment Pipeline
                            </div>
                        </div>
                        <div class="col-md-4 text-md-end">
                            <div class="text-muted small">Total Paid via ${escapeHTML(order.paymentMethod)}</div>
                            <div class="fs-4 fw-bold text-dark">₹${escapeHTML(order.total)}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ── Wishlist View ──
    function renderWishlistView() {
        const grid = document.getElementById('wishlistGrid');
        const emptyState = document.getElementById('wishlistEmptyState');
        if (!grid) return;

        const wishlistedItems = state.products.filter(p => state.wishlist.includes(p.id));

        if (wishlistedItems.length === 0) {
            if (emptyState) emptyState.style.display = 'block';
            grid.innerHTML = '';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';

        grid.innerHTML = wishlistedItems.map(prod => `
            <div class="col-6 col-md-4 col-lg-3">
                <div class="product-card-customer">
                    <div class="product-thumb-wrapper">
                        <button class="wishlist-toggle-btn active" title="Remove" onclick="window.JG.toggleWishlist(${Number(prod.id)})">
                            <i class="bi bi-trash3 text-danger"></i>
                        </button>
                        <img src="${escapeHTML(prod.image)}" alt="${escapeHTML(prod.name)}" class="product-thumb-img">
                    </div>
                    <div class="delivery-eta-tag"><i class="bi bi-stopwatch"></i> ${escapeHTML(prod.eta || '15 MINS')}</div>
                    <div class="d-flex align-items-center gap-2 mb-1 mt-1">
                        <span class="veg-icon" title="100% Vegetarian"></span>
                        <span class="product-pack-size mb-0">${escapeHTML(prod.unit || '1 unit')}</span>
                    </div>
                    <h3 class="product-title-text">${escapeHTML(prod.name)}</h3>
                    <div class="price-box-wrap">
                        <div class="curr-price">₹${Number(prod.price)}</div>
                        <button class="btn btn-sm btn-success rounded-pill px-3" onclick="window.JG.addToCart(${Number(prod.id)}); window.JG.toggleWishlist(${Number(prod.id)});">
                            <i class="bi bi-bag-plus me-1"></i> Move to Bag
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // ── Profile View ──
    function renderProfileView() {
        const nameInput = document.getElementById('profileFullName');
        const emailInput = document.getElementById('profileEmail');
        const phoneInput = document.getElementById('profilePhone');
        const addressInput = document.getElementById('profileAddress');

        const user = state.user || {};
        if (nameInput) nameInput.value = user.full_name || user.name || '';
        if (emailInput) emailInput.value = user.email || '';
        if (phoneInput) phoneInput.value = user.phone || '';
        if (addressInput) addressInput.value = user.address || '';

        document.querySelectorAll('.profile-user-name-display').forEach(el => el.textContent = user.full_name || user.username || 'Customer Profile');
        document.querySelectorAll('.profile-user-email-display').forEach(el => el.textContent = user.email || 'Sign in to sync your orders across devices');

        const initials = ((user.full_name || user.name || user.username || 'EG')
            .trim()
            .split(/\s+/)
            .map(w => w[0].toUpperCase())
            .slice(0, 2)
            .join('')) || 'EG';
        document.querySelectorAll('.profile-avatar-circle').forEach(el => el.textContent = initials);

        const walletEl = document.getElementById('profileWalletBalance');
        if (walletEl) {
            walletEl.textContent = `₹${user.wallet_balance !== undefined ? user.wallet_balance : 250}`;
        }

        if (window.location.hash.includes('review')) {
            showProfileSection('reviews');
        } else {
            showProfileSection('settings');
        }
    }


    window.handleCartCheckoutProceed = function (e) {
        if (e) e.preventDefault();
        const count = state.cart.reduce((sum, item) => sum + (Number(item.qty || item.quantity) || 1), 0);
        if (count === 0) {
            alert('Your shopping bag is empty. Please add items before checking out.');
            return false;
        }
        const user = JSON.parse(localStorage.getItem('jg_auth_user') || 'null');
        if (!user || !user.id || user.role !== 'customer') {
            window.location.href = '../auth/login.html?redirect=checkout.html';
            return false;
        }
        window.location.href = 'checkout.html';
        return false;
    };

    // ── Public Global JG API ──
    window.JG = {
        filterCategory: function (cat) {
            state.selectedCategory = cat;
            document.querySelectorAll('.cat-pill-btn').forEach(btn => {
                btn.classList.toggle('active', btn.getAttribute('data-category') === cat);
            });
            renderShopView();
        },

        handleSearchInput: function (val) {
            state.searchQuery = (val || '').trim();
            const clearBtn = document.getElementById('masterSearchClear');
            if (clearBtn) clearBtn.style.display = state.searchQuery ? 'flex' : 'none';

            if (document.getElementById('productsGrid')) {
                renderShopView();
            } else {
                renderSearchSuggestionsDropdown(state.searchQuery);
            }
        },

        clearSearch: function () {
            state.searchQuery = '';
            const inputs = document.querySelectorAll('#masterSearchInput');
            inputs.forEach(i => { i.value = ''; });
            const clearBtn = document.getElementById('masterSearchClear');
            if (clearBtn) clearBtn.style.display = 'none';
            const drop = document.getElementById('searchDropdown');
            if (drop) drop.style.display = 'none';
            if (document.getElementById('productsGrid')) renderShopView();
        },

        handleSortChange: function (val) {
            state.sortBy = val;
            renderShopView();
        },

        // ── Real-World Product Review & Rating System APIs ──
        openReviewModal: function (isEditMode) {
            openReviewModal(Boolean(isEditMode));
        },
        setReviewRating: function (val) {
            setReviewRating(val);
        },
        toggleReviewTag: function (el, tag) {
            toggleReviewTag(el, tag);
        },
        handleCommentInput: function (el) {
            handleCommentInput(el);
        },
        submitReview: function () {
            submitReview();
        },
        openDeleteReviewModal: function (reviewId, prodName) {
            openDeleteReviewModal(reviewId, prodName);
        },
        confirmDeleteReview: function () {
            confirmDeleteReview();
        },
        filterReviewsByStar: function (star) {
            filterReviewsByStar(star);
        },
        filterReviewsByVerified: function () {
            filterReviewsByVerified();
        },
        sortReviews: function (criterion) {
            sortReviews(criterion);
        },
        voteHelpful: function (reviewId, btn) {
            voteHelpful(reviewId, btn);
        },
        showProfileSection: function (section) {
            showProfileSection(section);
        },
        openProfileEditReview: function (reviewId, prodId, prodName, rating, comment) {
            currentUserProductReview = { id: reviewId, rating: rating, comment: comment };
            currentDetailProduct = { id: prodId, name: prodName };
            openReviewModal(true);
        },
        promptOrderReview: function (orderId) {
            const inCustomer = window.location.pathname.includes('/customer/');
            window.location.href = inCustomer ? 'product.html?id=1#reviews' : 'customer/product.html?id=1#reviews';
        },


        addToCart: async function (productId, quantityToAdd = 1) {
            const addQty = Math.max(1, Number(quantityToAdd) || 1);
            const numId = Number(productId);
            const prod = state.products.find(p => Number(p.id) === numId);
            if (prod && prod.inStock === false) {
                alert(`Sorry, "${prod.name}" is currently out of stock.`);
                return;
            }
            const existing = state.cart.find(i => Number(i.productId || i.id) === numId);
            if (existing) {
                existing.qty = (Number(existing.qty) || 0) + addQty;
                existing.quantity = existing.qty;
            } else {
                state.cart.push({ productId: numId, id: numId, qty: addQty, quantity: addQty });
            }
            persistState();
            renderShopView();
            if (window.location.hash === '#cart' || document.getElementById('cartItemsContainer') || document.getElementById('cartItemsList')) {
                renderCartView();
            }

            // Fire reactive event for UI components (like cart drawer)
            window.dispatchEvent(new CustomEvent('cart:updated', { detail: { cart: state.cart } }));

            // Fire-and-forget sync to backend
            try {
                const fetchFn = window.apiFetch || fetch;
                fetchFn('/api/cart/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ product_id: numId, quantity: addQty })
                });
            } catch (e) {}
        },

        updateCartQty: function (productId, delta) {
            const itemIndex = state.cart.findIndex(i => i.productId === productId);
            if (itemIndex > -1) {
                state.cart[itemIndex].qty += delta;
                if (state.cart[itemIndex].qty <= 0) {
                    state.cart.splice(itemIndex, 1);
                }
            }
            persistState();
            renderShopView();
            if (window.location.hash === '#cart' || document.getElementById('cartItemsList')) renderCartView();
        },

        removeCartItem: function (productId) {
            state.cart = state.cart.filter(i => i.productId !== productId);
            persistState();
            renderCartView();
            renderShopView();
        },

        toggleWishlist: function (productId) {
            const idx = state.wishlist.indexOf(productId);
            if (idx > -1) {
                state.wishlist.splice(idx, 1);
            } else {
                state.wishlist.push(productId);
            }
            persistState();
            renderShopView();
            if (window.location.hash === '#wishlist' || document.getElementById('wishlistGrid')) renderWishlistView();
        },

        applyCoupon: async function () {
            const input = document.getElementById('couponCodeInput');
            const code = input ? input.value.trim().toUpperCase() : '';
            const feedback = document.getElementById('couponFeedbackMsg');

            if (!code) {
                if (feedback) {
                    feedback.className = 'text-danger small mt-2 fw-bold';
                    feedback.textContent = 'Please enter a coupon code.';
                }
                return;
            }

            const currentSubtotal = calculateCartTotals().subtotal;

            try {
                const fetchFn = window.apiFetch || fetch;
                const res = await fetchFn('/api/coupons/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code, cart_total: currentSubtotal })
                });
                const data = await res.json().catch(() => ({}));

                if (res.ok && data.success && data.coupon) {
                    const c = data.coupon;
                    state.activeCoupon = {
                        code: c.code,
                        discount_type: c.discount_type,
                        value: c.value,
                        discount_amount: c.discount_amount,
                        discountPercent: c.discount_type === 'percentage' ? c.value : null,
                        discountFlat: c.discount_type !== 'percentage' ? c.value : null
                    };
                    persistState();
                    renderCartView();
                    if (feedback) {
                        feedback.className = 'text-success small mt-2 fw-bold';
                        feedback.textContent = `Coupon ${c.code} applied! Saved ₹${c.discount_amount}.`;
                    }
                } else {
                    state.activeCoupon = null;
                    persistState();
                    renderCartView();
                    if (feedback) {
                        feedback.className = 'text-danger small mt-2 fw-bold';
                        feedback.textContent = data.message || 'Invalid coupon code.';
                    }
                }
            } catch (err) {
                // Offline fallback
                if (code === 'SAVE10' || code === 'FRESH15') {
                    state.activeCoupon = { code: code, discountPercent: 10, discount_amount: Math.round(currentSubtotal * 0.1) };
                    persistState();
                    renderCartView();
                    if (feedback) {
                        feedback.className = 'text-success small mt-2 fw-bold';
                        feedback.textContent = '10% discount applied!';
                    }
                } else {
                    if (feedback) {
                        feedback.className = 'text-danger small mt-2 fw-bold';
                        feedback.textContent = 'Unable to validate coupon. Please try again.';
                    }
                }
            }
        },

        removeCoupon: function () {
            state.activeCoupon = null;
            persistState();
            renderCartView();
        },

        selectAddress: function (addrId) {
            state.selectedAddressId = addrId;
            renderCheckoutAddresses();
            renderCheckoutView();
        },

        setDefaultAddress: function (addrId) {
            state.addresses.forEach(a => {
                a.isDefault = (a.id === addrId);
            });
            state.selectedAddressId = addrId;
            const chosen = state.addresses.find(a => a.id === addrId);
            if (chosen && state.user) {
                state.user.address = chosen.fullAddress;
                if (chosen.phone) state.user.phone = chosen.phone;
                if (chosen.fullName) state.user.full_name = chosen.fullName;
            }
            persistState();

            // Background sync with profile
            if (chosen) {
                try {
                    const fetchFn = window.apiFetch || fetch;
                    fetchFn('/api/auth/profile', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            full_name: chosen.fullName,
                            phone: chosen.phone,
                            address: chosen.fullAddress
                        })
                    }).catch(() => {});
                } catch (e) {}
            }

            renderCheckoutAddresses();
            renderCheckoutView();
        },

        removeAddress: function (addrId) {
            const target = state.addresses.find(a => a.id === addrId);
            const name = target ? (target.tag || 'this') : 'this';
            if (!confirm(`Are you sure you want to remove ${name} delivery address?`)) {
                return;
            }

            state.addresses = state.addresses.filter(a => a.id !== addrId);

            if (state.selectedAddressId === addrId) {
                const def = state.addresses.find(a => a.isDefault);
                state.selectedAddressId = def ? def.id : (state.addresses.length > 0 ? state.addresses[0].id : null);
            }

            // If removed was default and there are other addresses, make the first one default
            if (target && target.isDefault && state.addresses.length > 0) {
                state.addresses[0].isDefault = true;
                if (state.user) {
                    state.user.address = state.addresses[0].fullAddress;
                    if (state.addresses[0].phone) state.user.phone = state.addresses[0].phone;
                    if (state.addresses[0].fullName) state.user.full_name = state.addresses[0].fullName;
                }
                try {
                    const fetchFn = window.apiFetch || fetch;
                    fetchFn('/api/auth/profile', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            full_name: state.addresses[0].fullName,
                            phone: state.addresses[0].phone,
                            address: state.addresses[0].fullAddress
                        })
                    }).catch(() => {});
                } catch (e) {}
            } else if (state.addresses.length === 0) {
                if (state.user) state.user.address = '';
                try {
                    const fetchFn = window.apiFetch || fetch;
                    fetchFn('/api/auth/profile', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ address: '' })
                    }).catch(() => {});
                } catch (e) {}
            }

            persistState();
            renderCheckoutAddresses();
            renderCheckoutView();
        },

        selectCheckoutAddress: function (type) {
            const match = state.addresses.find(a => (a.tag || '').toLowerCase() === type.toLowerCase());
            if (match) {
                window.JG.selectAddress(match.id);
            }
        },

        openAddressModal: function (addrId) {
            const modalEl = document.getElementById('checkoutAddressModal');
            if (!modalEl) return;

            const titleEl = document.getElementById('addrModalTitleText');
            const editIdInput = document.getElementById('addrEditingId');
            const nameInput = document.getElementById('addrFullName');
            const phoneInput = document.getElementById('addrPhone');
            const flatInput = document.getElementById('addrFlat');
            const streetInput = document.getElementById('addrStreet');
            const landmarkInput = document.getElementById('addrLandmark');
            const cityInput = document.getElementById('addrCity');
            const pincodeInput = document.getElementById('addrPincode');
            const defCheck = document.getElementById('addrSetDefault');

            if (addrId) {
                // Change / Edit existing address
                const addr = state.addresses.find(a => a.id === addrId);
                if (addr) {
                    if (titleEl) titleEl.textContent = 'Change / Edit Delivery Address';
                    if (editIdInput) editIdInput.value = addr.id;
                    if (nameInput) nameInput.value = addr.fullName || '';
                    if (phoneInput) phoneInput.value = (addr.phone || '').replace('+91', '').trim();
                    if (flatInput) flatInput.value = addr.flat || '';
                    if (streetInput) streetInput.value = addr.street || '';
                    if (landmarkInput) landmarkInput.value = addr.landmark || '';
                    if (cityInput) cityInput.value = addr.city || 'Pali';
                    if (pincodeInput) pincodeInput.value = addr.pincode || '306401';
                    if (defCheck) defCheck.checked = Boolean(addr.isDefault);

                    const tag = addr.tag || 'Home';
                    const radio = document.getElementById(`tag${tag}`);
                    if (radio) radio.checked = true;
                }
            } else {
                // Add new address
                if (titleEl) titleEl.textContent = 'Add New Delivery Address';
                if (editIdInput) editIdInput.value = '';
                if (nameInput) nameInput.value = (state.user && (state.user.full_name || state.user.name || state.user.username)) || '';
                if (phoneInput) phoneInput.value = (state.user && state.user.phone ? state.user.phone.replace('+91', '').trim() : '');
                if (flatInput) flatInput.value = '';
                if (streetInput) streetInput.value = '';
                if (landmarkInput) landmarkInput.value = '';
                if (cityInput) cityInput.value = 'Pali';
                if (pincodeInput) pincodeInput.value = '306401';
                if (defCheck) defCheck.checked = (state.addresses.length === 0);

                const homeRadio = document.getElementById('tagHome');
                if (homeRadio) homeRadio.checked = true;
            }

            if (window.bootstrap && bootstrap.Modal) {
                bootstrap.Modal.getOrCreateInstance(modalEl).show();
            }
        },

        saveCustomAddress: function (e) {
            if (e) e.preventDefault();
            const editingId = (document.getElementById('addrEditingId')?.value || '').trim();
            const fullName = (document.getElementById('addrFullName')?.value || '').trim();
            const phone = (document.getElementById('addrPhone')?.value || '').trim();
            const flat = (document.getElementById('addrFlat')?.value || '').trim();
            const street = (document.getElementById('addrStreet')?.value || '').trim();
            const landmark = (document.getElementById('addrLandmark')?.value || '').trim();
            const city = (document.getElementById('addrCity')?.value || 'Pali').trim();
            const pincode = (document.getElementById('addrPincode')?.value || '306401').trim();
            const isDefault = Boolean(document.getElementById('addrSetDefault')?.checked) || state.addresses.length === 0;

            const selectedTagRadio = document.querySelector('input[name="addrTagRadio"]:checked');
            const tag = selectedTagRadio ? selectedTagRadio.value : 'Home';

            const fullAddr = [flat, street, landmark ? 'Near ' + landmark : '', `${city}, Rajasthan - ${pincode}`].filter(Boolean).join(', ');
            const formattedPhone = phone.startsWith('+91') ? phone : `+91 ${phone}`;

            let activeId = editingId;
            if (editingId) {
                // Update existing
                const existing = state.addresses.find(a => a.id === editingId);
                if (existing) {
                    existing.tag = tag;
                    existing.fullName = fullName;
                    existing.phone = formattedPhone;
                    existing.flat = flat;
                    existing.street = street;
                    existing.landmark = landmark;
                    existing.city = city;
                    existing.pincode = pincode;
                    existing.fullAddress = fullAddr;
                    if (isDefault) existing.isDefault = true;
                }
                activeId = editingId;
            } else {
                // Add new address
                const newId = 'addr_' + Date.now();
                const newObj = {
                    id: newId,
                    tag: tag,
                    fullName: fullName,
                    phone: formattedPhone,
                    flat: flat,
                    street: street,
                    landmark: landmark,
                    city: city,
                    pincode: pincode,
                    fullAddress: fullAddr,
                    isDefault: isDefault
                };
                state.addresses.push(newObj);
                activeId = newId;
            }

            state.selectedAddressId = activeId;

            if (isDefault) {
                state.addresses.forEach(a => {
                    if (a.id !== activeId) a.isDefault = false;
                });
                if (!state.user) state.user = {};
                state.user.address = fullAddr;
                state.user.phone = formattedPhone;
                if (fullName) state.user.full_name = fullName;
            }

            persistState();

            // Background profile sync
            if (isDefault) {
                try {
                    const fetchFn = window.apiFetch || fetch;
                    fetchFn('/api/auth/profile', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            full_name: fullName,
                            phone: formattedPhone,
                            address: fullAddr
                        })
                    }).catch(() => {});
                } catch (err) {}
            }

            // Dismiss modal
            const modalEl = document.getElementById('checkoutAddressModal');
            if (modalEl && window.bootstrap && bootstrap.Modal) {
                const inst = bootstrap.Modal.getInstance(modalEl);
                if (inst) inst.hide();
            }

            renderCheckoutAddresses();
            renderCheckoutView();
        },

        toggleInstruction: function (el, text) {
            el.classList.toggle('active');
            if (!state.checkoutData.deliveryInstructions) {
                state.checkoutData.deliveryInstructions = [];
            }
            const idx = state.checkoutData.deliveryInstructions.indexOf(text);
            if (el.classList.contains('active')) {
                if (idx === -1) state.checkoutData.deliveryInstructions.push(text);
            } else {
                if (idx !== -1) state.checkoutData.deliveryInstructions.splice(idx, 1);
            }
        },

        selectCheckoutSlot: function (slot) {
            state.checkoutData.slot = slot;
            document.querySelectorAll('.checkout-slot-card').forEach(c => {
                c.classList.toggle('selected', c.getAttribute('data-slot') === slot);
            });
        },

        switchPaymentTab: function (method) {
            state.checkoutData.paymentMethod = method;
            document.querySelectorAll('.payment-tab-btn').forEach(b => {
                const target = b.getAttribute('data-target');
                const isTarget = target === `panel-${method.toLowerCase()}`;
                b.classList.toggle('active', isTarget);
            });
            document.querySelectorAll('.payment-panel').forEach(p => {
                p.classList.toggle('active', p.id === `panel-${method.toLowerCase()}`);
            });
        },

        selectUpiApp: function (appName) {
            state.checkoutData.selectedUpiApp = appName;
            document.querySelectorAll('.upi-app-btn').forEach(btn => {
                btn.classList.toggle('selected', btn.textContent.includes(appName) || btn.innerText.includes(appName));
            });
        },

        verifyUpiVpa: function () {
            const input = document.getElementById('upiVpaInput');
            const feedback = document.getElementById('upiVpaFeedback');
            const val = input ? input.value.trim() : '';
            if (val.includes('@') && val.length >= 6) {
                state.checkoutData.upiVpa = val;
                if (feedback) {
                    feedback.innerHTML = `<span class="text-success fw-bold"><i class="bi bi-check-circle-fill me-1"></i> Verified & Active: ${val} (Linked to Jay Goga Escrow)</span>`;
                }
            } else {
                if (feedback) {
                    feedback.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-exclamation-triangle-fill me-1"></i> Please enter a valid UPI VPA (e.g. mobile@okhdfcbank)</span>`;
                }
            }
        },

        appendUpiHandle: function (handle) {
            const input = document.getElementById('upiVpaInput');
            if (input) {
                let current = input.value.trim();
                if (current.includes('@')) current = current.split('@')[0];
                if (!current) current = (state.user && state.user.phone ? state.user.phone.replace(/\D/g, '') : '9876543210');
                input.value = current + handle;
                input.focus();
                window.JG.verifyUpiVpa();
            }
        },

        toggleUpiQr: function (show) {
            const qrBox = document.getElementById('desktopQrBox');
            if (qrBox) qrBox.style.display = show ? 'block' : 'none';
        },

        handleCardNumberInput: function (input) {
            let val = input.value.replace(/\D/g, '').substring(0, 16);
            input.value = val.replace(/(\d{4})(?=\d)/g, '$1 ');

            const preview = document.getElementById('cardNumberPreview');
            if (preview) {
                if (val.length === 0) {
                    preview.textContent = '•••• •••• •••• 4242';
                } else {
                    const formatted = val.padEnd(16, '•').replace(/(.{4})/g, '$1 ').trim();
                    preview.textContent = formatted;
                }
            }

            // Brand Detection
            const brandPreview = document.getElementById('cardBrandPreview');
            const brandIcon = document.getElementById('cardBrandIcon');
            let brand = 'CARD';
            if (/^4/.test(val)) brand = 'VISA';
            else if (/^(5[1-5]|2[2-7])/.test(val)) brand = 'MASTERCARD';
            else if (/^(60|65|81|82|508)/.test(val)) brand = 'RUPAY';
            else if (/^3[47]/.test(val)) brand = 'AMEX';

            if (brandPreview) brandPreview.textContent = brand;
            if (brandIcon) {
                brandIcon.innerHTML = `<span class="badge bg-success-subtle text-success fw-bold">${brand}</span>`;
            }
        },

        handleCardNameInput: function (input) {
            const preview = document.getElementById('cardHolderPreview');
            if (preview) {
                preview.textContent = input.value.trim().toUpperCase() || 'REGISTERED CUSTOMER';
                preview.dataset.edited = 'true';
            }
        },

        handleCardExpiryInput: function (input) {
            let val = input.value.replace(/\D/g, '').substring(0, 4);
            if (val.length >= 3) {
                input.value = val.substring(0, 2) + '/' + val.substring(2);
            } else {
                input.value = val;
            }
            const preview = document.getElementById('cardExpiryPreview');
            if (preview) {
                preview.textContent = input.value || '12/28';
            }
        },

        selectBank: function (bankCode) {
            state.checkoutData.bank = bankCode;
            document.querySelectorAll('.bank-pill').forEach(pill => {
                pill.classList.toggle('selected', pill.textContent.includes(bankCode));
            });
            const sel = document.getElementById('allBanksSelector');
            if (sel) {
                const hasOption = Array.from(sel.options).some(o => o.value === bankCode);
                if (hasOption) sel.value = bankCode;
            }
        },

        selectTip: function (amount, btn) {
            state.checkoutData.tip = Number(amount);
            document.querySelectorAll('.tip-pill').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');
            renderCheckoutView();
        },

        applyCheckoutCoupon: function () {
            const input = document.getElementById('checkoutCouponInput');
            const code = input ? input.value.trim().toUpperCase() : '';
            const feedback = document.getElementById('checkoutCouponFeedback');
            if (!code) return;

            if (code === 'FRESH15' || code === 'SAVE10') {
                state.activeCoupon = { code: code, discountPercent: code === 'FRESH15' ? 15 : 10 };
                persistState();
                renderCheckoutView();
                if (feedback) {
                    feedback.className = 'text-success smallest mt-1 fw-bold';
                    feedback.textContent = `🎉 Coupon ${code} applied successfully!`;
                }
            } else if (code === 'JAYGOGA100') {
                state.activeCoupon = { code: code, discountFlat: 100 };
                persistState();
                renderCheckoutView();
                if (feedback) {
                    feedback.className = 'text-success smallest mt-1 fw-bold';
                    feedback.textContent = `🎉 Flat ₹100 Discount Applied!`;
                }
            } else {
                if (feedback) {
                    feedback.className = 'text-danger smallest mt-1 fw-bold';
                    feedback.textContent = `Invalid coupon code. Try FRESH15 or JAYGOGA100.`;
                }
            }
        },

        removeCheckoutCoupon: function () {
            state.activeCoupon = null;
            const input = document.getElementById('checkoutCouponInput');
            if (input) input.value = '';
            const feedback = document.getElementById('checkoutCouponFeedback');
            if (feedback) feedback.textContent = '';
            persistState();
            renderCheckoutView();
        },

        fillCoupon: function (code) {
            const input = document.getElementById('checkoutCouponInput');
            if (input) {
                input.value = code;
                window.JG.applyCheckoutCoupon();
            }
        },

        // Real-World Backend Checkout
        processCheckout: async function () {
            if (state.cart.length === 0) {
                alert('Your shopping bag is empty! Add items from the shop first.');
                return;
            }

            // Verify if user is logged in
            if (!state.user || !state.user.id) {
                alert('Please sign in or create an account to complete checkout and track your delivery.');
                const loginPath = window.location.pathname.includes('/customer/') ? '../auth/login.html' : 'auth/login.html';
                window.location.href = loginPath;
                return;
            }

            const totals = calculateCartTotals();

            // Validate Delivery Address from user's saved addresses (No hardcoded mock addresses)
            const activeAddr = state.addresses && state.addresses.find(a => a.id === state.selectedAddressId);
            if (!activeAddr || !activeAddr.fullAddress || activeAddr.fullAddress.trim().length < 10) {
                alert('Please add or select a delivery address before placing your order.');
                window.JG.openAddressModal();
                return;
            }

            const baseAddress = activeAddr.fullAddress.trim();

            const slotLabel = state.checkoutData.slot === 'evening' ? 'Evening 6-8 PM' 
                            : (state.checkoutData.slot === 'tomorrow' ? 'Tomorrow Morning 7-9 AM' : '⚡ 15-Min Instant Express');

            const instructionsArr = state.checkoutData.deliveryInstructions || [];
            const customNote = (document.getElementById('customDeliveryNote')?.value || '').trim();
            if (customNote) instructionsArr.push(customNote);

            const instructionsStr = instructionsArr.length > 0 ? ` | Instructions: ${instructionsArr.join(', ')}` : '';
            const finalShippingAddress = `${baseAddress} [Slot: ${slotLabel}]${instructionsStr}`.substring(0, 480);

            // Button Loading State
            const btn = document.getElementById('btnPlaceOrder');
            const spinner = document.getElementById('checkoutSpinner');
            if (btn) btn.disabled = true;
            if (spinner) spinner.classList.remove('d-none');

            const rawMethod = (state.checkoutData.paymentMethod || 'UPI').toUpperCase();
            const validPaymentMethod = (rawMethod === 'CARD') ? 'CARD' 
                                     : (rawMethod === 'NETBANKING' ? 'NETBANKING' 
                                     : (rawMethod === 'COD' ? 'COD' : 'UPI'));

            const payload = {
                shipping_address: finalShippingAddress,
                payment_method: validPaymentMethod,
                items: state.cart.map(c => ({
                    product_id: c.productId || c.id,
                    quantity: c.qty || c.quantity || 1
                }))
            };

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn('/api/orders/checkout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();

                if (res.ok && data.success) {
                    const serverOrder = data.order;
                    const cartItemsSnapshot = state.cart.map(c => ({
                        name: c.name,
                        unit: c.unit || c.weight || '1 pack',
                        mrp: Number(c.mrp) || (Number(c.price) * 1.15),
                        price: Number(c.price),
                        qty: Number(c.qty || c.quantity || 1),
                        category: c.category || 'Grocery'
                    }));

                    const confirmedOrder = {
                        id: serverOrder.id,
                        date: serverOrder.created_at ? new Date(serverOrder.created_at).toLocaleString('en-IN') : 'Recent',
                        status: serverOrder.order_status || 'Pending',
                        step: 1,
                        paymentMethod: serverOrder.payment_method,
                        total: serverOrder.total_amount,
                        address: finalShippingAddress,
                        items: cartItemsSnapshot
                    };

                    // Clear cart
                    state.cart = [];
                    persistState();

                    // Route based on payment method
                    if (payload.payment_method !== 'COD') {
                        initPaymentSimulation(confirmedOrder);
                    } else {
                        showOrderConfirmation(confirmedOrder);
                    }
                } else {
                    alert(data.message || 'Checkout could not be processed. Please check address and stock.');
                    if (btn) btn.disabled = false;
                    if (spinner) spinner.classList.add('d-none');
                }
            } catch (err) {
                console.error('Checkout network error:', err);
                alert('Network connection error during checkout. Please try again.');
                if (btn) btn.disabled = false;
                if (spinner) spinner.classList.add('d-none');
            }
        },

        simulatePaymentSuccess: function () {
            let order = window._pendingOrder;
            if (!order) {
                try {
                    order = JSON.parse(sessionStorage.getItem('egm_pending_order') || 'null');
                } catch (e) {}
            }
            if (order) {
                showOrderConfirmation(order);
            } else {
                if (document.getElementById('view-orders')) {
                    window.location.hash = '#orders';
                } else {
                    const inCustomer = window.location.pathname.includes('/customer/');
                    window.location.href = inCustomer ? 'orders.html' : 'customer/orders.html';
                }
            }
        },

        saveProfile: async function (e) {
            if (e) e.preventDefault();
            const name = document.getElementById('profileFullName').value.trim();
            const phone = document.getElementById('profilePhone').value.trim();
            const address = document.getElementById('profileAddress').value.trim();

            const fetchFn = window.apiFetch || fetch;
            try {
                const res = await fetchFn('/api/auth/profile', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        full_name: name,
                        phone: phone,
                        address: address
                    })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    state.user = data.user;
                    persistState();
                    const alertBox = document.getElementById('profileSaveAlert');
                    if (alertBox) {
                        alertBox.style.display = 'block';
                        setTimeout(() => alertBox.style.display = 'none', 3000);
                    }
                    renderProfileView();
                } else {
                    alert(data.message || 'Could not save profile.');
                }
            } catch (err) {
                console.error('Profile update error:', err);
            }
        },

        openProductModal: function (productId) {
            const numId = Number(productId);
            const prod = state.products.find(p => Number(p.id) === numId);
            if (!prod) return;

            const titleEl = document.getElementById('quickViewTitle');
            if (titleEl) titleEl.textContent = prod.name;
            const imgEl = document.getElementById('quickViewImg');
            if (imgEl) imgEl.src = prod.image;
            const priceEl = document.getElementById('quickViewPrice');
            if (priceEl) priceEl.textContent = `₹${prod.price}`;
            const mrpEl = document.getElementById('quickViewMrp');
            if (mrpEl) mrpEl.textContent = `₹${prod.mrp || Math.round(prod.price * 1.15)}`;
            const unitEl = document.getElementById('quickViewUnit');
            if (unitEl) unitEl.textContent = prod.unit || '1 unit';
            const descEl = document.getElementById('quickViewDesc');
            if (descEl) descEl.textContent = prod.description || 'Authentic fresh groceries.';
            const ratEl = document.getElementById('quickViewRating');
            if (ratEl) ratEl.textContent = `${prod.rating} ★ (${prod.ratingCount} reviews)`;

            const addBtn = document.getElementById('quickViewAddBtn');
            if (addBtn) {
                addBtn.onclick = function () {
                    window.JG.addToCart(prod.id);
                    const modalEl = document.getElementById('quickViewModal');
                    if (modalEl && window.bootstrap) {
                        const modal = bootstrap.Modal.getInstance(modalEl);
                        if (modal) modal.hide();
                    }
                };
            }

            const buyBtn = document.getElementById('quickViewBuyBtn');
            if (buyBtn) {
                buyBtn.onclick = function () {
                    const modalEl = document.getElementById('quickViewModal');
                    if (modalEl && window.bootstrap) {
                        const modal = bootstrap.Modal.getInstance(modalEl);
                        if (modal) modal.hide();
                    }
                    window.JG.buyNow(prod.id);
                };
            }

            const detailsLink = document.getElementById('quickViewDetailsLink');
            if (detailsLink) {
                const inCustomer = window.location.pathname.includes('/customer/');
                detailsLink.href = inCustomer ? `product.html?id=${prod.id}` : `customer/product.html?id=${prod.id}`;
            }

            const modalEl = document.getElementById('quickViewModal');
            if (modalEl && window.bootstrap) {
                const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                modal.show();
            }
        },

        buyNow: function (productId, quantity = 1) {
            const numId = Number(productId);
            window.JG.addToCart(numId, quantity);
            const inCustomer = window.location.pathname.includes('/customer/');
            const checkoutUrl = inCustomer ? 'checkout.html' : 'customer/checkout.html';
            const user = state.user;
            if (!user || !user.id) {
                const loginUrl = inCustomer ? `../auth/login.html?redirect=checkout.html` : `auth/login.html?redirect=customer/checkout.html`;
                window.location.href = loginUrl;
            } else {
                window.location.href = checkoutUrl;
            }
        },

        viewInvoice: function (orderId) {
            const inCustomer = window.location.pathname.includes('/customer/');
            const invPath = inCustomer ? 'invoice.html' : 'customer/invoice.html';
            window.open(`${invPath}?order_id=${encodeURIComponent(orderId)}`, '_blank');
        },

        reorder: function (orderId) {
            if (document.getElementById('view-shop')) {
                window.location.hash = '#shop';
            } else {
                const inCustomer = window.location.pathname.includes('/customer/');
                window.location.href = inCustomer ? 'shop.html' : 'customer/shop.html';
            }
            alert('Items added to your bag. Ready for quick checkout!');
        }
    };

    function initPaymentSimulation(order) {
        window._pendingOrder = order;
        sessionStorage.setItem('egm_pending_order', JSON.stringify(order));

        if (!document.getElementById('view-payment')) {
            const inCustomer = window.location.pathname.includes('/customer/');
            window.location.href = inCustomer ? 'payment.html' : 'customer/payment.html';
            return;
        }

        const amountEl = document.getElementById('simPaymentAmount');
        const orderIdEl = document.getElementById('simPaymentOrderId');
        if (amountEl) amountEl.textContent = `₹${order.total}`;
        if (orderIdEl) orderIdEl.textContent = `#${order.id}`;

        const progBar = document.getElementById('paymentSimulatorProgressBar');
        const statusTxt = document.getElementById('paymentSimulatorStatusText');
        if (progBar && statusTxt) {
            progBar.style.width = '20%';
            statusTxt.textContent = 'Connecting to e Grossary Secure Banking Gateway...';

            setTimeout(() => {
                progBar.style.width = '65%';
                statusTxt.textContent = 'Awaiting UPI authorization or OTP confirmation...';
            }, 1000);

            setTimeout(() => {
                progBar.style.width = '100%';
                statusTxt.textContent = 'Payment Authorized Successfully!';
                setTimeout(() => {
                    window.JG.simulatePaymentSuccess();
                }, 600);
            }, 2000);
        }
    }

    function showOrderConfirmation(order) {
        sessionStorage.setItem('egm_confirmed_order', JSON.stringify(order));
        if (document.getElementById('view-order-confirmation')) {
            window.location.hash = '#order-confirmation';
            document.querySelectorAll('.confirmed-order-id-txt').forEach(el => el.textContent = `#${order.id}`);
            document.querySelectorAll('.confirmed-order-total-txt').forEach(el => el.textContent = `₹${order.total}`);
            document.querySelectorAll('.confirmed-order-pay-txt').forEach(el => el.textContent = order.paymentMethod);
            const addrEl = document.getElementById('confirmedOrderAddress');
            if (addrEl && order.address) addrEl.textContent = order.address;
        } else {
            const inCustomer = window.location.pathname.includes('/customer/');
            window.location.href = inCustomer ? 'order-confirmation.html' : 'customer/order-confirmation.html';
        }
    }

    // ── Live Catalog Sync from Backend REST API ──
    async function syncWithServer() {
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/products?per_page=100');
            if (res.ok) {
                const data = await res.json();
                if (data.success && data.products && data.products.length > 0) {
                    state.products = data.products.map(p => {
                        const catRaw = (p.category || p.category_name || '').toLowerCase();
                        let slug = 'staples';
                        if (catRaw.includes('fruit') || catRaw.includes('veg')) slug = 'vegetables';
                        else if (catRaw.includes('dairy') || catRaw.includes('milk')) slug = 'dairy';
                        else if (catRaw.includes('snack') || catRaw.includes('biscuit')) slug = 'snacks';
                        else if (catRaw.includes('bev') || catRaw.includes('tea')) slug = 'beverages';
                        else if (catRaw.includes('clean') || catRaw.includes('house') || catRaw.includes('care')) slug = 'cleaning';
                        else if (catRaw.includes('spice') || catRaw.includes('masala')) slug = 'spices';

                        return {
                            id: p.id,
                            name: p.name,
                            category: slug,
                            categoryName: p.category || p.category_name || 'General',
                            price: parseFloat(p.selling_price),
                            mrp: Math.round(parseFloat(p.selling_price) * 1.15),
                            unit: p.name.match(/\d+\s*(?:kg|g|L|ml|Dozen)/i)?.[0] || '1 unit',
                            rating: p.average_rating ? Number(p.average_rating.toFixed(1)) : 4.8,
                            ratingCount: p.reviews_count || 120,
                            isVeg: true,
                            inStock: p.stock_quantity > 0,
                            eta: "15 MINS",
                            image: p.image_path ? (window.apiUrl ? window.apiUrl(p.image_path) : p.image_path) : '../static/images/logo-icon.png',
                            description: `${p.name} — Authentic grocery item available at e Grossary.`,
                            nutrition: { calories: 'N/A' }
                        };
                    });
                    if (window.EG && window.EG.cart) {
                        window.EG.cart.setCatalog(state.products);
                        window.EG.cart.updateBadgeElements();
                    }
                    renderShopView();
                    if (document.getElementById('productDetailTitle')) {
                        renderProductDetailView();
                    }
                }
            }
        } catch (e) {
            console.debug('Products sync deferred:', e);
        }
    }

    // ── Check Current Authenticated Customer Session with 30-Day Persistence ──
    async function checkAuthSession() {
        const pathFile = window.location.pathname.split('/').pop().replace('.html', '').toLowerCase();
        const isProtectedCustomerRoute = ['profile', 'checkout', 'payment', 'order-confirmation', 'orders', 'wishlist'].includes(pathFile);
        const CUSTOMER_SESSION_MS = 30 * 24 * 60 * 60 * 1000;

        // Check local cache expiration first
        let currentLocal = null;
        try {
            currentLocal = JSON.parse(localStorage.getItem('jg_auth_user') || 'null');
            if (currentLocal && currentLocal.role === 'customer') {
                const now = Date.now();
                if (currentLocal.expires_at && now > Number(currentLocal.expires_at)) {
                    console.warn('[Customer] 30-day customer session expired. Automatically signing out.');
                    localStorage.removeItem('jg_auth_user');
                    state.user = null;
                    if (typeof window.handleLogout === 'function') {
                        window.handleLogout();
                        return;
                    }
                }
            }
        } catch (e) {}

        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/auth/me');
            if (res.ok) {
                const data = await res.json();
                if (data && data.authenticated && data.user && data.user.role === 'customer') {
                    const u = data.user;
                    if (data.expires_at) {
                        u.expires_at = data.expires_at * 1000;
                    } else if (!u.expires_at) {
                        u.expires_at = Date.now() + CUSTOMER_SESSION_MS;
                    }
                    state.user = u;
                    localStorage.setItem('jg_auth_user', JSON.stringify(u));
                    persistState();
                    renderProfileView();
                    document.documentElement.style.display = '';

                    // Batch sync local cart with server
                    if (state.cart.length > 0) {
                        fetchFn('/api/cart/sync', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                items: state.cart.map(c => ({ product_id: c.productId, quantity: c.qty }))
                            })
                        });
                    }
                    return;
                }
            }
        } catch (e) {
            console.debug('Session check deferred:', e);
        }

        // Offline / cached session fallback (valid for 30 days)
        if (currentLocal && currentLocal.role === 'customer') {
            const now = Date.now();
            if (!currentLocal.expires_at || now <= Number(currentLocal.expires_at)) {
                state.user = currentLocal;
                renderProfileView();
                document.documentElement.style.display = '';
                return;
            }
        }

        // Unauthenticated or not customer on server: clear customer state & redirect if on protected page
        state.user = null;
        if (currentLocal && currentLocal.role !== 'admin') {
            localStorage.removeItem('jg_auth_user');
        }
        renderProfileView();

        if (isProtectedCustomerRoute) {
            document.documentElement.style.display = 'none';
            const inCustomerDir = window.location.pathname.includes('/customer/');
            const loginPath = inCustomerDir ? `../auth/login.html?redirect=${pathFile}.html` : `auth/login.html?redirect=customer/${pathFile}.html`;
            window.location.replace(loginPath);
        } else {
            document.documentElement.style.display = '';
        }
    }

    // ── Header Auth UI Synchronization ──
    function updateHeaderAuthUI() {
        const u = state.user;
        const nameDisplays = document.querySelectorAll('.profile-user-name-display, #headerDropdownUserName');
        const emailDisplays = document.querySelectorAll('.profile-user-email-display, #headerDropdownUserEmail');
        const guestActions = document.querySelectorAll('.auth-guest-action, #headerGuestActionRow');
        const customerActions = document.querySelectorAll('.auth-customer-action');
        const accountBtnText = document.getElementById('accountBtnText');

        if (u && u.id) {
            const displayName = u.first_name ? `${u.first_name} ${u.last_name || ''}`.trim() : (u.username || 'Customer');
            nameDisplays.forEach(el => { el.textContent = displayName; });
            emailDisplays.forEach(el => { el.textContent = u.email || 'Verified Shopper'; });
            guestActions.forEach(el => { el.style.display = 'none'; });
            customerActions.forEach(el => { el.style.display = ''; });
            if (accountBtnText) accountBtnText.textContent = displayName.split(' ')[0];
        } else {
            nameDisplays.forEach(el => { el.textContent = 'Customer Account'; });
            emailDisplays.forEach(el => { el.textContent = 'Sign in to sync orders'; });
            guestActions.forEach(el => { el.style.display = ''; });
            customerActions.forEach(el => { el.style.display = 'none'; });
            if (accountBtnText) accountBtnText.textContent = 'Sign In';
        }
    }

    // ── Live Search Suggestions Dropdown ──
    function renderSearchSuggestionsDropdown(query) {
        const drop = document.getElementById('searchDropdown');
        if (!drop) return;
        if (!query) {
            drop.style.display = 'none';
            return;
        }

        const matches = state.products.filter(p =>
            p.name.toLowerCase().includes(query.toLowerCase()) ||
            (p.categoryName && p.categoryName.toLowerCase().includes(query.toLowerCase()))
        ).slice(0, 6);

        if (matches.length === 0) {
            drop.innerHTML = `
                <div class="p-3 text-center text-muted small">
                    <i class="bi bi-search me-1 opacity-50"></i> No groceries found for "<strong>${escapeHTML(query)}</strong>"
                </div>
            `;
            drop.style.display = 'block';
            return;
        }

        const inCustomer = window.location.pathname.includes('/customer/');
        const shopPrefix = inCustomer ? 'product.html' : 'customer/product.html';

        drop.innerHTML = matches.map(p => `
            <a href="${shopPrefix}?id=${p.id}" class="search-suggest-item">
                <div class="d-flex align-items-center gap-2">
                    <img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}" style="width: 32px; height: 32px; object-fit: contain; border-radius: 6px;" onerror="this.onerror=null; this.src='../static/images/logo-icon.png';">
                    <div>
                        <div class="fw-bold text-dark text-truncate" style="max-width: 260px;">${escapeHTML(p.name)}</div>
                        <div class="smallest text-muted">${escapeHTML(p.categoryName || 'Groceries')} &bull; ${escapeHTML(p.unit || '1 unit')}</div>
                    </div>
                </div>
                <span class="fw-bold text-success small">₹${p.price}</span>
            </a>
        `).join('') + `
            <a href="${inCustomer ? 'shop.html' : 'customer/shop.html'}?search=${encodeURIComponent(query)}" class="d-block text-center py-2 border-top text-success fw-bold small text-decoration-none bg-light">
                View all results for "${escapeHTML(query)}" <i class="bi bi-arrow-right"></i>
            </a>
        `;
        drop.style.display = 'block';
    }

    // ── Lifecycle Init ──
    window.addEventListener('DOMContentLoaded', () => {
        updateNavCounters();
        router();
        window.addEventListener('hashchange', router);
        checkAuthSession();
        syncWithServer();

        // Close search dropdown on click outside
        document.addEventListener('click', (e) => {
            const drop = document.getElementById('searchDropdown');
            const searchWrap = document.querySelector('.search-form-wrapper');
            if (drop && searchWrap && !searchWrap.contains(e.target)) {
                drop.style.display = 'none';
            }
        });

        // Listen for components loaded by component-loader
        window.addEventListener('component:loaded', (e) => {
            if (e.detail && e.detail.name === 'customer-header') {
                updateNavCounters();
                updateHeaderAuthUI();
                const searchInput = document.getElementById('masterSearchInput');
                if (searchInput && state.searchQuery) {
                    searchInput.value = state.searchQuery;
                }
            }
        });

        // Listen for reactive updates from EG.cart
        window.addEventListener('cart:updated', (e) => {
            if (e.detail && e.detail.cart) {
                state.cart = e.detail.cart;
                renderShopView();
                if (document.getElementById('cartItemsList')) renderCartView();
                if (document.getElementById('checkoutItemsContainer')) renderCheckoutView();
            }
        });
    });

})();

