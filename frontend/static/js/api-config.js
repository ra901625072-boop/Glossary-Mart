/**
 * e Grossary - Decoupled Frontend API Configuration
 * 
 * Automatically resolves backend endpoint URLs:
 * 1. In Local Development (Frontend on Port 3000 / 5500, Backend on Port 5000):
 *    Directs requests to http://127.0.0.1:5000
 * 2. In Production (Vercel -> Render):
 *    Uses relative paths handled by Vercel edge rewrites (/api/* -> Render backend)
 * 3. Supports manual override via localStorage.setItem('jg_api_base', 'http://...')
 */
(function (window) {
    'use strict';

    const hostname = window.location.hostname;
    const port = window.location.port;
    const protocol = window.location.protocol;

    const isLocalhost = Boolean(
        hostname === 'localhost' ||
        hostname === '127.0.0.1' ||
        hostname === '[::1]' ||
        protocol === 'file:'
    );

    // If running on a local frontend server (e.g. 3000, 5500, 5173, 8080) and NOT the backend port (5000),
    // target the local Flask backend on port 5000 using matching hostname.
    let defaultBase = '';
    if (isLocalhost && port !== '5000') {
        const host = hostname === '127.0.0.1' ? '127.0.0.1' : 'localhost';
        defaultBase = `http://${host}:5000`;
    }

    const API_BASE = window.API_BASE || localStorage.getItem('jg_api_base') || defaultBase;
    window.API_BASE = API_BASE;

    /**
     * Resolves an API or media path against the configured backend base URL.
     * @param {string} path - e.g. '/api/products' or '/static/uploads/apple.png'
     * @returns {string} - Fully qualified or relative URL
     */
    window.apiUrl = function (path) {
        if (!path) return '';
        if (path.startsWith('http://') || path.startsWith('https://')) return path;
        const cleanPath = path.startsWith('/') ? path : '/' + path;
        return (window.API_BASE || '') + cleanPath;
    };

    /**
     * Wrapper for window.fetch that includes credentials (cookies) and default headers.
     * @param {string} url - Target URL or endpoint path (e.g. '/api/products')
     * @param {RequestInit} [options={}] - Standard fetch options
     * @returns {Promise<Response>}
     */
    window.apiFetch = async function (url, options = {}) {
        const fullUrl = window.apiUrl(url);
        const headers = {
            'Accept': 'application/json',
            ...(options.headers || {})
        };

        let body = options.body;
        if (body && typeof body === 'object' && !(body instanceof FormData) && !(body instanceof Blob)) {
            body = JSON.stringify(body);
            if (!headers['Content-Type']) {
                headers['Content-Type'] = 'application/json';
            }
        }

        const defaultOptions = {
            credentials: 'include', // Transmit session cookies across ports
            headers: headers,
            body: body
        };
        const mergedOptions = { ...options, ...defaultOptions };

        try {
            const res = await fetch(fullUrl, mergedOptions);
            // If relative proxy /api/ call returns 404 on Vercel, fallback directly to Render backend
            if (res.status === 404 && !isLocalhost && !window.API_BASE && (url.startsWith('/api/') || url.startsWith('api/'))) {
                const cleanEndpoint = url.startsWith('/') ? url : '/' + url;
                const fallbackUrl = 'https://glossary-mart.onrender.com' + cleanEndpoint;
                const fallbackRes = await fetch(fallbackUrl, mergedOptions);
                if (fallbackRes.ok || fallbackRes.status !== 404) {
                    return fallbackRes;
                }
            }
            return res;
        } catch (err) {
            // Network error fallback if relative proxy fails entirely
            if (!isLocalhost && !window.API_BASE && (url.startsWith('/api/') || url.startsWith('api/'))) {
                const cleanEndpoint = url.startsWith('/') ? url : '/' + url;
                const fallbackUrl = 'https://glossary-mart.onrender.com' + cleanEndpoint;
                return fetch(fallbackUrl, mergedOptions);
            }
            throw err;
        }
    };

    /**
     * Convenience helper to perform JSON requests and return parsed data.
     */
    window.apiJSON = async function (url, body = null, method = 'GET') {
        const opts = { method };
        if (body) {
            opts.method = method === 'GET' ? 'POST' : method;
            opts.body = body;
        }
        const res = await window.apiFetch(url, opts);
        const data = await res.json().catch(() => ({}));
        return { ok: res.ok, status: res.status, data };
    };

    /**
     * Unified cross-app logout: terminates backend session cookie, clears all local/session storage,
     * and cleanly redirects to storefront login.
     */
    window.handleLogout = async function () {
        try {
            await window.apiFetch('/api/auth/logout', { method: 'POST' }).catch(() => {});
        } catch (e) {}
        try {
            localStorage.removeItem('jg_auth_user');
            localStorage.removeItem('jg_admin_token');
            localStorage.removeItem('egm_cart');
            localStorage.removeItem('jg_cart');
            localStorage.removeItem('jg_coupon');
            sessionStorage.clear();
        } catch (e) {}
        let target = 'auth/login.html';
        const path = window.location.pathname.toLowerCase();
        if (path.includes('/customer/') || path.includes('/admin/')) {
            target = '../auth/login.html';
        } else if (path.includes('/auth/')) {
            target = 'login.html';
        }
        window.location.href = target;
    };

    console.log(`%c[e Grossary API]%c Backend target: ${window.API_BASE || '(relative / Vercel proxy)'}`,
        'color: #10b981; font-weight: bold;', 'color: inherit;');
})(window);

