/**
 * e Grossary — Shopping Cart Service (cart.service.js)
 * Centralized, reactive state management for shopping bag, qty steppers,
 * free delivery thresholds, discount coupon vouchers, and backend synchronization.
 */

(function (window) {
    'use strict';

    const STORAGE_KEY = 'egm_cart';
    const COUPON_KEY = 'egm_active_coupon';

    class CartService {
        constructor() {
            this.cart = this.loadCart();
            this.activeCoupon = this.loadCoupon();
            this.catalog = [];
        }

        loadCart() {
            try {
                const raw = localStorage.getItem(STORAGE_KEY) || localStorage.getItem('jg_cart');
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

        loadCoupon() {
            try {
                const raw = localStorage.getItem(COUPON_KEY) || localStorage.getItem('jg_coupon');
                return raw ? JSON.parse(raw) : null;
            } catch (e) {
                return null;
            }
        }

        persist() {
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(this.cart));
                // Sync legacy key for backward compatibility
                localStorage.setItem('jg_cart', JSON.stringify(this.cart));
                if (this.activeCoupon) {
                    localStorage.setItem(COUPON_KEY, JSON.stringify(this.activeCoupon));
                } else {
                    localStorage.removeItem(COUPON_KEY);
                    localStorage.removeItem('jg_coupon');
                }
            } catch (e) {}
            this.notify();
        }

        notify() {
            window.dispatchEvent(new CustomEvent('cart:updated', {
                detail: {
                    cart: this.cart,
                    totals: this.calculateTotals()
                }
            }));
            this.updateBadgeElements();
        }

        setCatalog(products) {
            if (Array.isArray(products)) {
                this.catalog = products;
            }
        }

        getItems() {
            return this.cart;
        }

        getItemCount() {
            return this.cart.reduce((sum, item) => sum + (Number(item.qty) || 0), 0);
        }

        getQty(productId) {
            const entry = this.cart.find(i => Number(i.productId) === Number(productId));
            return entry ? entry.qty : 0;
        }

        addItem(productId, qty = 1) {
            const numId = Number(productId);
            const existing = this.cart.find(i => Number(i.productId) === numId);
            if (existing) {
                existing.qty += qty;
            } else {
                this.cart.push({ productId: numId, qty: qty });
            }
            this.persist();

            // Fire-and-forget sync to live backend
            try {
                const fetchFn = window.apiFetch || fetch;
                fetchFn('/api/cart/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ product_id: numId, quantity: qty })
                }).catch(() => {});
            } catch (e) {}
        }

        updateQty(productId, delta) {
            const numId = Number(productId);
            const index = this.cart.findIndex(i => Number(i.productId) === numId);
            if (index > -1) {
                this.cart[index].qty += delta;
                if (this.cart[index].qty <= 0) {
                    this.cart.splice(index, 1);
                }
                this.persist();
            }
        }

        removeItem(productId) {
            const numId = Number(productId);
            this.cart = this.cart.filter(i => Number(i.productId) !== numId);
            this.persist();
        }

        clear() {
            this.cart = [];
            this.activeCoupon = null;
            this.persist();
        }

        applyCoupon(code) {
            const cleanCode = String(code).trim().toUpperCase();
            if (cleanCode === 'GROSSARY10' || cleanCode === 'WELCOME10') {
                this.activeCoupon = { code: cleanCode, type: 'percent', value: 10 };
                this.persist();
                return { success: true, message: `Coupon ${cleanCode} applied! 10% discount added.` };
            } else if (cleanCode === 'SUPER50' || cleanCode === 'FRESH50') {
                this.activeCoupon = { code: cleanCode, type: 'flat', value: 50 };
                this.persist();
                return { success: true, message: `Coupon ${cleanCode} applied! ₹50 instant discount added.` };
            }
            return { success: false, message: 'Invalid or expired coupon code. Try WELCOME10 or SUPER50.' };
        }

        removeCoupon() {
            this.activeCoupon = null;
            this.persist();
        }

        calculateTotals() {
            let subtotal = 0;
            let originalMrpTotal = 0;

            this.cart.forEach(item => {
                const numQty = Number(item.qty || item.quantity || 1);
                const numId = Number(item.productId || item.id || 0);
                const product = this.catalog.find(p => Number(p.id) === numId);
                const price = product ? Number(product.price) : Number(item.price || 0);
                const mrp = product ? Number(product.mrp || Math.round(price * 1.15)) : (Number(item.mrp) || Math.round(price * 1.15));

                const validPrice = isNaN(price) ? 0 : price;
                const validMrp = isNaN(mrp) ? validPrice : mrp;
                const validQty = isNaN(numQty) || numQty < 1 ? 1 : numQty;

                subtotal += validPrice * validQty;
                originalMrpTotal += validMrp * validQty;
            });

            let couponDiscount = 0;
            if (this.activeCoupon && subtotal > 0) {
                const val = Number(this.activeCoupon.value || 0);
                if (this.activeCoupon.type === 'percent') {
                    couponDiscount = Math.round((subtotal * val) / 100);
                } else {
                    couponDiscount = Math.min(val, subtotal);
                }
            }

            const deliveryFee = subtotal >= 499 || subtotal === 0 ? 0 : 29;
            const handlingFee = subtotal > 0 ? 2 : 0;
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
                freeDeliveryThreshold: 499,
                freeDeliveryRemaining: Math.max(0, 499 - subtotal),
                isFreeDelivery: subtotal >= 499
            };
        }

        updateBadgeElements() {
            const count = this.getItemCount();
            const totals = this.calculateTotals();
            const safeCount = isNaN(count) ? 0 : count;
            const safeTotal = isNaN(totals.finalTotal) ? 0 : totals.finalTotal;

            document.querySelectorAll('.cart-counter-badge, #cartCountBadge, #mobileCartBadge').forEach(el => {
                el.textContent = safeCount;
                el.style.display = safeCount > 0 ? (el.classList.contains('action-badge-pill') ? 'flex' : 'inline-flex') : 'none';
            });

            document.querySelectorAll('.cart-total-header-pill, #cartTotalHeaderPill').forEach(el => {
                el.textContent = `₹${safeTotal}`;
            });
        }
    }

    window.EG = window.EG || {};
    window.EG.cart = new CartService();

    // Initialize badges on load
    document.addEventListener('DOMContentLoaded', () => {
        window.EG.cart.updateBadgeElements();
    });

})(window);
