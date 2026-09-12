/**
 * e Grossary — Authentication & User Session Service (auth.service.js)
 * Centralized user session management, credentials storage, role validation,
 * live backend session validation, and security route guards.
 */

(function (window) {
    'use strict';

    const USER_KEY = 'jg_auth_user';

    class AuthService {
        constructor() {
            this.user = this.loadLocalUser();
        }

        loadLocalUser() {
            try {
                const raw = localStorage.getItem(USER_KEY);
                return raw ? JSON.parse(raw) : null;
            } catch (e) {
                return null;
            }
        }

        getUser() {
            return this.user;
        }

        isAuthenticated() {
            return Boolean(this.user && this.user.id);
        }

        isAdmin() {
            return Boolean(this.user && (this.user.role === 'admin' || this.user.role === 'manager'));
        }

        setUser(user) {
            this.user = user;
            try {
                if (user) {
                    localStorage.setItem(USER_KEY, JSON.stringify(user));
                } else {
                    localStorage.removeItem(USER_KEY);
                }
            } catch (e) {}
            this.syncUI();
        }

        async verifySession() {
            try {
                const fetchFn = window.apiFetch || fetch;
                const res = await fetchFn('/api/auth/me');
                if (res.ok) {
                    const data = await res.json();
                    if (data && data.authenticated && data.user) {
                        this.setUser(data.user);
                        return { authenticated: true, user: data.user };
                    } else {
                        this.setUser(null);
                        return { authenticated: false, user: null };
                    }
                } else if (res.status === 401) {
                    this.setUser(null);
                    return { authenticated: false, user: null };
                }
            } catch (e) {
                console.debug('[AuthService] Server verify session deferred:', e);
            }
            return { authenticated: Boolean(this.user && this.user.id), user: this.user };
        }

        async login(emailOrUsername, password) {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email_or_username: emailOrUsername,
                    username: emailOrUsername,
                    email: emailOrUsername,
                    password: password
                })
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.success) {
                const sessionUser = {
                    id: data.user?.id || 1,
                    name: data.user?.full_name || data.user?.name || data.user?.username || emailOrUsername.split('@')[0],
                    email: data.user?.email || emailOrUsername,
                    role: data.user?.role || 'customer'
                };
                this.setUser(sessionUser);
                return { success: true, user: sessionUser };
            }
            return { success: false, message: data.message || 'Invalid credentials' };
        }

        async register(userData) {
            const fetchFn = window.apiFetch || fetch;
            const res = await fetchFn('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.success) {
                const newUser = {
                    id: data.user?.id || Date.now(),
                    name: userData.full_name || userData.name || userData.username,
                    email: userData.email,
                    phone: userData.phone,
                    role: 'customer'
                };
                this.setUser(newUser);
                return { success: true, user: newUser };
            }
            return { success: false, message: data.message || 'Registration failed' };
        }

        async logout() {
            if (typeof window.handleLogout === 'function') {
                return window.handleLogout();
            }
            this.setUser(null);
            window.location.href = 'auth/login.html';
        }

        requireAuth(redirectUrl = '../auth/login.html') {
            if (!this.isAuthenticated()) {
                alert('Please sign in to proceed.');
                window.location.href = redirectUrl;
                return false;
            }
            return true;
        }

        requireAdmin(redirectUrl = '../auth/login.html') {
            if (!this.isAdmin()) {
                alert('Administrator privileges required. Please sign in with an authorized ERP account.');
                window.location.href = redirectUrl;
                return false;
            }
            return true;
        }

        syncUI() {
            const user = this.user;
            const isCustomer = Boolean(user && user.role === 'customer');

            if (!user || !isCustomer) {
                document.querySelectorAll('#accountBtnText').forEach(el => {
                    el.textContent = 'Login';
                });
                document.querySelectorAll('.profile-user-name-display').forEach(el => {
                    el.textContent = 'Account';
                });
                document.querySelectorAll('.profile-user-email-display').forEach(el => {
                    el.textContent = 'Sign in to sync orders';
                });
                document.querySelectorAll('.auth-guest-action').forEach(el => {
                    el.style.display = 'block';
                });
                document.querySelectorAll('.auth-customer-action').forEach(el => {
                    el.style.display = 'none';
                });
                const subnavAuth = document.getElementById('subnavAuthLink');
                if (subnavAuth) {
                    subnavAuth.innerHTML = '<i class="bi bi-box-arrow-in-right me-1"></i>Sign In';
                    subnavAuth.setAttribute('href', 'auth/login.html');
                    subnavAuth.onclick = null;
                }
                return;
            }

            // Authenticated customer: display first name on storefront button and profile dropdown
            const customerName = (user.name || user.full_name || user.username || 'Account').split(' ')[0];
            document.querySelectorAll('#accountBtnText').forEach(el => {
                el.textContent = customerName;
            });
            document.querySelectorAll('.profile-user-name-display').forEach(el => {
                el.textContent = user.name || user.full_name || user.username || 'Customer';
            });
            document.querySelectorAll('.profile-user-email-display').forEach(el => {
                el.textContent = user.email || '';
            });
            document.querySelectorAll('.auth-guest-action').forEach(el => {
                el.style.display = 'none';
            });
            document.querySelectorAll('.auth-customer-action').forEach(el => {
                el.style.display = '';
            });
            const subnavAuth = document.getElementById('subnavAuthLink');
            if (subnavAuth) {
                subnavAuth.innerHTML = '<i class="bi bi-box-arrow-right me-1"></i>Sign Out';
                subnavAuth.setAttribute('href', 'javascript:void(0)');
                subnavAuth.onclick = (e) => {
                    e.preventDefault();
                    if (typeof window.handleLogout === 'function') {
                        window.handleLogout();
                    }
                };
            }
        }
    }

    window.EG = window.EG || {};
    window.EG.auth = new AuthService();

    document.addEventListener('DOMContentLoaded', () => {
        window.EG.auth.syncUI();
        window.EG.auth.verifySession();
    });

})(window);
