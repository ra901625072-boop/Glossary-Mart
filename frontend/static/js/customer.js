/**
 * E-GROSSARY — CONSOLIDATED CUSTOMER SUPER-APP ENGINE (customer.js)
 * High-performance state management, client router, cart & checkout, payment simulation, and order tracking.
 */

(function () {
    'use strict';

    // ── Pre-Seeded Product Catalog ──
    const CATALOG = [
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
        },
        {
            id: 7,
            name: "Fortune Sunlite Refined Sunflower Oil 1L",
            category: "staples",
            categoryName: "Staples & Grains",
            price: 199,
            mrp: 230,
            unit: "1 L Pouch",
            rating: 4.7,
            ratingCount: 650,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=400&q=80",
            description: "Enriched with Vitamins A & D, light and heart-healthy cooking oil that retains natural flavours.",
            nutrition: { energy: "900 kcal", fats: "100g", saturated: "11g", mufa: "28g", pufa: "61g" }
        },
        {
            id: 8,
            name: "Amul Pasteurised Salted Butter 500g",
            category: "dairy",
            categoryName: "Dairy & Breakfast",
            price: 145,
            mrp: 160,
            unit: "500 g",
            rating: 4.9,
            ratingCount: 1680,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?auto=format&fit=crop&w=400&q=80",
            description: "Pure salted butter made from fresh dairy cream. Utterly butterly delicious classic taste.",
            nutrition: { calories: "720 kcal", fat: "80g", sodium: "800mg" }
        },
        {
            id: 9,
            name: "Britannia Good Day Cashew Cookies 100g",
            category: "snacks",
            categoryName: "Snacks & Biscuits",
            price: 40,
            mrp: 45,
            unit: "100 g",
            rating: 4.7,
            ratingCount: 790,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?auto=format&fit=crop&w=400&q=80",
            description: "Loaded with crunchy cashew nuts and butter flavour, baked to golden crunchy perfection.",
            nutrition: { calories: "492 kcal", carbs: "67g", protein: "7.2g", fat: "22g" }
        },
        {
            id: 10,
            name: "Tata Sampann Unpolished Toor Dal 1kg",
            category: "staples",
            categoryName: "Staples & Grains",
            price: 89,
            mrp: 105,
            unit: "1 kg",
            rating: 4.8,
            ratingCount: 420,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=400&q=80",
            description: "Nutrient-rich unpolished arhar dal without artificial water, oil, or stone polishing.",
            nutrition: { protein: "22g", fiber: "15g", iron: "3.2mg" }
        },
        {
            id: 11,
            name: "Surf Excel Easy Wash Detergent Powder 1kg",
            category: "cleaning",
            categoryName: "Household",
            price: 165,
            mrp: 195,
            unit: "1 kg",
            rating: 4.8,
            ratingCount: 890,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1583947215259-38e31be8751f?auto=format&fit=crop&w=400&q=80",
            description: "Supercharged stain-removing detergent powder that effortlessly dissolves tough stains.",
            nutrition: { type: "Detergent Powder", fragrance: "Fresh Floral" }
        },
        {
            id: 12,
            name: "Harpic Power Plus Toilet Cleaner 500ml",
            category: "cleaning",
            categoryName: "Household",
            price: 99,
            mrp: 115,
            unit: "500 ml",
            rating: 4.8,
            ratingCount: 610,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=400&q=80",
            description: "Disinfectant toilet cleaner with 10x better limescale removal and 99.9% germ kill formula.",
            nutrition: { action: "Disinfectant & Descaler" }
        },
        {
            id: 13,
            name: "Fresh Farm Crisp Organic Tomatoes 1kg",
            category: "vegetables",
            categoryName: "Fruits & Vegetables",
            price: 35,
            mrp: 50,
            unit: "1 kg",
            rating: 4.8,
            ratingCount: 780,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=400&q=80",
            description: "Farm-fresh ripe hybrid red tomatoes sourced every morning directly from Gujarat Krishi Mandis.",
            nutrition: { calories: "18 kcal", carbs: "3.9g", protein: "0.9g", vitaminC: "14mg" }
        },
        {
            id: 14,
            name: "Fresh Farm Green Spinach (Palak) 250g",
            category: "vegetables",
            categoryName: "Fruits & Vegetables",
            price: 22,
            mrp: 30,
            unit: "250 g",
            rating: 4.7,
            ratingCount: 310,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=400&q=80",
            description: "Crisp, cleaned tender green spinach leaves rich in natural iron, dietary fiber, and vitamins.",
            nutrition: { calories: "23 kcal", iron: "2.7mg", fiber: "2.2g" }
        },
        {
            id: 15,
            name: "Ratnagiri Alphonso Mangoes (1 Dozen)",
            category: "vegetables",
            categoryName: "Fruits & Vegetables",
            price: 599,
            mrp: 750,
            unit: "12 pcs (1 Dozen)",
            rating: 5.0,
            ratingCount: 480,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&w=400&q=80",
            description: "Naturally ripened GI-tagged premium Alphonso (Hapus) mangoes with royal sweetness and intoxicating aroma.",
            nutrition: { calories: "60 kcal per 100g", vitaminA: "High", vitaminC: "High" }
        },
        {
            id: 16,
            name: "Dabur Red Ayurvedic Toothpaste 300g",
            category: "cleaning",
            categoryName: "Personal Care",
            price: 140,
            mrp: 165,
            unit: "300 g Saver Pack",
            rating: 4.9,
            ratingCount: 920,
            isVeg: true,
            inStock: true,
            eta: "15 MINS",
            image: "https://images.unsplash.com/photo-1559650656-5d1d42e99e69?auto=format&fit=crop&w=400&q=80",
            description: "India's No. 1 Ayurvedic paste with clove oil, pudina satva, and tomar beej for total dental protection.",
            nutrition: { formulation: "Ayurvedic Herbal", keyHerbs: "Laung, Pudina, Tomar" }
        }
    ];

    // ── Version Migration & Storage Sanitizer ──
    const DATA_VERSION = '2026-v3-prod-clean';
    if (localStorage.getItem('eg_customer_ver') !== DATA_VERSION) {
        localStorage.setItem('eg_customer_ver', DATA_VERSION);
        localStorage.removeItem('jg_cart');
        localStorage.removeItem('jg_wishlist');
        localStorage.removeItem('jg_coupon');
        localStorage.removeItem('jg_auth_user');
        localStorage.removeItem('eg_orders');
        localStorage.removeItem('jg_orders');
    }

    // ── Local State Initialization ──
    let state = {
        products: CATALOG,
        selectedCategory: 'all',
        searchQuery: '',
        sortBy: 'popularity',
        cart: JSON.parse(localStorage.getItem('jg_cart')) || [],
        wishlist: JSON.parse(localStorage.getItem('jg_wishlist')) || [],
        activeCoupon: JSON.parse(localStorage.getItem('jg_coupon')) || null,
        user: JSON.parse(localStorage.getItem('jg_auth_user')) || null,
        orders: JSON.parse(localStorage.getItem('eg_orders')) || [],
        checkoutData: {
            addressType: 'home',
            slot: 'express',
            paymentMethod: 'UPI',
            customAddress: ''
        }
    };

    // ── Helper: Save to LocalStorage ──
    function persistState() {
        localStorage.setItem('jg_cart', JSON.stringify(state.cart));
        localStorage.setItem('jg_wishlist', JSON.stringify(state.wishlist));
        localStorage.setItem('jg_orders', JSON.stringify(state.orders));
        localStorage.setItem('jg_coupon', JSON.stringify(state.activeCoupon));
        localStorage.setItem('jg_auth_user', JSON.stringify(state.user));
        updateNavCounters();
    }

    // ── Update Badge Counters ──
    function updateNavCounters() {
        const totalCartItems = state.cart.reduce((sum, item) => sum + item.qty, 0);
        const wishlistCount = state.wishlist.length;

        document.querySelectorAll('.cart-counter-badge').forEach(el => {
            el.textContent = totalCartItems;
            el.style.display = totalCartItems > 0 ? 'inline-block' : 'none';
        });

        document.querySelectorAll('.wishlist-counter-badge').forEach(el => {
            el.textContent = wishlistCount;
            el.style.display = wishlistCount > 0 ? 'inline-block' : 'none';
        });

        const subtotal = calculateCartTotals().subtotal;
        document.querySelectorAll('.cart-total-header-pill').forEach(el => {
            el.textContent = `₹${subtotal}`;
        });
    }

    // ── Calculate Totals ──
    function calculateCartTotals() {
        let subtotal = 0;
        let originalMrpTotal = 0;

        state.cart.forEach(cartItem => {
            const prod = state.products.find(p => p.id === cartItem.productId);
            if (prod) {
                subtotal += prod.price * cartItem.qty;
                originalMrpTotal += prod.mrp * cartItem.qty;
            }
        });

        let couponDiscount = 0;
        if (state.activeCoupon) {
            if (state.activeCoupon.code === 'FRESH15') {
                couponDiscount = Math.round(subtotal * 0.15);
            } else if (state.activeCoupon.code === 'JAYGOGA100') {
                couponDiscount = Math.min(subtotal, 100);
            }
        }

        const deliveryFee = subtotal >= 499 || subtotal === 0 ? 0 : 30;
        const handlingFee = subtotal > 0 ? 5 : 0;
        const finalTotal = Math.max(0, subtotal - couponDiscount + deliveryFee + handlingFee);
        const totalSavings = Math.max(0, (originalMrpTotal - subtotal) + couponDiscount);

        return {
            subtotal,
            originalMrpTotal,
            couponDiscount,
            deliveryFee,
            handlingFee,
            finalTotal,
            totalSavings
        };
    }

    // ── View Router Engine ──
    function router() {
        const rawHash = window.location.hash || '#shop';
        const route = rawHash.split('?')[0].replace('#', '') || 'shop';

        // Hide all views
        document.querySelectorAll('.app-view').forEach(view => {
            view.classList.remove('active-view');
        });

        // Show target view
        const targetView = document.getElementById(`view-${route}`) || document.getElementById('view-shop');
        if (targetView) {
            targetView.classList.add('active-view');
        }

        // Update active class on nav links
        document.querySelectorAll('[data-route-link]').forEach(link => {
            const linkRoute = link.getAttribute('data-route-link');
            if (linkRoute === route) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Render view specific logic
        if (route === 'shop') renderShopView();
        else if (route === 'cart') renderCartView();
        else if (route === 'checkout') renderCheckoutView();
        else if (route === 'orders') renderOrdersView();
        else if (route === 'wishlist') renderWishlistView();
        else if (route === 'profile') renderProfileView();

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // ── Shop View Renderer ──
    function renderShopView() {
        const grid = document.getElementById('productsGrid');
        if (!grid) return;

        let filtered = state.products.filter(p => {
            const matchCat = state.selectedCategory === 'all' || p.category === state.selectedCategory;
            const matchSearch = !state.searchQuery ||
                p.name.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
                p.categoryName.toLowerCase().includes(state.searchQuery.toLowerCase());
            return matchCat && matchSearch;
        });

        if (state.sortBy === 'price-low') {
            filtered.sort((a, b) => a.price - b.price);
        } else if (state.sortBy === 'price-high') {
            filtered.sort((a, b) => b.price - a.price);
        } else if (state.sortBy === 'rating') {
            filtered.sort((a, b) => b.rating - a.rating);
        } else if (state.sortBy === 'discount') {
            filtered.sort((a, b) => (b.mrp - b.price) / b.mrp - (a.mrp - a.price) / a.mrp);
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
                    <p class="text-muted small">Try searching for tomatoes, milk, atta, spices or chips.</p>
                    <button class="btn btn-outline-success rounded-pill px-4" onclick="window.JG.clearSearch()">Show All Products</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = filtered.map(product => {
            const discountPercent = Math.round(((product.mrp - product.price) / product.mrp) * 100);
            const inWishlist = state.wishlist.includes(product.id);
            const cartEntry = state.cart.find(item => item.productId === product.id);
            const qty = cartEntry ? cartEntry.qty : 0;

            const actionButtonHtml = qty === 0 ? `
                <button class="btn-add-cart-init" onclick="window.JG.addToCart(${product.id})">
                    <i class="bi bi-plus-lg me-1"></i>ADD
                </button>
            ` : `
                <div class="product-qty-stepper">
                    <button class="stepper-btn" onclick="window.JG.updateCartQty(${product.id}, -1)">-</button>
                    <span class="stepper-val">${qty}</span>
                    <button class="stepper-btn" onclick="window.JG.updateCartQty(${product.id}, 1)">+</button>
                </div>
            `;

            return `
                <div class="col-6 col-md-4 col-lg-3">
                    <div class="product-card-customer">
                        <div class="product-thumb-wrapper">
                            ${discountPercent > 0 ? `<span class="discount-badge-pill">${discountPercent}% OFF</span>` : ''}
                            <button class="wishlist-toggle-btn ${inWishlist ? 'active' : ''}" 
                                    title="${inWishlist ? 'Remove from Wishlist' : 'Add to Wishlist'}"
                                    onclick="window.JG.toggleWishlist(${product.id})">
                                <i class="bi bi-heart${inWishlist ? '-fill' : ''}"></i>
                            </button>
                            <img src="${product.image}" alt="${product.name}" class="product-thumb-img" 
                                 onclick="window.JG.openProductModal(${product.id})" style="cursor:pointer;">
                        </div>

                        <div class="delivery-eta-tag">
                            <i class="bi bi-stopwatch"></i> ${product.eta}
                        </div>

                        <div class="d-flex align-items-center gap-2 mb-1">
                            <span class="veg-icon" title="100% Vegetarian"></span>
                            <span class="product-pack-size mb-0">${product.unit}</span>
                        </div>

                        <h3 class="product-title-text" onclick="window.JG.openProductModal(${product.id})" style="cursor:pointer;">
                            ${product.name}
                        </h3>

                        <div class="product-rating-line">
                            <span>★</span>
                            <span class="text-dark fw-bold">${product.rating}</span>
                            <span class="text-muted">(${product.ratingCount})</span>
                        </div>

                        <div class="price-box-wrap">
                            <div>
                                <span class="curr-price">₹${product.price}</span>
                                ${product.mrp > product.price ? `<span class="mrp-strike">₹${product.mrp}</span>` : ''}
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

        // Free shipping progress
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
                        <img src="${prod.image}" alt="${prod.name}" class="cart-item-img">
                        <div>
                            <div class="fw-bold text-dark mb-1">${prod.name}</div>
                            <div class="text-muted small">${prod.unit} • ₹${prod.price} each</div>
                        </div>
                    </div>

                    <div class="d-flex align-items-center gap-4">
                        <div class="product-qty-stepper">
                            <button class="stepper-btn" onclick="window.JG.updateCartQty(${prod.id}, -1)">-</button>
                            <span class="stepper-val">${cartItem.qty}</span>
                            <button class="stepper-btn" onclick="window.JG.updateCartQty(${prod.id}, 1)">+</button>
                        </div>

                        <div class="fw-bold text-dark text-end" style="min-width: 65px;">
                            ₹${itemTotal}
                        </div>

                        <button class="btn btn-sm btn-link text-danger p-0" title="Remove" onclick="window.JG.removeCartItem(${prod.id})">
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

        // Coupon display
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
            addrDisplay.textContent = (state.user && state.user.address) ? state.user.address : 'Default Delivery Address (Sign in or enter address)';
        }
    }

    // ── Orders View Renderer ──
    function renderOrdersView() {
        const container = document.getElementById('ordersListContainer');
        if (!container) return;

        if (state.orders.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-bag-x display-3 text-muted opacity-50 mb-3 d-block"></i>
                    <h4 class="fw-bold">No orders placed yet</h4>
                    <p class="text-muted small">Your grocery journey begins now! Order fresh produce in 15 mins.</p>
                    <a href="#shop" class="btn btn-success rounded-pill px-4">Start Shopping</a>
                </div>
            `;
            return;
        }

        container.innerHTML = state.orders.map((order, idx) => {
            const isDelivered = order.status === 'Delivered';
            const badgeColor = isDelivered ? 'bg-success' : 'bg-primary';

            return `
                <div class="ss-surface-card mb-4">
                    <div class="d-flex flex-wrap justify-content-between align-items-center pb-3 border-bottom mb-3 gap-2">
                        <div>
                            <span class="badge ${badgeColor} me-2 px-3 py-2 rounded-pill fw-bold">${order.status}</span>
                            <span class="fw-bold text-dark fs-5">#${order.id}</span>
                            <span class="text-muted small ms-2">• ${order.date}</span>
                        </div>
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-outline-secondary rounded-pill px-3" onclick="window.JG.viewInvoice('${order.id}')">
                                <i class="bi bi-receipt me-1"></i> Receipt
                            </button>
                            <button class="btn btn-sm btn-success rounded-pill px-3" onclick="window.JG.reorder('${order.id}')">
                                <i class="bi bi-arrow-repeat me-1"></i> Reorder
                            </button>
                        </div>
                    </div>

                    <!-- Visual Delivery Stepper -->
                    <div class="px-2 py-2 mb-3 bg-light rounded-3">
                        <div class="row text-center g-2">
                            <div class="col-3">
                                <div class="fw-bold small text-${order.step >= 1 ? 'success' : 'muted'}">
                                    <i class="bi bi-check-circle-fill"></i> Order Placed
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

                    ${order.rider ? `
                        <div class="alert alert-info py-2 px-3 small d-flex align-items-center gap-2 mb-3">
                            <i class="bi bi-person-badge-fill fs-5"></i>
                            <div>Assigned Rider: <strong>${order.rider}</strong></div>
                        </div>
                    ` : ''}

                    <!-- Items List -->
                    <div class="row g-2 align-items-center">
                        <div class="col-md-8">
                            <div class="text-muted small mb-1">Ordered Items:</div>
                            <div class="fw-semibold small">
                                ${order.items.map(it => `${it.name} (${it.qty}x)`).join(' • ')}
                            </div>
                        </div>
                        <div class="col-md-4 text-md-end">
                            <div class="text-muted small">Total Paid via ${order.paymentMethod}</div>
                            <div class="fs-4 fw-bold text-dark">₹${order.total}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ── Wishlist View Renderer ──
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
                        <button class="wishlist-toggle-btn active" title="Remove" onclick="window.JG.toggleWishlist(${prod.id})">
                            <i class="bi bi-trash3 text-danger"></i>
                        </button>
                        <img src="${prod.image}" alt="${prod.name}" class="product-thumb-img">
                    </div>
                    <div class="product-pack-size">${prod.unit}</div>
                    <h3 class="product-title-text">${prod.name}</h3>
                    <div class="price-box-wrap">
                        <div class="curr-price">₹${prod.price}</div>
                        <button class="btn btn-sm btn-success rounded-pill px-3" onclick="window.JG.addToCart(${prod.id}); window.JG.toggleWishlist(${prod.id});">
                            <i class="bi bi-bag-plus me-1"></i> Move to Bag
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // ── Profile View Renderer ──
    function renderProfileView() {
        const nameInput = document.getElementById('profileFullName');
        const emailInput = document.getElementById('profileEmail');
        const phoneInput = document.getElementById('profilePhone');
        const addressInput = document.getElementById('profileAddress');
        const walletDisplay = document.getElementById('profileWalletBalance');

        const user = state.user || {};
        if (nameInput) nameInput.value = user.name || '';
        if (emailInput) emailInput.value = user.email || '';
        if (phoneInput) phoneInput.value = user.phone || '';
        if (addressInput) addressInput.value = user.address || '';
        if (walletDisplay) walletDisplay.textContent = `₹${user.wallet || 0}`;

        document.querySelectorAll('.profile-user-name-display').forEach(el => el.textContent = user.name || 'Customer Profile');
        document.querySelectorAll('.profile-user-email-display').forEach(el => el.textContent = user.email || 'Sign in or update your account details');
    }

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

        addToCart: function (productId) {
            const existing = state.cart.find(i => i.productId === productId);
            if (existing) {
                existing.qty += 1;
            } else {
                state.cart.push({ productId, qty: 1 });
            }
            persistState();
            renderShopView();
            if (window.location.hash === '#cart') renderCartView();
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
            if (window.location.hash === '#cart') renderCartView();
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
            if (window.location.hash === '#wishlist') renderWishlistView();
        },

        applyCoupon: function () {
            const input = document.getElementById('couponCodeInput');
            const code = input ? input.value.trim().toUpperCase() : '';
            const feedback = document.getElementById('couponFeedbackMsg');

            if (code === 'FRESH15') {
                state.activeCoupon = { code: 'FRESH15', discountPercent: 15 };
                persistState();
                renderCartView();
                if (feedback) {
                    feedback.className = 'text-success small mt-2 fw-bold';
                    feedback.textContent = 'Awesome! 15% discount applied successfully.';
                }
            } else if (code === 'JAYGOGA100') {
                state.activeCoupon = { code: 'JAYGOGA100', discountFlat: 100 };
                persistState();
                renderCartView();
                if (feedback) {
                    feedback.className = 'text-success small mt-2 fw-bold';
                    feedback.textContent = 'Awesome! Flat ₹100 discount applied successfully.';
                }
            } else {
                if (feedback) {
                    feedback.className = 'text-danger small mt-2 fw-bold';
                    feedback.textContent = 'Invalid code. Try FRESH15 or EGROSSARY100.';
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

        processCheckout: function () {
            if (state.cart.length === 0) {
                alert('Your cart is empty!');
                return;
            }

            const totals = calculateCartTotals();
            const orderId = `EG-${Math.floor(100000 + Math.random() * 900000)}`;

            const orderItems = state.cart.map(c => {
                const prod = state.products.find(p => p.id === c.productId);
                return {
                    name: prod ? prod.name : 'Grocery Item',
                    qty: c.qty,
                    price: prod ? prod.price : 0
                };
            });

            const newOrder = {
                id: orderId,
                date: new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }),
                status: 'Order Placed',
                step: 1,
                rider: 'Suresh Patel (+91 98250 11223)',
                paymentMethod: state.checkoutData.paymentMethod,
                total: totals.finalTotal,
                items: orderItems
            };

            if (state.checkoutData.paymentMethod === 'COD') {
                state.orders.unshift(newOrder);
                state.cart = [];
                persistState();
                showOrderConfirmation(newOrder);
            } else {
                // Open payment simulator
                window.location.hash = '#payment';
                initPaymentSimulation(newOrder);
            }
        },

        simulatePaymentSuccess: function () {
            if (window._pendingOrder) {
                state.orders.unshift(window._pendingOrder);
                state.cart = [];
                persistState();
                showOrderConfirmation(window._pendingOrder);
            } else {
                window.location.hash = '#orders';
            }
        },

        saveProfile: function (e) {
            if (e) e.preventDefault();
            const name = document.getElementById('profileFullName').value;
            const email = document.getElementById('profileEmail').value;
            const phone = document.getElementById('profilePhone').value;
            const address = document.getElementById('profileAddress').value;

            if (!state.user) state.user = {};
            state.user.name = name;
            state.user.email = email;
            state.user.phone = phone;
            state.user.address = address;
            persistState();

            const alertBox = document.getElementById('profileSaveAlert');
            if (alertBox) {
                alertBox.style.display = 'block';
                setTimeout(() => alertBox.style.display = 'none', 3000);
            }
            renderProfileView();
        },

        openProductModal: function (productId) {
            const prod = state.products.find(p => p.id === productId);
            if (!prod) return;

            document.getElementById('quickViewTitle').textContent = prod.name;
            document.getElementById('quickViewImg').src = prod.image;
            document.getElementById('quickViewPrice').textContent = `₹${prod.price}`;
            document.getElementById('quickViewMrp').textContent = `₹${prod.mrp}`;
            document.getElementById('quickViewUnit').textContent = prod.unit;
            document.getElementById('quickViewDesc').textContent = prod.description;
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
            const order = state.orders.find(o => o.id === orderId);
            if (!order) return;

            document.getElementById('invoiceOrderId').textContent = `#${order.id}`;
            document.getElementById('invoiceDate').textContent = order.date;
            document.getElementById('invoicePayMethod').textContent = order.paymentMethod;
            document.getElementById('invoiceTotal').textContent = `₹${order.total}`;

            const itemsTbody = document.getElementById('invoiceItemsTbody');
            itemsTbody.innerHTML = order.items.map((it, i) => `
                <tr>
                    <td>${i + 1}</td>
                    <td>${it.name}</td>
                    <td class="text-center">${it.qty}</td>
                    <td class="text-end">₹${it.price}</td>
                    <td class="text-end fw-bold">₹${it.qty * it.price}</td>
                </tr>
            `).join('');

            const modal = new bootstrap.Modal(document.getElementById('invoiceModal'));
            modal.show();
        },

        reorder: function (orderId) {
            const order = state.orders.find(o => o.id === orderId);
            if (!order) return;

            order.items.forEach(it => {
                const prod = state.products.find(p => p.name === it.name);
                if (prod) {
                    window.JG.addToCart(prod.id);
                }
            });
            window.location.hash = '#cart';
        }
    };

    function initPaymentSimulation(order) {
        window._pendingOrder = order;
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
            }, 1200);

            setTimeout(() => {
                progBar.style.width = '100%';
                statusTxt.textContent = 'Payment Authorized Successfully!';
                setTimeout(() => {
                    window.JG.simulatePaymentSuccess();
                }, 800);
            }, 2600);
        }
    }

    function showOrderConfirmation(order) {
        window.location.hash = '#order-confirmation';
        document.querySelectorAll('.confirmed-order-id-txt').forEach(el => el.textContent = `#${order.id}`);
        document.querySelectorAll('.confirmed-order-total-txt').forEach(el => el.textContent = `₹${order.total}`);
        document.querySelectorAll('.confirmed-order-pay-txt').forEach(el => el.textContent = order.paymentMethod);
    }

    async function syncWithServer() {
        try {
            const res = await (window.apiFetch || fetch)('/api/products?per_page=100');
            if (res.ok) {
                const data = await res.json();
                if (data.success && data.products && data.products.length > 0) {
                    state.products = data.products.map(p => ({
                        id: p.id,
                        name: p.name,
                        category: p.category_name ? p.category_name.toLowerCase().replace(/[^a-z0-9]/g, '') : 'general',
                        categoryName: p.category_name || 'General',
                        price: parseFloat(p.selling_price),
                        mrp: Math.round(parseFloat(p.selling_price) * 1.15),
                        unit: '1 unit',
                        rating: 4.8,
                        ratingCount: 150,
                        isVeg: true,
                        inStock: p.stock_quantity > 0,
                        eta: "15 MINS",
                        image: p.image_path || 'static/images/logo-icon.png',
                        description: p.description || `${p.name} — Authentic grocery item available at e Grossary.`,
                        nutrition: { calories: 'N/A' }
                    }));
                    renderShopView();
                }
            }
        } catch (e) {
            console.debug('API sync deferred (running in offline/static mode):', e);
        }
    }

    // ── Lifecycle Init ──
    window.addEventListener('DOMContentLoaded', () => {
        updateNavCounters();
        router();
        window.addEventListener('hashchange', router);
        syncWithServer();

        // Search input binding
        const searchInput = document.getElementById('masterSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                window.JG.handleSearchInput(e.target.value);
            });
        }
    });

})();
