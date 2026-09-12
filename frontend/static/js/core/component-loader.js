/**
 * e Grossary — Lightweight Component Partial Loader (component-loader.js)
 * Automatically discovers, normalizes paths, and loads reusable HTML components
 * (customer-header, customer-footer, cart-drawer, mobile-bottom-nav, etc.).
 * Usage: <div data-component="customer-header"></div>
 */

(function (window) {
    'use strict';

    function normalizeComponentHtml(html, isSubdirectory) {
        if (isSubdirectory) {
            // Already in /customer/, /admin/, or /auth/ subdirectory
            return html;
        }

        // At root directory (e.g., /index.html or /404.html):
        // Replace relative '../static/' with 'static/'
        let normalized = html.replace(/(src|href)=["']\.\.\/static\//g, '$1="static/');

        // Replace '../index.html' with 'index.html'
        normalized = normalized.replace(/href=["']\.\.\/index\.html["']/g, 'href="index.html"');

        // Replace '../auth/' with 'auth/'
        normalized = normalized.replace(/href=["']\.\.\/auth\//g, 'href="auth/');

        // In root pages, links like href="shop.html" or href="cart.html" should point to "customer/shop.html", etc.
        const customerPages = [
            'shop.html', 'cart.html', 'checkout.html', 'product.html',
            'orders.html', 'order-confirmation.html', 'payment.html',
            'profile.html', 'wishlist.html', 'about.html', 'contact.html',
            'faq.html', 'terms.html'
        ];

        customerPages.forEach(function (page) {
            // Match href="page" or href="page?..."
            const regex = new RegExp('href=["\'](' + page.replace('.', '\\.') + '([?#][^"\']*)?)["\']', 'g');
            normalized = normalized.replace(regex, 'href="customer/$1"');
        });

        return normalized;
    }

    async function loadComponent(el) {
        const componentName = el.getAttribute('data-component');
        if (!componentName) return;

        // Resolve relative components directory based on current URL path
        let basePath = 'components/';
        const path = window.location.pathname.toLowerCase();
        const isSubdirectory = path.includes('/customer/') || path.includes('/admin/') || path.includes('/auth/');
        if (isSubdirectory) {
            basePath = '../components/';
        }

        const componentUrl = `${basePath}${componentName}.html`;

        try {
            const res = await fetch(componentUrl);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            let html = await res.text();

            html = normalizeComponentHtml(html, isSubdirectory);

            // Create temporary container to parse HTML
            const temp = document.createElement('div');
            temp.innerHTML = html;

            // Replace placeholder with component elements
            const parent = el.parentNode;
            if (!parent) return;

            const insertedNodes = [];
            while (temp.firstChild) {
                const child = temp.firstChild;
                insertedNodes.push(child);
                parent.insertBefore(child, el);
            }
            parent.removeChild(el);

            // Dispatch lifecycle event
            window.dispatchEvent(new CustomEvent('component:loaded', {
                detail: { name: componentName, elements: insertedNodes }
            }));
        } catch (err) {
            console.warn(`[ComponentLoader] Could not load component '${componentName}':`, err);
        }
    }

    async function initComponentLoader() {
        const placeholders = document.querySelectorAll('[data-component]');
        if (placeholders.length === 0) return;
        await Promise.all(Array.from(placeholders).map(loadComponent));
        window.dispatchEvent(new CustomEvent('components:all-loaded'));
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initComponentLoader);
    } else {
        initComponentLoader();
    }

    window.EG = window.EG || {};
    window.EG.loadComponent = loadComponent;
    window.EG.initComponentLoader = initComponentLoader;

})(window);
