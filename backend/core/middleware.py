from werkzeug.middleware.proxy_fix import ProxyFix

def init_middleware(app):
    """Apply WSGI middleware"""
    # Apply ProxyFix for production (important for Render/Heroku)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
