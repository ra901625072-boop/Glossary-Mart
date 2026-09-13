from flask import jsonify, request, redirect, url_for, session
from flask_login import current_user

def init_hooks(app):
    """Register application hooks"""
    
    @app.before_request
    def enforce_session_lifecycles():
        """Enforce 30-day persistent session for customers and strict timeout for admins."""
        session.permanent = True

        if current_user.is_authenticated:
            import time
            from flask_login import logout_user

            if getattr(current_user, 'role', None) == 'customer':
                login_time = session.get('login_time')
                if not login_time:
                    session['login_time'] = time.time()
                else:
                    max_customer_seconds = app.config.get('CUSTOMER_SESSION_DAYS', 30) * 86400
                    if (time.time() - float(login_time)) > max_customer_seconds:
                        logout_user()
                        session.clear()
                        if request.path.startswith('/api/') or request.is_json:
                            return jsonify({
                                'success': False,
                                'authenticated': False,
                                'user': None,
                                'message': 'Customer session expired after 30 days. Please log in again.'
                            }), 401
                        return redirect(url_for('auth.customer_login'))
            elif getattr(current_user, 'role', None) in ('admin', 'manager'):
                admin_timeout = app.config.get('ADMIN_SESSION_TIMEOUT_MINUTES', 60) * 60
                last_active = session.get('last_active')
                now = time.time()
                if last_active and (now - float(last_active) > admin_timeout):
                    logout_user()
                    session.clear()
                    if request.path.startswith('/api/') or request.is_json:
                        return jsonify({
                            'success': False,
                            'authenticated': False,
                            'message': 'Admin session timed out. Please sign in again.'
                        }), 401
                    return redirect(url_for('auth.login'))
                session['last_active'] = now

    @app.before_request
    def restrict_public_routes():
        """Only allow landing, auth, and security pages for anonymous users."""
        if current_user.is_authenticated:
            return None

        # Pass through OPTIONS requests for CORS preflight immediately
        if request.method == 'OPTIONS':
            return None

        # Allow public storefront and consolidated master portals directly
        if request.path in [
            '/', '/index.html',
            '/customer', '/customer.html',
            '/admin', '/admin.html',
            '/admin/console', '/admin/erp', '/admin/master',
            '/health', '/favicon.ico'
        ]:
            return None

        # REST API endpoints manage their own authentication and return JSON, never HTML 302 redirects
        if request.path.startswith('/api/') or (request.endpoint and request.endpoint.startswith('api.')):
            return None

        allowed_endpoints = {
            'customer.index',
            'customer.customer_portal',
            'customer.admin_html',
            'customer.api_portal',
            'admin.admin_erp_console',
            'admin.admin_base',
            'auth.customer_login',
            'auth.customer_login_redirect',
            'auth.customer_register',
            'auth.customer_register_redirect',
            'auth.login',
            'security.verify_email',
            'security.forgot_password',
            'security.reset_password',
            'security.verify_2fa',
            'static',
            'health_check',
        }

        if request.endpoint and request.endpoint not in allowed_endpoints:
            if (
                request.is_json
                or request.path.startswith('/api/')
                or '/api/' in request.path
                or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or 'application/json' in request.headers.get('Accept', '')
            ):
                return jsonify({'success': False, 'message': 'Authentication required.'}), 401
            return redirect(url_for('auth.customer_login'))


    @app.after_request
    def set_security_headers(response):
        """Attach security headers to every response."""
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net js.stripe.com; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
            "font-src 'self' fonts.gstatic.com cdn.jsdelivr.net; "
            "img-src 'self' data: blob: https://images.unsplash.com https://*.s3.amazonaws.com https://cdn.jsdelivr.net https://api.qrserver.com; "
            "connect-src 'self' api.stripe.com https://api.stripe.com; "
            "frame-src js.stripe.com; "
            "frame-ancestors 'self'; "
            "base-uri 'self';"
        )
        if not app.debug and not app.testing:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
