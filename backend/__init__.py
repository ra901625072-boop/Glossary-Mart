import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from flask import Flask

from .config import Config
from .extensions import cors, csrf, limiter, login_manager, mail, migrate
from .core.middleware import init_middleware
from .core.hooks import init_hooks
from database.models import db, User


def create_app(config_class=Config):
    """Application factory — single entry point for all environments."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    backend_template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    static_dir = os.path.join(project_root, 'frontend', 'static')

    app = Flask(
        __name__,
        template_folder=backend_template_dir,
        static_folder=None
    )

    import jinja2
    # Jinja2 is only needed for email templates now (backend/templates/emails/)
    app.jinja_loader = jinja2.FileSystemLoader([backend_template_dir])

    app.config.from_object(config_class)

    # Validate critical config (raises RuntimeError in production if misconfigured)
    config_class.validate(app)

    # Configure Logging
    setup_logging(app)

    # Initialize Extensions
    db.init_app(app)
    cors.init_app(
        app,
        resources={
            r"/api/*": {"origins": app.config.get("CORS_ALLOWED_ORIGINS", "*")},
            r"/static/uploads/*": {"origins": app.config.get("CORS_ALLOWED_ORIGINS", "*")},
            r"/auth/*": {"origins": app.config.get("CORS_ALLOWED_ORIGINS", "*")},
            r"/health": {"origins": "*"},
            r"/": {"origins": "*"}
        },
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "X-CSRF-Token"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        expose_headers=["Content-Length", "Content-Type", "Set-Cookie"]
    )
    csrf.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db, directory=os.path.join(project_root, "database", "migrations"))
    limiter.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.customer_login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Initialize Core Components
    init_middleware(app)
    init_hooks(app)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register Blueprints
    register_blueprints(app)

    # Health Check Route — returns clean JSON backend status
    @app.route('/health')
    def health_check():
        return {
            "status": "online",
            "message": "e Grossary API Backend is running. Frontend is hosted separately on Vercel."
        }, 200

    # Favicon for browser requests on backend port
    @app.route('/favicon.ico')
    def favicon_route():
        return '', 204

    # Serve Uploaded Product Files exclusively
    @app.route('/static/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app


def setup_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        # Stream to stdout for production (Render/Docker)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)

        # Rotating File Handler
        if not os.path.exists('logs'):
            try:
                os.mkdir('logs')
            except OSError:
                pass
        
        if os.path.exists('logs'):
            file_handler = RotatingFileHandler('logs/mart.log', maxBytes=1024 * 1024, backupCount=5, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('e Grossary startup')

def register_blueprints(app):
    """Register application blueprints"""
    from .routes import admin_bp, auth_bp, customer_bp
    from .routes.security import security_bp
    from .routes.api import api_bp

    # Exempt REST API from CSRF protection for cross-origin / decoupled frontend requests
    csrf.exempt(api_bp)

    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(security_bp)


def init_db(app):
    """Initialize database and seed data"""
    with app.app_context():
        if not app.config.get('SKIP_DB_CREATE', False):
            try:
                db.create_all()
                app.logger.info("Database tables verified/created.")
            except Exception:
                app.logger.exception("Database creation failed")
        
        try:
            from .seeds import seed_all
            seed_all(app)
        except Exception:
            app.logger.exception("Database seeding deferred")

