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
        const defaultOptions = {
            credentials: 'include', // Transmit session cookies across ports
            headers: {
                'Accept': 'application/json',
                ...(options.headers || {})
            }
        };
        const mergedOptions = { ...defaultOptions, ...options };
        return fetch(fullUrl, mergedOptions);
    };

    console.log(`%c[e Grossary API]%c Backend target: ${window.API_BASE || '(relative / Vercel proxy)'}`,
        'color: #10b981; font-weight: bold;', 'color: inherit;');
})(window);
