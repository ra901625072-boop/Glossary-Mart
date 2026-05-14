from flask import request, redirect, url_for, session
from flask_login import current_user

def init_hooks(app):
    """Register application hooks"""
    
    @app.before_request
    def make_session_permanent():
        """Enable permanent sessions so the 30-min timeout in config applies."""
        session.permanent = True

    @app.before_request
    def restrict_public_routes():
        """Only allow landing, auth, and security pages for anonymous users."""
        if current_user.is_authenticated:
            return None

        allowed_endpoints = {
            'customer.index',
            'auth.customer_login',
            'auth.customer_register',
            'auth.login',
            'security.verify_email',
            'security.forgot_password',
            'security.reset_password',
            'security.verify_2fa',
            'static',
            'health_check',
        }

        if request.endpoint and request.endpoint not in allowed_endpoints:
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
            "img-src 'self' data: blob: *; "
            "connect-src 'self' api.stripe.com; "
            "frame-src js.stripe.com;"
        )
        return response
