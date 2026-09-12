/**
 * e Grossary — Frontend Engine (homepage.js)
 * Standalone, robust client-side e-commerce engine:
 * - Product catalog rendering (Today's Deals, Best Sellers, Category exploration)
 * - Reactive Cart drawer with quantity steppers & free shipping progress bar (threshold ₹499)
 * - Dynamic coupon discount calculation (FRESH15 & JAYGOGA100)
 * - Live search with instant suggestions
 * - Flash sale real-time countdown timer
 * - Location selector modal
 * - Multi-step checkout simulation & live order tracking
 * - Cross-project route resolver (Shop, Cart, Checkout, Profile, Auth)
 */

(function () {
    'use strict';

    function escapeHTML(str) {
        if (window.EG && window.EG.utils && window.EG.utils.escapeHTML) {
            return window.EG.utils.escapeHTML(str);
        }
        if (!str) return '';
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

    // ── 1. Real Project Catalog Data (Aligning with Real Database & Mockup) ──
    let DEALS_PRODUCTS = [
        {
            id: 1,
            name: "Aashirvaad Atta 5kg",
            category: "Staples & Grains",
            price: 279,
            mrp: 320,
            discount: "13% OFF",
            unit: "5 kg",
            rating: 4.8,
            reviews: "1.2k",
            image: "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=400&q=80",
            inStock: true
        },
        {
            id: 2,
            name: "Tata Salt 1kg",
            category: "Masala & Spices",
            price: 36,
            mrp: 40,
            discount: "10% OFF",
            unit: "1 kg",
            rating: 4.5,
            reviews: "980",
            image: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=400&q=80",
            inStock: true
        },
        {
            id: 3,
            name: "Amul Pasteurized Milk 1L",
            category: "Dairy & Breakfast",
            price: 56,
            mrp: 70,
            discount: "20% OFF",
            unit: "1 L",
            rating: 4.7,
            reviews: "2.3k",
            image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=400&q=80",
            inStock: true
        },
        {
            id: 4,
            name: "Maggi Noodles 280g",
            category: "Snacks & Biscuits",
            price: 42,
            mrp: 50,
            discount: "15% OFF",
            unit: "280 g",
            rating: 4.6,
            reviews: "1.8k",
            image: "https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=400&q=80",
            inStock: true
        },
        {
            id: 5,
            name: "Tata Tea Premium 250g",
            category: "Beverages",
            price: 132,
            mrp: 150,
            discount: "12% OFF",
            unit: "250 g",
            rating: 4.5,
            reviews: "1.5k",
            image: "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=400&q=80",
            inStock: true
        },
        {
            id: 6,
            name: "Cadbury Dairy Milk 120g",
            category: "Snacks & Biscuits",
            price: 98,
            mrp: 120,
            discount: "18% OFF",
            unit: "120 g",
            rating: 4.9,
            reviews: "2.1k",
            image: "https://images.unsplash.com/photo-1549007994-cb92caebd54b?auto=format&fit=crop&w=400&q=80",
            inStock: true
        }
    ];

    let BESTSELLER_PRODUCTS = [
        {
            id: 7,
            name: "Fortune Refined Oil",
            category: "Staples & Grains",
            price: 199,
            mrp: 220,
            discount: "10% OFF",
            unit: "1 L",
            rating: 4.5,
            reviews: "1.2k",
            image: "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=400&q=80",
            inStock: true
        },
        {
            id: 8,
            name: "Amul Butter",
            category: "Dairy & Breakfast",
            price: 145,
            mrp: 160,
            discount: "9% OFF",
            unit: "500 g",
            rating: 4.8,
            reviews: "2.3k",
            image: "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?auto=format&fit=crop&w=400&q=80",
            inStock: true
        },
        {
            id: 9,
            name: "Britannia Good Day Biscuits",
            category: "Snacks & Biscuits",
            price: 40,
            mrp: 45,
            discount: "11% OFF",
            unit: "100 g",
            rating: 4.4,
            reviews: "1.5k",
            image: "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?auto=format&fit=crop&w=400&q=80",
            inStock: true
        },
        {
            id: 10,
            name: "Tata Sampann Dal",
            category: "Staples & Grains",
            price: 89,
            mrp: 105,
            discount: "15% OFF",
            unit: "1 kg",
            rating: 4.7,
            reviews: "980",
            image: "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=400&q=80",
            inStock: true
        },
        {
            id: 11,
            name: "Surf Excel Detergent",
            category: "Household",
            price: 165,
            mrp: 185,
            discount: "11% OFF",
            unit: "1 kg",
            rating: 4.6,
            reviews: "780",
            image: "https://images.unsplash.com/photo-1583947215259-38e31be8751f?auto=format&fit=crop&w=400&q=80",
            inStock: true
        },
        {
            id: 12,
            name: "Harpic Toilet Cleaner",
            category: "Household",
            price: 99,
            mrp: 115,
            discount: "14% OFF",
            unit: "500 ml",
            rating: 4.5,
            reviews: "790",
            image: "https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=400&q=80",
            inStock: true
        }
    ];

    let ALL_PRODUCTS = [...DEALS_PRODUCTS, ...BESTSELLER_PRODUCTS];

    // ── 2. Local State Management ──
    let cart = [];
    let wishlist = [];
    let appliedCoupon = null;
    let currentDeliveryLocation = "Pali & Mehsana (384260)";

    // Load persisted state from localStorage
    function loadState() {
        try {
            const savedCart = localStorage.getItem('egm_cart');
            if (savedCart) {
                cart = JSON.parse(savedCart);
            } else {
                cart = [];
            }

            const savedWishlist = localStorage.getItem('egm_wishlist');
            if (savedWishlist) {
                wishlist = JSON.parse(savedWishlist);
            }

            const savedLoc = localStorage.getItem('egm_location');
            if (savedLoc) {
                currentDeliveryLocation = savedLoc;
            }
        } catch (e) {
            console.warn("Could not load state from localStorage", e);
        }
    }

    function saveCart() {
        try {
            localStorage.setItem('egm_cart', JSON.stringify(cart));
            localStorage.setItem('jg_cart', JSON.stringify(cart));
        } catch (e) {
            console.warn("Could not save cart", e);
        }
        updateCartUI();
    }

    function saveWishlist() {
        try {
            localStorage.setItem('egm_wishlist', JSON.stringify(wishlist));
        } catch (e) {
            console.warn("Could not save wishlist", e);
        }
        updateWishlistUI();
    }

    // ── 3. Render Product Cards ──
    function createProductCardHTML(p) {
        const cartItem = cart.find(item => String(item.id) === String(p.id));
        const qty = cartItem ? cartItem.quantity : 1;

        return `
            <div class="product-card" id="card-${escapeHTML(String(p.id))}">
                ${p.discount ? `<span class="discount-badge-pill">${escapeHTML(p.discount)}</span>` : ''}
                <div class="product-img-box" onclick="openQuickView('${escapeHTML(String(p.id))}')" style="cursor: pointer;">
                    <img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}" class="product-img" loading="lazy">
                </div>
                <div class="product-info">
                    <div class="product-rating">
                        <i class="bi bi-star-fill star-icon"></i>
                        <span class="fw-bold">${Number(p.rating)}</span>
                        <span class="review-count">(${Number(p.reviews)})</span>
                    </div>
                    <h4 class="product-name" title="${escapeHTML(p.name)}" onclick="openQuickView('${escapeHTML(String(p.id))}')" style="cursor: pointer;">${escapeHTML(p.name)}</h4>
                    <div class="product-price-row">
                        <span class="current-price">₹${Number(p.price)}</span>
                        ${p.mrp ? `<span class="mrp-price">₹${Number(p.mrp)}</span>` : ''}
                    </div>
                    <div class="product-unit">${escapeHTML(p.unit)}</div>
                </div>
                <div class="product-card-actions">
                    <div class="stepper-box">
                        <button class="stepper-btn" onclick="updateItemQuantity('${escapeHTML(String(p.id))}', -1)" aria-label="Decrease quantity">&minus;</button>
                        <span class="stepper-value" id="stepper-val-${escapeHTML(String(p.id))}">${Number(qty)}</span>
                        <button class="stepper-btn" onclick="updateItemQuantity('${escapeHTML(String(p.id))}', 1)" aria-label="Increase quantity">&plus;</button>
                    </div>
                    <button class="btn-card-add" onclick="addToCart('${escapeHTML(String(p.id))}')">
                        Add
                    </button>
                </div>
            </div>
        `;
    }

    function renderProductGrids() {
        const dealsGrid = document.getElementById('dealsGrid');
        if (dealsGrid) {
            dealsGrid.innerHTML = DEALS_PRODUCTS.map(createProductCardHTML).join('');
        }

        const bestsellersGrid = document.getElementById('bestsellersGrid');
        if (bestsellersGrid) {
            bestsellersGrid.innerHTML = BESTSELLER_PRODUCTS.map(createProductCardHTML).join('');
        }
    }

    // ── 4. Cart State & Calculation ──
    function addToCart(productId, explicitQty = null) {
        const product = ALL_PRODUCTS.find(p => String(p.id) === String(productId));
        if (!product) return;

        const stepperEl = document.getElementById(`stepper-val-${product.id}`);
        const qtyToAdd = explicitQty !== null ? explicitQty : (stepperEl ? parseInt(stepperEl.innerText) || 1 : 1);

        const existingIndex = cart.findIndex(item => String(item.id || item.productId) === String(product.id));
        if (existingIndex > -1) {
            const newQty = (cart[existingIndex].quantity || cart[existingIndex].qty || 0) + qtyToAdd;
            cart[existingIndex].quantity = newQty;
            cart[existingIndex].qty = newQty;
        } else {
            cart.push({
                id: product.id,
                productId: product.id,
                name: product.name,
                price: Number(product.price) || 0,
                mrp: Number(product.mrp) || Math.round(Number(product.price) * 1.15),
                unit: product.unit,
                quantity: qtyToAdd,
                qty: qtyToAdd,
                image: product.image
            });
        }

        saveCart();
        showToast(`Added ${product.name} to cart!`, 'success');

        // Asynchronously sync with Flask backend session & database cart
        const numericId = parseInt(product.id, 10);
        if (!isNaN(numericId)) {
            (window.apiFetch || fetch)('/api/cart/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: numericId, quantity: qtyToAdd })
            }).catch(() => {});
        }
    }

    function updateItemQuantity(productId, delta) {
        const stepperEl = document.getElementById(`stepper-val-${productId}`);
        const existingItem = cart.find(item => String(item.id) === String(productId));

        if (existingItem) {
            existingItem.quantity += delta;
            if (existingItem.quantity <= 0) {
                cart = cart.filter(item => String(item.id) !== String(productId));
                showToast(`Removed item from cart.`, 'info');
            }
            saveCart();
            if (stepperEl) {
                stepperEl.innerText = existingItem ? Math.max(1, existingItem.quantity) : 1;
            }
        } else {
            // Adjust card-level stepper before adding
            if (stepperEl) {
                let current = parseInt(stepperEl.innerText) || 1;
                current = Math.max(1, current + delta);
                stepperEl.innerText = current;
            }
        }
    }

    function removeCartItem(productId) {
        cart = cart.filter(item => String(item.id) !== String(productId));
        saveCart();
        showToast(`Item removed from bag.`, 'info');
    }

    function updateCartUI() {
        const totalItemsCount = cart.reduce((acc, item) => acc + item.quantity, 0);
        const subtotal = cart.reduce((acc, item) => acc + (item.price * item.quantity), 0);

        // Header and mobile badge counters
        const headerBadge = document.getElementById('cartCountBadge');
        if (headerBadge) headerBadge.innerText = totalItemsCount;

        const mobileBadge = document.getElementById('mobileCartBadge');
        if (mobileBadge) mobileBadge.innerText = totalItemsCount;

        // Offcanvas Cart Items Container
        const cartContainer = document.getElementById('cartItemsContainer');
        if (cartContainer) {
            if (cart.length === 0) {
                cartContainer.innerHTML = `
                    <div class="text-center py-5 text-muted">
                        <i class="bi bi-basket2 display-3 text-success opacity-50 mb-3"></i>
                        <h6 class="fw-bold">Your shopping bag is empty</h6>
                        <p class="small">Add items from Today's Deals or Best Sellers to start shopping.</p>
                        <button class="btn btn-sm btn-outline-success rounded-pill px-4 mt-2" data-bs-dismiss="offcanvas" onclick="location.href='#deals'">Browse Deals</button>
                    </div>
                `;
            } else {
                cartContainer.innerHTML = cart.map(item => `
                    <div class="cart-item-row">
                        <img src="${escapeHTML(item.image)}" alt="${escapeHTML(item.name)}" class="cart-item-img">
                        <div class="cart-item-details">
                            <div class="cart-item-title">${escapeHTML(item.name)}</div>
                            <div class="cart-item-price">₹${Number(item.price)} <span class="small text-muted">(${escapeHTML(item.unit)})</span></div>
                            <div class="d-flex align-items-center gap-2 mt-1">
                                 <div class="stepper-box" style="height: 28px; width: 90px;">
                                     <button class="stepper-btn" onclick="updateItemQuantity('${escapeHTML(String(item.id))}', -1)">&minus;</button>
                                     <span class="stepper-value">${Number(item.quantity)}</span>
                                     <button class="stepper-btn" onclick="updateItemQuantity('${escapeHTML(String(item.id))}', 1)">&plus;</button>
                                 </div>
                                 <span class="small fw-bold text-dark">₹${Number(item.price) * Number(item.quantity)}</span>
                            </div>
                        </div>
                        <button class="cart-item-remove-btn" onclick="removeCartItem('${escapeHTML(String(item.id))}')" title="Remove item">
                            <i class="bi bi-trash3"></i>
                        </button>
                    </div>
                `).join('');
            }
        }

        // Free Shipping Calculation (Threshold: ₹499)
        const freeShippingThreshold = 499;
        const remainingForFree = Math.max(0, freeShippingThreshold - subtotal);
        const freeShippingFill = document.getElementById('freeShippingFill');
        const freeShippingMsg = document.getElementById('freeShippingMsg');

        if (freeShippingFill && freeShippingMsg) {
            const percent = Math.min(100, (subtotal / freeShippingThreshold) * 100);
            freeShippingFill.style.width = `${percent}%`;

            if (remainingForFree === 0) {
                freeShippingMsg.innerHTML = `<i class="bi bi-check-circle-fill text-success"></i> You unlocked <strong>FREE Delivery!</strong>`;
            } else {
                freeShippingMsg.innerHTML = `Add <strong>₹${remainingForFree}</strong> more to unlock <strong>FREE Delivery!</strong>`;
            }
        }

        // Pricing Breakdown
        const deliveryFee = (subtotal >= freeShippingThreshold || subtotal === 0) ? 0 : 40;
        let discountAmount = 0;
        if (appliedCoupon === 'FRESH15') {
            discountAmount = Math.round(subtotal * 0.15);
        } else if (appliedCoupon === 'JAYGOGA100' && subtotal >= 500) {
            discountAmount = 100;
        }

        const grandTotal = Math.max(0, subtotal + deliveryFee - discountAmount);

        const subtotalEl = document.getElementById('billSubtotal');
        if (subtotalEl) subtotalEl.innerText = `₹${subtotal}`;

        const deliveryEl = document.getElementById('billDeliveryFee');
        if (deliveryEl) deliveryEl.innerText = deliveryFee === 0 ? 'FREE' : `₹${deliveryFee}`;

        const discountRow = document.getElementById('billDiscountRow');
        const discountEl = document.getElementById('billDiscount');
        if (discountRow && discountEl) {
            if (discountAmount > 0) {
                discountRow.style.display = 'flex';
                discountEl.innerText = `-₹${discountAmount}`;
            } else {
                discountRow.style.display = 'none';
            }
        }

        const grandTotalEl = document.getElementById('billGrandTotal');
        if (grandTotalEl) grandTotalEl.innerText = `₹${grandTotal}`;

        // Also update Checkout modal summary if open
        const modalSubtotal = document.getElementById('checkoutSubtotal');
        if (modalSubtotal) modalSubtotal.innerText = `₹${subtotal}`;

        const modalGrandTotal = document.getElementById('checkoutGrandTotal');
        if (modalGrandTotal) modalGrandTotal.innerText = `₹${grandTotal}`;
    }

    // ── 5. Coupons & Promo Codes ──
    function applyCouponCode() {
        const input = document.getElementById('couponInput');
        const feedback = document.getElementById('couponFeedback');
        if (!input) return;

        const code = input.value.trim().toUpperCase();
        if (code === 'FRESH15') {
            appliedCoupon = 'FRESH15';
            if (feedback) {
                feedback.className = 'small text-success mt-1';
                feedback.innerHTML = `<i class="bi bi-check-circle me-1"></i> Coupon <strong>FRESH15</strong> applied (15% OFF)!`;
            }
            showToast('15% discount applied!', 'success');
        } else if (code === 'JAYGOGA100') {
            appliedCoupon = 'JAYGOGA100';
            if (feedback) {
                feedback.className = 'small text-success mt-1';
                feedback.innerHTML = `<i class="bi bi-check-circle me-1"></i> Coupon <strong>JAYGOGA100</strong> applied (₹100 Flat Savings)!`;
            }
            showToast('₹100 savings applied!', 'success');
        } else {
            appliedCoupon = null;
            if (feedback) {
                feedback.className = 'small text-danger mt-1';
                feedback.innerText = 'Invalid coupon code. Try FRESH15 or JAYGOGA100.';
            }
            showToast('Invalid coupon code.', 'danger');
        }
        updateCartUI();
    }

    // ── 6. Flash Sale Real-Time Countdown Timer ──
    function initCountdown() {
        const countdownEl = document.getElementById('saleCountdown');
        if (!countdownEl) return;

        // Set countdown to 2 hours 14 mins 36 secs from now (as displayed in mockup)
        let totalSeconds = (2 * 3600) + (14 * 60) + 36;

        setInterval(() => {
            if (totalSeconds > 0) {
                totalSeconds--;
                const h = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
                const m = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
                const s = String(totalSeconds % 60).padStart(2, '0');
                countdownEl.innerText = `${h}:${m}:${s}`;
            }
        }, 1000);
    }

    // ── 7. Live Search Autocomplete ──
    function handleLiveSearch(query) {
        const dropdown = document.getElementById('searchDropdown');
        if (!dropdown) return;

        const q = query.trim().toLowerCase();
        if (q.length < 2) {
            dropdown.style.display = 'none';
            dropdown.innerHTML = '';
            return;
        }

        const matches = ALL_PRODUCTS.filter(p =>
            p.name.toLowerCase().includes(q) ||
            p.category.toLowerCase().includes(q)
        ).slice(0, 6);

        if (matches.length === 0) {
            dropdown.innerHTML = `<div class="p-3 text-muted small text-center">No grocery products found for "${escapeHTML(query)}".</div>`;
        } else {
            dropdown.innerHTML = matches.map(p => `
                <div class="search-suggestion-item" onclick="selectSearchResult('${escapeHTML(String(p.id))}')">
                    <div class="d-flex align-items-center gap-2">
                        <img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}" style="width: 36px; height: 36px; object-fit: contain; border-radius: 4px;">
                        <div>
                            <div class="small fw-bold text-dark">${escapeHTML(p.name)}</div>
                            <div class="smallest text-muted">${escapeHTML(p.unit)}</div>
                        </div>
                    </div>
                    <div class="text-end">
                        <span class="small fw-bold text-success">₹${Number(p.price)}</span>
                    </div>
                </div>
            `).join('');
        }
        dropdown.style.display = 'block';
    }

    function triggerSearch() {
        const input = document.getElementById('globalSearchInput');
        if (input) handleLiveSearch(input.value);
    }

    function selectSearchResult(productId) {
        const dropdown = document.getElementById('searchDropdown');
        if (dropdown) dropdown.style.display = 'none';
        openQuickView(productId);
    }

    // ── 8. Category Navigation & Filtering ──
    function filterByCategory(categoryKey) {
        const catMap = {
            'produce': 'Fruits & Vegetables',
            'dairy': 'Dairy & Breakfast',
            'staples': 'Staples & Grains',
            'snacks': 'Snacks & Biscuits',
            'beverages': 'Beverages',
            'personal': 'Personal Care',
            'household': 'Household',
            'spices': 'Masala & Spices'
        };
        const realCat = catMap[categoryKey] || categoryKey;
        if (realCat && realCat !== 'all') {
            window.location.href = `/shop?category=${encodeURIComponent(realCat)}`;
        } else {
            window.location.href = '/shop';
        }
    }

    // ── 9. Wishlist Controls ──
    function toggleWishlist(productId) {
        const idx = wishlist.indexOf(productId);
        if (idx > -1) {
            wishlist.splice(idx, 1);
            showToast('Removed from wishlist', 'info');
        } else {
            wishlist.push(productId);
            showToast('Added to your saved wishlist ❤️', 'success');
        }
        saveWishlist();
    }

    function updateWishlistUI() {
        const badge = document.getElementById('wishlistCountBadge');
        if (badge) badge.innerText = wishlist.length;

        const mobileBadge = document.getElementById('mobileWishlistBadge');
        if (mobileBadge) mobileBadge.innerText = wishlist.length;
    }

    // ── 10. Location Selector Modal ──
    function setDeliveryLocation(locationName) {
        currentDeliveryLocation = locationName;
        try {
            localStorage.setItem('egm_location', locationName);
        } catch (e) {}

        const locLabel = document.getElementById('headerDeliveryLocation');
        if (locLabel) locLabel.innerText = locationName;

        const ribbonLoc = document.getElementById('ribbonLocation');
        if (ribbonLoc) ribbonLoc.innerText = locationName;

        const modalEl = document.getElementById('locationModal');
        if (modalEl && window.bootstrap) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }
        showToast(`Delivery location set to ${locationName}!`, 'success');
    }

    // ── 11. Quick View Modal ──
    function openQuickView(productId) {
        const product = ALL_PRODUCTS.find(p => String(p.id) === String(productId));
        if (!product) return;

        const modalTitle = document.getElementById('quickViewTitle');
        const modalBody = document.getElementById('quickViewBody');
        if (!modalTitle || !modalBody) return;

        modalTitle.innerText = product.name;
        modalBody.innerHTML = `
            <div class="row g-4 align-items-center">
                <div class="col-md-5 text-center">
                    <img src="${product.image}" alt="${product.name}" class="img-fluid rounded-3" style="max-height: 220px; object-fit: contain;">
                </div>
                <div class="col-md-7">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <span class="badge bg-success">${product.discount || 'Fresh Harvest'}</span>
                        <span class="text-warning small"><i class="bi bi-star-fill"></i> ${product.rating} (${product.reviews} reviews)</span>
                    </div>
                    <h5 class="fw-bold mb-1">${product.name}</h5>
                    <p class="text-muted small mb-3">Authentic essential provision, sourced directly for purity and freshness.</p>
                    <div class="d-flex align-items-baseline gap-2 mb-3">
                        <span class="fs-4 fw-bold text-success">₹${product.price}</span>
                        ${product.mrp ? `<span class="text-muted text-decoration-line-through">₹${product.mrp}</span>` : ''}
                        <span class="small text-muted ms-2">Unit: ${product.unit}</span>
                    </div>
                    <div class="d-flex flex-wrap gap-2">
                        <button class="btn btn-ss-primary px-4 py-2 rounded-pill fw-bold" onclick="addToCart('${product.id}'); bootstrap.Modal.getInstance(document.getElementById('quickViewModal')).hide();">
                            <i class="bi bi-cart-plus me-1"></i> Add to Bag
                        </button>
                        <a href="/product/${product.id}" class="btn btn-outline-success px-4 py-2 rounded-pill fw-bold">
                            <i class="bi bi-box-arrow-up-right me-1"></i> Full Details &amp; Reviews
                        </a>
                    </div>
                </div>
            </div>
        `;

        if (window.bootstrap) {
            const modal = new bootstrap.Modal(document.getElementById('quickViewModal'));
            modal.show();
        }
    }

    function isCustomerAuthenticated() {
        try {
            const user = JSON.parse(localStorage.getItem('jg_auth_user') || 'null');
            return Boolean(user && user.id && user.role === 'customer');
        } catch (e) {
            return false;
        }
    }

    function handleCheckoutNavigation(e) {
        if (e) e.preventDefault();
        if (cart.length === 0) {
            showToast('Your shopping bag is empty! Add items first.', 'warning');
            return false;
        }
        if (!isCustomerAuthenticated()) {
            showToast('Please sign in with your customer account to proceed to checkout.', 'info');
            setTimeout(() => {
                window.location.href = 'auth/login.html?redirect=customer/checkout.html';
            }, 600);
            return false;
        }
        window.location.href = 'customer/checkout.html';
        return false;
    }

    function handleWishlistNavigation(e) {
        if (e) e.preventDefault();
        if (!isCustomerAuthenticated()) {
            showToast('Please sign in to view your saved wishlist.', 'info');
            const authModalEl = document.getElementById('authModal');
            if (authModalEl && window.bootstrap) {
                authModalEl.dataset.redirect = 'customer/wishlist.html';
                switchAuthTab('login');
                const modal = bootstrap.Modal.getInstance(authModalEl) || new bootstrap.Modal(authModalEl);
                modal.show();
            } else {
                setTimeout(() => {
                    window.location.href = 'auth/login.html?redirect=customer/wishlist.html';
                }, 400);
            }
            return false;
        }
        window.location.href = 'customer/wishlist.html';
        return false;
    }

    function handleOrdersNavigation(e) {
        if (e) e.preventDefault();
        if (!isCustomerAuthenticated()) {
            showToast('Please sign in with your customer account to track orders.', 'info');
            const authModalEl = document.getElementById('authModal');
            if (authModalEl && window.bootstrap) {
                authModalEl.dataset.redirect = 'customer/orders.html';
                switchAuthTab('login');
                const modal = bootstrap.Modal.getInstance(authModalEl) || new bootstrap.Modal(authModalEl);
                modal.show();
            } else {
                setTimeout(() => {
                    window.location.href = 'auth/login.html?redirect=customer/orders.html';
                }, 400);
            }
            return false;
        }
        window.location.href = 'customer/orders.html';
        return false;
    }

    function handleProfileNavigation(e) {
        if (e) e.preventDefault();
        if (!isCustomerAuthenticated()) {
            showToast('Please sign in to access your profile and preferences.', 'info');
            const authModalEl = document.getElementById('authModal');
            if (authModalEl && window.bootstrap) {
                authModalEl.dataset.redirect = 'customer/profile.html';
                switchAuthTab('login');
                const modal = bootstrap.Modal.getInstance(authModalEl) || new bootstrap.Modal(authModalEl);
                modal.show();
            } else {
                setTimeout(() => {
                    window.location.href = 'auth/login.html?redirect=customer/profile.html';
                }, 400);
            }
            return false;
        }
        window.location.href = 'customer/profile.html';
        return false;
    }

    // ── 12. Checkout & Order Placement Flow ──
    function initiateCheckout() {
        if (cart.length === 0) {
            showToast('Your shopping bag is empty! Add items first.', 'warning');
            return;
        }

        // Close cart offcanvas if open
        const offcanvasEl = document.getElementById('cartOffcanvas');
        if (offcanvasEl && window.bootstrap) {
            const offcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
            if (offcanvas) offcanvas.hide();
        }

        if (!isCustomerAuthenticated()) {
            showToast('Please sign in with your customer account to proceed to checkout.', 'info');
            setTimeout(() => {
                window.location.href = 'auth/login.html?redirect=customer/checkout.html';
            }, 600);
            return;
        }

        window.location.href = 'customer/checkout.html';
    }

    function placeOrder() {
        const orderId = 'EGM-' + Math.floor(100000 + Math.random() * 900000);

        // Hide checkout modal
        const checkoutModalEl = document.getElementById('checkoutModal');
        if (checkoutModalEl && window.bootstrap) {
            const modal = bootstrap.Modal.getInstance(checkoutModalEl);
            if (modal) modal.hide();
        }

        // Update Success Modal Elements
        const orderIdDisplay = document.getElementById('confirmedOrderId');
        if (orderIdDisplay) orderIdDisplay.innerText = '#' + orderId;

        // Clear cart
        cart = [];
        saveCart();

        // Show Success Modal
        if (window.bootstrap) {
            const successModal = new bootstrap.Modal(document.getElementById('orderSuccessModal'));
            successModal.show();
        }
        showToast('Order confirmed successfully!', 'success');
    }

    // ── 13. Newsletter Subscription ──
    function subscribeNewsletter(event) {
        if (event) event.preventDefault();
        const input = document.getElementById('newsletterEmailInput');
        if (!input || !input.value.includes('@')) {
            showToast('Please enter a valid email address.', 'warning');
            return;
        }
        showToast('Thank you for subscribing! Check your inbox for exclusive grocery offers.', 'success');
        input.value = '';
    }

    // ── 14. Best Sellers Carousel Scrolling ──
    function scrollBestsellers(direction) {
        const container = document.getElementById('bestsellersGrid');
        if (!container) return;
        const scrollAmount = 320;
        container.scrollBy({ left: direction * scrollAmount, behavior: 'smooth' });
    }

    // ── 15. Cross-Project Route Resolver ──
    function navigateTo(route) {
        window.location.href = route;
    }

    // ── 16. Toast Notifications ──
    function showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        const icon = type === 'success' ? 'bi-check-circle-fill' : (type === 'danger' ? 'bi-exclamation-triangle-fill' : 'bi-info-circle-fill');
        const bgClass = type === 'success' ? 'bg-success' : (type === 'danger' ? 'bg-danger' : 'bg-primary');

        toast.className = `toast align-items-center text-white ${bgClass} border-0 show shadow-lg mb-2`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex p-2 px-3">
                <div class="toast-body d-flex align-items-center gap-2">
                    <i class="bi ${icon} fs-6"></i>
                    <span>${message}</span>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3500);
    }

    // ── 17. Backend Live API Synchronization ──
    async function loadCatalogFromBackend() {
        try {
            const res = await (window.apiFetch || fetch)('/api/products?per_page=50');
            if (res.ok) {
                const data = await res.json();
                if (data && data.products && data.products.length > 0) {
                    const realList = data.products.map(p => {
                        const mrpVal = p.cost_price ? Math.round(p.cost_price * 1.25) : Math.round(p.selling_price * 1.15);
                        const discPct = mrpVal > p.selling_price ? Math.round(((mrpVal - p.selling_price) / mrpVal) * 100) : 10;
                        return {
                            id: p.id,
                            name: p.name,
                            category: p.category || 'Grocery',
                            price: Math.round(p.selling_price),
                            mrp: mrpVal,
                            discount: `${discPct}% OFF`,
                            unit: p.name.match(/\d+\s*(?:kg|g|L|ml|Dozen)/i)?.[0] || '1 unit',
                            rating: p.average_rating ? Number(p.average_rating.toFixed(1)) : 4.6,
                            reviews: p.reviews_count ? `${p.reviews_count * 100}+` : '1.2k',
                            image: p.image_path || 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=400&q=80',
                            inStock: p.stock_quantity > 0
                        };
                    });

                    DEALS_PRODUCTS = realList.slice(0, 6);
                    BESTSELLER_PRODUCTS = realList.length > 6 ? realList.slice(6, 12) : realList.slice(0, 6);
                    ALL_PRODUCTS = realList;
                    renderProductGrids();
                }
            }
        } catch (e) {
            // Standalone / offline mode
        }
    }

    async function syncCartFromBackend() {
        try {
            const res = await (window.apiFetch || fetch)('/api/cart');
            if (res.ok) {
                const data = await res.json();
                if (data && data.items && data.items.length > 0) {
                    data.items.forEach(bItem => {
                        const existing = cart.find(c => String(c.id) === String(bItem.product_id));
                        if (!existing) {
                            cart.push({
                                id: bItem.product_id,
                                name: bItem.product_name,
                                price: Math.round(bItem.product_price),
                                mrp: Math.round(bItem.product_price * 1.15),
                                unit: bItem.product_name.match(/\d+\s*(?:kg|g|L|ml|Dozen)/i)?.[0] || '1 unit',
                                quantity: bItem.quantity,
                                image: bItem.product_image || 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=400&q=80'
                            });
                        }
                    });
                    saveCart();
                }
            }
        } catch (e) {
            // Standalone mode
        }
    }

    // ── 18. Authentication State Synchronization ──
    async function checkAuthState() {
        const accountBtn = document.getElementById('headerAccountBtn');
        const accountText = document.getElementById('accountBtnText');
        const dropdownMenu = document.getElementById('headerAccountDropdownMenu');
        const dropdownUserName = document.getElementById('headerDropdownUserName');
        const dropdownUserEmail = document.getElementById('headerDropdownUserEmail');
        const subnavAuth = document.getElementById('subnavAuthLink');

        function applyUnauthenticatedState() {
            if (accountText) accountText.innerText = 'Login';
            if (accountBtn) {
                accountBtn.title = 'Login';
                accountBtn.setAttribute('data-bs-toggle', 'modal');
                accountBtn.setAttribute('data-bs-target', '#authModal');
                accountBtn.classList.remove('dropdown-toggle');
                accountBtn.removeAttribute('aria-expanded');
            }
            if (dropdownMenu) {
                dropdownMenu.style.display = 'none';
            }
            if (subnavAuth) {
                subnavAuth.innerHTML = '<i class="bi bi-box-arrow-in-right me-1"></i>Sign In';
                subnavAuth.setAttribute('href', 'auth/login.html');
                subnavAuth.onclick = null;
            }
        }

        function applyAuthenticatedState(user) {
            const displayName = user.full_name || user.name || user.username || 'Account';
            const firstName = displayName.split(' ')[0];
            if (accountText) accountText.innerText = firstName;
            if (accountBtn) {
                accountBtn.title = `Signed in as ${user.email || user.username}`;
                accountBtn.setAttribute('data-bs-toggle', 'dropdown');
                accountBtn.removeAttribute('data-bs-target');
                accountBtn.classList.add('dropdown-toggle');
            }
            if (dropdownMenu) {
                dropdownMenu.style.display = '';
            }
            if (dropdownUserName) {
                dropdownUserName.textContent = displayName;
            }
            if (dropdownUserEmail) {
                dropdownUserEmail.textContent = user.email || user.username || '';
            }
            if (subnavAuth) {
                subnavAuth.innerHTML = '<i class="bi bi-box-arrow-right me-1"></i>Sign Out';
                subnavAuth.setAttribute('href', 'javascript:void(0)');
                subnavAuth.onclick = (e) => {
                    e.preventDefault();
                    handleLogout();
                };
            }
        }

        // 1. Initial render from localStorage cache
        const authDataStr = localStorage.getItem('jg_auth_user');
        if (authDataStr) {
            try {
                const cachedUser = JSON.parse(authDataStr);
                if (cachedUser && cachedUser.role === 'customer') {
                    applyAuthenticatedState(cachedUser);
                } else {
                    applyUnauthenticatedState();
                }
            } catch (e) {
                applyUnauthenticatedState();
            }
        } else {
            applyUnauthenticatedState();
        }

        // 2. Dynamic live session verification with backend
        try {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/auth/me');
            if (res.ok) {
                const data = await res.json();
                if (data && data.authenticated && data.user && data.user.role === 'customer') {
                    const u = data.user;
                    const sessionUser = {
                        id: u.id,
                        name: u.full_name || u.name || u.username,
                        username: u.username,
                        email: u.email,
                        phone: u.phone,
                        role: 'customer'
                    };
                    localStorage.setItem('jg_auth_user', JSON.stringify(sessionUser));
                    applyAuthenticatedState(sessionUser);
                    return;
                } else {
                    const local = JSON.parse(localStorage.getItem('jg_auth_user') || 'null');
                    if (local && local.role !== 'admin') {
                        localStorage.removeItem('jg_auth_user');
                    }
                    applyUnauthenticatedState();
                }
            } else if (res.status === 401) {
                const local = JSON.parse(localStorage.getItem('jg_auth_user') || 'null');
                if (local && local.role !== 'admin') {
                    localStorage.removeItem('jg_auth_user');
                }
                applyUnauthenticatedState();
            }
        } catch (e) {
            // Backend network deferred
        }
    }

    function switchAuthTab(tab) {
        const loginPane = document.getElementById('authLoginPane');
        const registerPane = document.getElementById('authRegisterPane');
        const forgotPane = document.getElementById('authForgotPane');

        const tabLoginBtn = document.getElementById('tabLoginBtn');
        const tabRegisterBtn = document.getElementById('tabRegisterBtn');

        if (loginPane) loginPane.style.display = 'none';
        if (registerPane) registerPane.style.display = 'none';
        if (forgotPane) forgotPane.style.display = 'none';

        if (tabLoginBtn) tabLoginBtn.classList.remove('active');
        if (tabRegisterBtn) tabRegisterBtn.classList.remove('active');

        if (tab === 'login') {
            if (loginPane) loginPane.style.display = 'block';
            if (tabLoginBtn) tabLoginBtn.classList.add('active');
        } else if (tab === 'register') {
            if (registerPane) registerPane.style.display = 'block';
            if (tabRegisterBtn) tabRegisterBtn.classList.add('active');
        } else if (tab === 'forgot') {
            if (forgotPane) forgotPane.style.display = 'block';
        }
    }

    function togglePasswordVisibility(fieldId, iconId) {
        const input = document.getElementById(fieldId);
        const icon = document.getElementById(iconId);
        if (!input) return;

        if (input.type === 'password') {
            input.type = 'text';
            if (icon) {
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            }
        } else {
            input.type = 'password';
            if (icon) {
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        }
    }


    function resolveRedirectDestination(role, redirectTarget) {
        const path = window.location.pathname.toLowerCase();
        const isInAuthDir = path.includes('/auth/') || path.endsWith('/auth');
        const isStorefrontHome = !isInAuthDir && (path.endsWith('index.html') || path.endsWith('/') || path === '' || !path.includes('/customer/'));

        if (role === 'admin') {
            if (redirectTarget && (redirectTarget.includes('admin/') || redirectTarget.endsWith('.html'))) {
                const clean = redirectTarget.replace(/^\.\.\//, '').replace(/^admin\//, '');
                return isInAuthDir ? `../admin/${clean}` : `admin/${clean}`;
            }
            return isInAuthDir ? '../admin/index.html' : 'admin/index.html';
        }

        // Customer role:
        if (redirectTarget) {
            if (redirectTarget.includes('admin/')) {
                return isInAuthDir ? '../customer/shop.html' : 'customer/shop.html';
            }
            if (redirectTarget === 'index.html' || redirectTarget === '/' || redirectTarget.endsWith('index.html')) {
                return isInAuthDir ? '../index.html' : 'index.html';
            }
            const clean = redirectTarget.replace(/^\.\.\//, '').replace(/^customer\//, '');
            return isInAuthDir ? `../customer/${clean}` : `customer/${clean}`;
        }

        // No explicit redirect target
        if (isStorefrontHome) {
            return 'stay';
        }
        return isInAuthDir ? '../customer/shop.html' : 'customer/shop.html';
    }

    /**
     * Unified Login Handler
     * Seamlessly logs in customers and administrators through a single form,
     * automatically routing to Admin ERP or Customer Shop based on authenticated role.
     */
    async function handleLogin(e) {
        if (e) e.preventDefault();
        const loginInput = document.getElementById('loginEmail');
        const passwordInput = document.getElementById('loginPassword');
        const feedback = document.getElementById('loginFeedback');
        const rememberInput = document.getElementById('rememberMe');

        const credential = loginInput?.value?.trim() || '';
        const password = passwordInput?.value || '';
        const remember = rememberInput ? rememberInput.checked : true;

        if (!credential || !password) {
            if (feedback) feedback.innerHTML = '<div class="alert alert-danger py-2 small mb-3">Please enter your email/username and password.</div>';
            return;
        }

        if (feedback) feedback.innerHTML = '<div class="alert alert-info py-2 small mb-3"><span class="spinner-border spinner-border-sm me-2"></span>Signing in...</div>';

        try {
            const res = await (window.apiFetch || fetch)('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email_or_username: credential,
                    username: credential,
                    email: credential,
                    password: password,
                    remember: remember
                })
            });
            const data = await res.json().catch(() => ({}));

            if (res.ok && data.success) {
                if (data.requires_2fa) {
                    if (feedback) feedback.innerHTML = '<div class="alert alert-warning py-2 small mb-3">Two-factor authentication code required.</div>';
                    return;
                }

                const user = data.user || {};
                const sessionUser = {
                    id: user.id || 1,
                    name: user.full_name || user.name || user.username || credential.split('@')[0],
                    email: user.email || credential,
                    role: user.role || 'customer'
                };
                localStorage.setItem('jg_auth_user', JSON.stringify(sessionUser));

                showToast(`Welcome back, ${sessionUser.name}!`, 'success');

                // Resolve intended redirect destination if provided
                const urlParams = new URLSearchParams(window.location.search);
                const modalRedirect = document.getElementById('authModal')?.dataset?.redirect;
                const redirectTarget = urlParams.get('redirect') || modalRedirect || null;
                const finalDest = resolveRedirectDestination(sessionUser.role, redirectTarget);

                if (finalDest === 'stay') {
                    const authModalEl = document.getElementById('authModal');
                    if (authModalEl && window.bootstrap) {
                        delete authModalEl.dataset.redirect;
                        const modal = bootstrap.Modal.getInstance(authModalEl);
                        if (modal) modal.hide();
                    }
                    checkAuthState();
                    if (window.EG && window.EG.auth) {
                        window.EG.auth.setUser(sessionUser);
                    }
                    syncCartFromBackend();
                    return;
                }

                setTimeout(() => {
                    window.location.href = finalDest;
                }, 500);
                return;
            } else {
                const errorMsg = data.message || 'Invalid email/username or password. Please try again.';
                if (feedback) feedback.innerHTML = `<div class="alert alert-danger py-2 small mb-3">${escapeHTML(errorMsg)}</div>`;
                return;
            }
        } catch (err) {
            console.warn('Login network error:', err);
            if (feedback) feedback.innerHTML = '<div class="alert alert-warning py-2 small mb-3">Backend server unavailable. Please ensure backend is running on port 5000.</div>';
            return;
        }
    }

    const handleCustomerLogin = handleLogin;

    async function handleCustomerRegister(e) {
        if (e) e.preventDefault();
        const name = document.getElementById('regName')?.value.trim();
        const email = document.getElementById('regEmail')?.value.trim();
        const phone = document.getElementById('regPhone')?.value.trim();
        const password = document.getElementById('regPassword')?.value;
        const confirmPass = document.getElementById('regConfirmPassword')?.value;
        const feedback = document.getElementById('registerFeedback');

        if (!name || !email || !password) {
            if (feedback) feedback.innerHTML = '<div class="alert alert-danger py-2 small mb-3">Please fill out all required fields.</div>';
            return;
        }

        if (password !== confirmPass) {
            if (feedback) feedback.innerHTML = '<div class="alert alert-danger py-2 small mb-3">Passwords do not match.</div>';
            return;
        }

        if (feedback) feedback.innerHTML = '<div class="alert alert-info py-2 small mb-3"><span class="spinner-border spinner-border-sm me-2"></span>Creating your account...</div>';

        // Attempt live API register
        try {
            const res = await (window.apiFetch || fetch)('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: email.split('@')[0], full_name: name, name: name, email: email, phone: phone, password: password })
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.success) {
                const sessionUser = { id: data.user?.id || Date.now(), name: name, email: email, phone: phone, role: 'customer' };
                localStorage.setItem('jg_auth_user', JSON.stringify(sessionUser));
                showToast(`Welcome to e Grossary, ${name}!`, 'success');

                const urlParams = new URLSearchParams(window.location.search);
                const modalRedirect = document.getElementById('authModal')?.dataset?.redirect;
                const redirectTarget = urlParams.get('redirect') || modalRedirect || null;
                const targetDest = resolveRedirectDestination(sessionUser.role, redirectTarget);

                if (targetDest === 'stay') {
                    const authModalEl = document.getElementById('authModal');
                    if (authModalEl && window.bootstrap) {
                        delete authModalEl.dataset.redirect;
                        const modal = bootstrap.Modal.getInstance(authModalEl);
                        if (modal) modal.hide();
                    }
                    checkAuthState();
                    if (window.EG && window.EG.auth) {
                        window.EG.auth.setUser(sessionUser);
                    }
                    syncCartFromBackend();
                    return;
                }

                setTimeout(() => { window.location.href = targetDest; }, 600);
                return;
            } else {
                if (feedback) feedback.innerHTML = `<div class="alert alert-danger py-2 small mb-3">${escapeHTML(data.message || 'Registration failed.')}</div>`;
                return;
            }
        } catch (err) {
            console.warn('Live register error:', err);
            if (feedback) feedback.innerHTML = `<div class="alert alert-warning py-2 small mb-3">Backend server unavailable. Please try again shortly.</div>`;
            return;
        }
    }


    function handleForgotPassword(e) {
        if (e) e.preventDefault();
        const email = document.getElementById('forgotEmail')?.value.trim();
        const feedback = document.getElementById('forgotFeedback');

        if (!email) {
            if (feedback) feedback.innerHTML = '<div class="alert alert-danger py-2 small mb-3">Please enter your registered email.</div>';
            return;
        }

        if (feedback) {
            feedback.innerHTML = '<div class="alert alert-success py-2 small mb-3">Password reset instructions have been sent to <strong>' + escapeHTML(email) + '</strong>. Check your inbox!</div>';
        }
        showToast('Reset email sent!', 'info');
    }

    async function handleLogout() {
        try {
            await (window.apiFetch || fetch)('/api/auth/logout', { method: 'POST' }).catch(() => {});
        } catch (e) {}
        try {
            localStorage.removeItem('jg_auth_user');
            localStorage.removeItem('jg_admin_token');
            localStorage.removeItem('egm_cart');
            localStorage.removeItem('jg_cart');
            localStorage.removeItem('jg_coupon');
            sessionStorage.clear();
        } catch (e) {}
        showToast('You have been signed out.', 'info');
        setTimeout(() => {
            location.href = 'index.html#login';
        }, 400);
    }

    // ── 19. Initialization ──
    document.addEventListener('DOMContentLoaded', () => {
        loadState();
        renderProductGrids();
        updateCartUI();
        updateWishlistUI();
        initCountdown();
        loadCatalogFromBackend();
        syncCartFromBackend();
        checkAuthState();

        // Check URL hash for direct auth navigation
        if (window.location.hash === '#login' || window.location.hash === '#signin') {
            const authModal = new bootstrap.Modal(document.getElementById('authModal'));
            switchAuthTab('login');
            authModal.show();
        } else if (window.location.hash === '#register' || window.location.hash === '#signup') {
            const authModal = new bootstrap.Modal(document.getElementById('authModal'));
            switchAuthTab('register');
            authModal.show();
        }

        // Close search dropdown on click outside
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('searchDropdown');
            const searchWrap = document.querySelector('.search-form-wrapper');
            if (dropdown && searchWrap && !searchWrap.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        // Set initial location text
        const locLabel = document.getElementById('headerDeliveryLocation');
        if (locLabel) locLabel.innerText = currentDeliveryLocation;
        const ribbonLoc = document.getElementById('ribbonLocation');
        if (ribbonLoc) ribbonLoc.innerText = currentDeliveryLocation;
    });

    // Expose necessary functions to window for HTML event handlers
    window.PRODUCTS = ALL_PRODUCTS;
    window.addToCart = addToCart;
    window.updateItemQuantity = updateItemQuantity;
    window.removeCartItem = removeCartItem;
    window.applyCouponCode = applyCouponCode;
    window.handleLiveSearch = handleLiveSearch;
    window.triggerSearch = triggerSearch;
    window.selectSearchResult = selectSearchResult;
    window.filterByCategory = filterByCategory;
    window.toggleWishlist = toggleWishlist;
    window.setDeliveryLocation = setDeliveryLocation;
    window.openQuickView = openQuickView;
    window.initiateCheckout = initiateCheckout;
    window.handleCheckoutNavigation = handleCheckoutNavigation;
    window.handleWishlistNavigation = handleWishlistNavigation;
    window.handleOrdersNavigation = handleOrdersNavigation;
    window.handleProfileNavigation = handleProfileNavigation;
    window.resolveRedirectDestination = resolveRedirectDestination;
    window.isCustomerAuthenticated = isCustomerAuthenticated;
    window.placeOrder = placeOrder;
    window.subscribeNewsletter = subscribeNewsletter;
    window.scrollBestsellers = scrollBestsellers;
    window.navigateTo = navigateTo;
    window.showToast = showToast;
    window.loadCatalogFromBackend = loadCatalogFromBackend;
    window.syncCartFromBackend = syncCartFromBackend;

    // Expose Auth Suite methods
    window.switchAuthTab = switchAuthTab;
    window.togglePasswordVisibility = togglePasswordVisibility;
    window.handleLogin = handleLogin;
    window.handleCustomerLogin = handleCustomerLogin;
    window.handleCustomerRegister = handleCustomerRegister;
    window.handleForgotPassword = handleForgotPassword;
    window.handleLogout = handleLogout;
    window.checkAuthState = checkAuthState;
})();

