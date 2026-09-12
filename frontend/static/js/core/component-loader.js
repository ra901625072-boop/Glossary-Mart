/**
 * e Grossary — Lightweight Component Partial Loader (component-loader.js)
 * Automatically discovers and loads reusable HTML components (e.g. headers, footers, sidebars).
 * Usage: <div data-component="customer-header"></div>
 */

(function (window) {
    'use strict';

    async function loadComponent(el) {
        const componentName = el.getAttribute('data-component');
        if (!componentName) return;

        // Resolve relative components directory based on current URL path
        let basePath = 'components/';
        const path = window.location.pathname.toLowerCase();
        if (path.includes('/customer/') || path.includes('/admin/') || path.includes('/auth/')) {
            basePath = '../components/';
        }

        const componentUrl = `${basePath}${componentName}.html`;

        try {
            const res = await fetch(componentUrl);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const html = await res.text();
            
            // Create temporary container to parse HTML
            const temp = document.createElement('div');
            temp.innerHTML = html;

            // Replace placeholder with component elements
            const parent = el.parentNode;
            while (temp.firstChild) {
                parent.insertBefore(temp.firstChild, el);
            }
            parent.removeChild(el);

            // Dispatch lifecycle event
            window.dispatchEvent(new CustomEvent('component:loaded', {
                detail: { name: componentName }
            }));
        } catch (err) {
            console.warn(`[ComponentLoader] Could not load component '${componentName}':`, err);
        }
    }

    async function initComponentLoader() {
        const placeholders = document.querySelectorAll('[data-component]');
        if (placeholders.length === 0) return;
        await Promise.all(Array.from(placeholders).map(loadComponent));
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
