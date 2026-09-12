/**
 * e Grossary — Core Utilities Engine (utils.js)
 * High-performance, cross-cutting helpers for XSS sanitization, currency formatting,
 * localized dates, debouncing, toast micro-interactions, and safe storage access.
 */

(function (window) {
    'use strict';

    const Utils = {
        /**
         * Sanitizes a string against XSS injection before DOM interpolation.
         * @param {*} str - Input raw string or value
         * @returns {string} - Escaped safe HTML string
         */
        escapeHTML: function (str) {
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
        },

        /**
         * Formats a numeric value into localized Indian Rupee currency (e.g. ₹1,299).
         * @param {number|string} amount - Number to format
         * @param {boolean} [includeDecimals=false] - Whether to include 2 decimal digits
         * @returns {string} - Formatted currency string
         */
        formatINR: function (amount, includeDecimals = false) {
            const num = parseFloat(amount) || 0;
            if (!includeDecimals && Number.isInteger(num)) {
                return '₹' + num.toLocaleString('en-IN');
            }
            return '₹' + num.toLocaleString('en-IN', {
                minimumFractionDigits: includeDecimals ? 2 : 0,
                maximumFractionDigits: 2
            });
        },

        /**
         * Formats an ISO or timestamp string into human-friendly localized Indian time.
         * @param {string|number|Date} dateVal - Input date value
         * @param {Intl.DateTimeFormatOptions} [options]
         * @returns {string}
         */
        formatDate: function (dateVal, options) {
            if (!dateVal) return 'Recent';
            try {
                const date = new Date(dateVal);
                if (isNaN(date.getTime())) return String(dateVal);
                const defaultOpts = { dateStyle: 'medium', timeStyle: 'short' };
                return date.toLocaleString('en-IN', options || defaultOpts);
            } catch (e) {
                return String(dateVal);
            }
        },

        /**
         * Displays a non-intrusive floating toast notification on screen.
         * @param {string} message - Toast text to display
         * @param {'success'|'danger'|'warning'|'info'} [type='success'] - Toast theme
         * @param {number} [duration=3000] - Lifespan in milliseconds
         */
        showToast: function (message, type = 'success', duration = 3000) {
            let container = document.getElementById('toastContainer');
            if (!container) {
                container = document.createElement('aside');
                container.id = 'toastContainer';
                container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
                container.style.zIndex = '1095';
                document.body.appendChild(container);
            }

            const icons = {
                success: 'bi-check-circle-fill text-success',
                danger: 'bi-exclamation-triangle-fill text-danger',
                warning: 'bi-exclamation-circle-fill text-warning',
                info: 'bi-info-circle-fill text-primary'
            };

            const toastId = 'toast-' + Date.now();
            const toastEl = document.createElement('div');
            toastEl.id = toastId;
            toastEl.className = 'toast align-items-center show shadow-lg border-0 rounded-4 mb-2';
            toastEl.setAttribute('role', 'alert');
            toastEl.setAttribute('aria-live', 'assertive');
            toastEl.setAttribute('aria-atomic', 'true');
            toastEl.style.backgroundColor = '#ffffff';
            toastEl.style.minWidth = '280px';

            toastEl.innerHTML = `
                <div class="d-flex p-3 align-items-center">
                    <i class="bi ${icons[type] || icons.success} fs-5 me-3"></i>
                    <div class="toast-body p-0 small fw-semibold text-dark flex-grow-1">
                        ${this.escapeHTML(message)}
                    </div>
                    <button type="button" class="btn-close ms-2" onclick="document.getElementById('${toastId}').remove()" aria-label="Close"></button>
                </div>
            `;

            container.appendChild(toastEl);
            setTimeout(() => {
                if (toastEl.parentNode) {
                    toastEl.classList.remove('show');
                    setTimeout(() => toastEl.remove(), 250);
                }
            }, duration);
        },

        /**
         * Debounces function calls to prevent rapid repeated executions (e.g. search inputs).
         * @param {Function} func - Callback
         * @param {number} wait - Delay in milliseconds
         * @returns {Function}
         */
        debounce: function (func, wait = 250) {
            let timeout;
            return function (...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        },

        /**
         * Safe localStorage / sessionStorage wrappers with automatic JSON handling.
         */
        storage: {
            get: function (key, defaultVal = null, useSession = false) {
                try {
                    const store = useSession ? window.sessionStorage : window.localStorage;
                    const val = store.getItem(key);
                    return val ? JSON.parse(val) : defaultVal;
                } catch (e) {
                    return defaultVal;
                }
            },
            set: function (key, val, useSession = false) {
                try {
                    const store = useSession ? window.sessionStorage : window.localStorage;
                    store.setItem(key, JSON.stringify(val));
                    return true;
                } catch (e) {
                    return false;
                }
            },
            remove: function (key, useSession = false) {
                try {
                    const store = useSession ? window.sessionStorage : window.localStorage;
                    store.removeItem(key);
                    return true;
                } catch (e) {
                    return false;
                }
            }
        }
    };

    // Expose as global singleton
    window.EG = window.EG || {};
    window.EG.utils = Utils;

    // Backward-compatible global aliases
    window.escapeHTML = Utils.escapeHTML;
    window.showToast = Utils.showToast;
    window.formatINR = Utils.formatINR;

})(window);
