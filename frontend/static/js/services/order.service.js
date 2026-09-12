/**
 * e Grossary — Orders & Checkout Service (order.service.js)
 * Centralized API integration for orders fulfillment, checkout payload dispatch,
 * live tracking status step calculations, and PDF invoice downloads.
 */

(function (window) {
    'use strict';

    const CONFIRMED_ORDER_KEY = 'egm_confirmed_order';
    const PENDING_ORDER_KEY = 'egm_pending_order';

    class OrderService {
        /**
         * Resolves delivery progress step (1 to 4) based on backend status.
         * @param {string} status - e.g. "Placed", "Packed", "Shipped", "Delivered"
         * @returns {number} - 1: Placed, 2: Packed, 3: Shipped/Out for delivery, 4: Delivered
         */
        getOrderStep(status) {
            const clean = String(status || '').toLowerCase();
            if (clean === 'delivered') return 4;
            if (clean === 'shipped' || clean.includes('out for delivery') || clean === 'dispatched') return 3;
            if (clean === 'processing' || clean === 'packed') return 2;
            return 1;
        }

        /**
         * Builds GST Tax Invoice download URL.
         * @param {number|string} orderId
         * @returns {string}
         */
        getInvoiceUrl(orderId) {
            const path = `/api/orders/${Number(orderId)}/invoice`;
            return window.apiUrl ? window.apiUrl(path) : path;
        }

        saveConfirmedOrder(order) {
            try {
                sessionStorage.setItem(CONFIRMED_ORDER_KEY, JSON.stringify(order));
            } catch (e) {}
        }

        getConfirmedOrder() {
            try {
                const raw = sessionStorage.getItem(CONFIRMED_ORDER_KEY);
                return raw ? JSON.parse(raw) : null;
            } catch (e) {
                return null;
            }
        }

        savePendingOrder(order) {
            try {
                sessionStorage.setItem(PENDING_ORDER_KEY, JSON.stringify(order));
            } catch (e) {}
        }

        getPendingOrder() {
            try {
                const raw = sessionStorage.getItem(PENDING_ORDER_KEY);
                return raw ? JSON.parse(raw) : null;
            } catch (e) {
                return null;
            }
        }

        async fetchUserOrders() {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/orders');
            if (res.status === 401) {
                return { authRequired: true, orders: [] };
            }
            if (res.ok) {
                const data = await res.json();
                return {
                    authRequired: false,
                    orders: (data && data.orders) ? data.orders : []
                };
            }
            return { authRequired: false, orders: [] };
        }

        async submitCheckout(address, paymentMethod, items) {
            const fetchFn = window.apiFetch || fetch;
            const payload = {
                shipping_address: address,
                payment_method: paymentMethod || 'COD',
                items: items.map(c => ({
                    product_id: Number(c.productId),
                    quantity: Number(c.qty)
                }))
            };

            const res = await fetchFn('/api/orders/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json().catch(() => ({}));
            return { ok: res.ok, data };
        }
    }

    window.EG = window.EG || {};
    window.EG.order = new OrderService();

})(window);
