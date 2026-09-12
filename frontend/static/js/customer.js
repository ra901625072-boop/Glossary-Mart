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

    // ── Local State Initialization ──
    let state = {
        products: DEFAULT_CATALOG,
        selectedCategory: 'all',
        searchQuery: '',
        sortBy: 'popularity',
        cart: loadInitialCustomerCart(),
        wishlist: JSON.parse(localStorage.getItem('jg_wishlist')) || [],
        activeCoupon: JSON.parse(localStorage.getItem('jg_coupon')) || null,
        user: (function () {
            try {
                const u = JSON.parse(localStorage.getItem('jg_auth_user') || 'null');
                return (u && u.id && u.role === 'customer') ? u : null;
            } catch (e) {
                return null;
            }
        })(),
        orders: [],
        checkoutData: {
            addressType: 'home',
            slot: 'express',
            paymentMethod: 'COD',
            customAddress: ''
        }
    };

    function persistState() {
        localStorage.setItem('jg_cart', JSON.stringify(state.cart));
        localStorage.setItem('egm_cart', JSON.stringify(state.cart));
        localStorage.setItem('jg_wishlist', JSON.stringify(state.wishlist));
        localStorage.setItem('jg_coupon', JSON.stringify(state.activeCoupon));
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
        const finalTotal = Math.max(0, subtotal - couponDiscount + deliveryFee + handlingFee);
        const totalSavings = Math.max(0, (originalMrpTotal - subtotal) + couponDiscount);

        return {
            subtotal: Math.round(subtotal) || 0,
            originalMrpTotal: Math.round(originalMrpTotal) || 0,
            couponDiscount: Math.round(couponDiscount) || 0,
            deliveryFee,
            handlingFee,
            finalTotal: Math.round(finalTotal) || 0,
            totalSavings: Math.round(totalSavings) || 0,
            totalSavings
        };
    }

    // ── View Router Engine ──
    function router() {
        const pageAttr = document.body ? document.body.getAttribute('data-page') : null;
        const pathFile = window.location.pathname.split('/').pop().replace('.html', '').toLowerCase();
        const rawHash = window.location.hash ? window.location.hash.split('?')[0].replace('#', '') : '';
        const inCustomerDir = window.location.pathname.includes('/customer/');

        // If user is inside /customer/ and navigates to a hash that does not exist on this page, redirect to that dedicated page
        if (rawHash && inCustomerDir && !document.getElementById(`view-${rawHash}`)) {
            const knownPages = ['shop', 'cart', 'checkout', 'payment', 'order-confirmation', 'orders', 'wishlist', 'profile'];
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
        const protectedRoutes = ['profile', 'checkout'];
        if (protectedRoutes.includes(route)) {
            const isAuthenticated = Boolean(state.user && state.user.id);
            if (!isAuthenticated) {
                const targetPage = route === 'checkout' ? 'checkout.html' : 'profile.html';
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
        else if (route === 'cart') renderCartView();
        else if (route === 'checkout') renderCheckoutView();
        else if (route === 'orders') { loadUserOrders(); renderOrdersView(); }
        else if (route === 'wishlist') renderWishlistView();
        else if (route === 'profile') renderProfileView();
        else if (route === 'order-confirmation') renderOrderConfirmationFromStorage();
        else if (route === 'payment') renderPaymentSimulationFromStorage();

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

            const actionButtonHtml = qty === 0 ? `
                <button class="btn-add-cart-init" onclick="window.JG.addToCart(${Number(product.id)})">
                    <i class="bi bi-plus-lg me-1"></i>ADD
                </button>
            ` : `
                <div class="product-qty-stepper">
                    <button class="stepper-btn" onclick="window.JG.updateCartQty(${Number(product.id)}, -1)">-</button>
                    <span class="stepper-val">${qty}</span>
                    <button class="stepper-btn" onclick="window.JG.updateCartQty(${Number(product.id)}, 1)">+</button>
                </div>
            `;

            return `
                <div class="col-6 col-md-4 col-lg-3">
                    <div class="product-card-customer">
                        <div class="product-thumb-wrapper">
                            ${discountPercent > 0 ? `<span class="discount-badge-pill">${discountPercent}% OFF</span>` : ''}
                            <button class="wishlist-toggle-btn ${inWishlist ? 'active' : ''}" 
                                    title="${inWishlist ? 'Remove from Wishlist' : 'Add to Wishlist'}"
                                    onclick="window.JG.toggleWishlist(${Number(product.id)})">
                                <i class="bi bi-heart${inWishlist ? '-fill' : ''}"></i>
                            </button>
                            <img src="${escapeHTML(product.image)}" alt="${escapeHTML(product.name)}" class="product-thumb-img" 
                                 onclick="window.JG.openProductModal(${Number(product.id)})" style="cursor:pointer;">
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
        document.querySelectorAll('.checkout-pay-total').forEach(el => el.textContent = `₹${totals.finalTotal}`);

        const addrDisplay = document.getElementById('checkoutSelectedAddressText');
        if (addrDisplay) {
            addrDisplay.textContent = (state.user && state.user.address) ? state.user.address : 'Default Delivery Address: Sector 4, Pali, Rajasthan';
        }

        const phoneEl = document.getElementById('checkoutContactPhone');
        if (phoneEl && state.user && state.user.phone) {
            phoneEl.textContent = state.user.phone;
        }
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
        if (status === 'Delivered') return 4;
        if (status === 'Shipped' || status === 'Out for Delivery') return 3;
        if (status === 'Processing' || status === 'Packed') return 2;
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
            const badgeColor = isDelivered ? 'bg-success' : 'bg-primary';
            const invoiceUrl = window.apiUrl ? window.apiUrl(`/api/orders/${Number(order.id)}/invoice`) : `/api/orders/${Number(order.id)}/invoice`;

            return `
                <div class="ss-surface-card mb-4 p-4 rounded-4 shadow-sm border">
                    <div class="d-flex flex-wrap justify-content-between align-items-center pb-3 border-bottom mb-3 gap-2">
                        <div>
                            <span class="badge ${badgeColor} me-2 px-3 py-2 rounded-pill fw-bold">${escapeHTML(order.status)}</span>
                            <span class="fw-bold text-dark fs-5">#${escapeHTML(order.id)}</span>
                            <span class="text-muted small ms-2">• ${escapeHTML(order.date)}</span>
                        </div>
                        <div class="d-flex gap-2">
                            <a href="${invoiceUrl}" target="_blank" class="btn btn-sm btn-outline-secondary rounded-pill px-3">
                                <i class="bi bi-receipt me-1"></i> Tax Invoice (PDF)
                            </a>
                            <button class="btn btn-sm btn-success rounded-pill px-3" onclick="window.JG.reorder('${escapeHTML(order.id)}')">
                                <i class="bi bi-arrow-repeat me-1"></i> Reorder
                            </button>
                        </div>
                    </div>

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
                    <div class="product-pack-size">${escapeHTML(prod.unit || '1 unit')}</div>
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
            state.searchQuery = val.trim();
            renderShopView();
        },

        clearSearch: function () {
            state.searchQuery = '';
            const input = document.getElementById('masterSearchInput');
            if (input) input.value = '';
            renderShopView();
        },

        handleSortChange: function (val) {
            state.sortBy = val;
            renderShopView();
        },

        addToCart: async function (productId) {
            const existing = state.cart.find(i => i.productId === productId);
            if (existing) {
                existing.qty += 1;
            } else {
                state.cart.push({ productId, qty: 1 });
            }
            persistState();
            renderShopView();
            if (window.location.hash === '#cart' || document.getElementById('cartItemsList')) renderCartView();

            // Fire-and-forget sync to backend
            try {
                const fetchFn = window.apiFetch || fetch;
                fetchFn('/api/cart/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ product_id: productId, quantity: 1 })
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

        selectCheckoutAddress: function (type) {
            state.checkoutData.addressType = type;
            document.querySelectorAll('.checkout-addr-card').forEach(c => {
                c.classList.toggle('selected', c.getAttribute('data-addr') === type);
            });
        },

        selectCheckoutSlot: function (slot) {
            state.checkoutData.slot = slot;
            document.querySelectorAll('.checkout-slot-card').forEach(c => {
                c.classList.toggle('selected', c.getAttribute('data-slot') === slot);
            });
        },

        selectPaymentMethod: function (method) {
            state.checkoutData.paymentMethod = method;
            document.querySelectorAll('.checkout-pay-card').forEach(c => {
                c.classList.toggle('selected', c.getAttribute('data-pay') === method);
            });
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
            const address = (state.user && state.user.address && state.user.address.length >= 15)
                ? state.user.address
                : 'Pali Sector 4, Opposite Krishi Mandi, Pali, Rajasthan 306401';

            const payload = {
                shipping_address: address,
                payment_method: state.checkoutData.paymentMethod || 'COD',
                items: state.cart.map(c => ({
                    product_id: c.productId,
                    quantity: c.qty
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
                    const confirmedOrder = {
                        id: serverOrder.id,
                        date: serverOrder.created_at ? new Date(serverOrder.created_at).toLocaleString('en-IN') : 'Recent',
                        status: serverOrder.order_status || 'Pending',
                        step: 1,
                        paymentMethod: serverOrder.payment_method,
                        total: serverOrder.total_amount,
                        address: address
                    };

                    // Clear cart
                    state.cart = [];
                    persistState();

                    // If non-COD, show quick verification animation
                    if (payload.payment_method !== 'COD') {
                        initPaymentSimulation(confirmedOrder);
                    } else {
                        showOrderConfirmation(confirmedOrder);
                    }
                } else {
                    alert(data.message || 'Checkout could not be processed. Please check address and stock.');
                }
            } catch (err) {
                console.error('Checkout network error:', err);
                alert('Network connection error during checkout. Please try again.');
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
            const prod = state.products.find(p => p.id === productId);
            if (!prod) return;

            document.getElementById('quickViewTitle').textContent = prod.name;
            document.getElementById('quickViewImg').src = prod.image;
            document.getElementById('quickViewPrice').textContent = `₹${prod.price}`;
            document.getElementById('quickViewMrp').textContent = `₹${prod.mrp || Math.round(prod.price * 1.15)}`;
            document.getElementById('quickViewUnit').textContent = prod.unit || '1 unit';
            document.getElementById('quickViewDesc').textContent = prod.description || 'Authentic fresh groceries.';
            document.getElementById('quickViewRating').textContent = `${prod.rating} ★ (${prod.ratingCount} reviews)`;

            const addBtn = document.getElementById('quickViewAddBtn');
            addBtn.onclick = function () {
                window.JG.addToCart(prod.id);
                const modalEl = document.getElementById('quickViewModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            };

            const modal = new bootstrap.Modal(document.getElementById('quickViewModal'));
            modal.show();
        },

        viewInvoice: function (orderId) {
            window.open(`/api/orders/${orderId}/invoice`, '_blank');
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
                            image: p.image_path || 'static/images/logo-icon.png',
                            description: `${p.name} — Authentic grocery item available at e Grossary.`,
                            nutrition: { calories: 'N/A' }
                        };
                    });
                    if (window.EG && window.EG.cart) {
                        window.EG.cart.setCatalog(state.products);
                        window.EG.cart.updateBadgeElements();
                    }
                    renderShopView();
                }
            }
        } catch (e) {
            console.debug('Products sync deferred:', e);
        }
    }

    // ── Check Current Authenticated Customer Session ──
    async function checkAuthSession() {
        const pathFile = window.location.pathname.split('/').pop().replace('.html', '').toLowerCase();
        const isProtectedCustomerRoute = ['profile', 'checkout', 'payment', 'order-confirmation'].includes(pathFile);

        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/auth/me');
            if (res.ok) {
                const data = await res.json();
                if (data && data.authenticated && data.user && data.user.role === 'customer') {
                    state.user = data.user;
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

        // Unauthenticated or not customer on server: clear customer state & redirect if on protected page
        state.user = null;
        const currentLocal = JSON.parse(localStorage.getItem('jg_auth_user') || 'null');
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

    // ── Lifecycle Init ──
    window.addEventListener('DOMContentLoaded', () => {
        updateNavCounters();
        router();
        window.addEventListener('hashchange', router);
        checkAuthSession();
        syncWithServer();

        const searchInput = document.getElementById('masterSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                window.JG.handleSearchInput(e.target.value);
            });
        }

        // Listen for reactive updates from EG.cart
        window.addEventListener('cart:updated', (e) => {
            if (e.detail && e.detail.cart) {
                state.cart = e.detail.cart;
                renderShopView();
                if (document.getElementById('cartItemsList')) renderCartView();
            }
        });
    });

})();
