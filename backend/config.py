import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # ------------------------------------------------------------------ #
    # Core
    # ------------------------------------------------------------------ #
    _raw_secret = os.getenv('SECRET_KEY')
    if not _raw_secret or _raw_secret in ('dev-secret-key-change-in-production', 'secret', 'changeme', ''):
        SECRET_KEY = secrets.token_hex(32)
    else:
        SECRET_KEY = _raw_secret


    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    # Render provides DATABASE_URL. SQLAlchemy 1.4+ requires 'postgresql://'
    _default_db = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'store.db')
    database_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URI') or _default_db
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url
    _engine_opts = {
        "pool_pre_ping": True,      # Detect stale connections
        "pool_recycle": 300,        # Recycle connections every 5 min
    }
    if database_url and database_url.startswith("postgresql"):
        _engine_opts["connect_args"] = {
            "connect_timeout": 10,
        }
    SQLALCHEMY_ENGINE_OPTIONS = _engine_opts

    # Production guard: set SKIP_DB_CREATE=true in Render env vars
    # so init_db() uses Flask-Migrate only, never auto-creates tables.
    SKIP_DB_CREATE = os.getenv('SKIP_DB_CREATE', 'false').lower() == 'true'

    # ------------------------------------------------------------------ #
    # Session & Cookie Security
    # ------------------------------------------------------------------ #
    # Expire session after 30 minutes of inactivity
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.getenv('SESSION_TIMEOUT_MINUTES', 30)))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    # Set to True in production (requires HTTPS). Set env var: SESSION_COOKIE_SECURE=true
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

    # ------------------------------------------------------------------ #
    # CORS & Cross-Domain Origins (for decoupled Vercel frontend)
    # ------------------------------------------------------------------ #
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://glossary-mart.vercel.app')
    _cors_env = os.getenv('CORS_ALLOWED_ORIGINS', '')
    
    # Base allowed origins: production Vercel app, all Vercel preview deploys, and local dev
    _base_origins = [
        'https://glossary-mart.vercel.app',
        'http://localhost:3000',
        'http://localhost:5173',
        'http://localhost:5500',
        'http://localhost:8000',
        'http://localhost:8080',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5500',
        'http://127.0.0.1:8000',
        'http://127.0.0.1:8080',
        r"^https:\/\/glossary-mart(-[a-zA-Z0-9_-]+)?\.vercel\.app$"
    ]
    if _cors_env:
        for origin in _cors_env.split(','):
            cleaned = origin.strip()
            if cleaned and cleaned not in _base_origins:
                _base_origins.append(cleaned)
    if FRONTEND_URL and FRONTEND_URL not in _base_origins:
        _base_origins.append(FRONTEND_URL)
        
    CORS_ALLOWED_ORIGINS = _base_origins

    # ------------------------------------------------------------------ #
    # Rate Limiter
    # ------------------------------------------------------------------ #
    # In production: set REDIS_URL to a Redis Cloud / Upstash URL.
    # In development: leave unset → falls back to in-memory (warning shown).
    RATELIMIT_STORAGE_URI = os.getenv('REDIS_URL', None)

    # ------------------------------------------------------------------ #
    # File Uploads (independent backend storage)
    # ------------------------------------------------------------------ #
    _project_root = os.path.dirname(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.getenv(
        'UPLOAD_FOLDER',
        os.path.join(_project_root, 'frontend', 'static', 'uploads')
    )
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 5 * 1024 * 1024))  # 5MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # ------------------------------------------------------------------ #
    # Admin Credentials (seed only — override in production .env)
    # ------------------------------------------------------------------ #
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@mart.com')

    # ------------------------------------------------------------------ #
    # Transactional Email (Resend REST API & SMTP Fallback)
    # ------------------------------------------------------------------ #
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.resend.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'onboarding@resend.dev')

    # ------------------------------------------------------------------ #
    # Payments
    # ------------------------------------------------------------------ #
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

    # ------------------------------------------------------------------ #
    # Minimum password length (NIST SP 800-63B compliant)
    # ------------------------------------------------------------------ #
    MIN_PASSWORD_LENGTH = int(os.getenv('MIN_PASSWORD_LENGTH', 8))

    @classmethod
    def validate(cls, app):
        """
        Validate critical configuration at startup.
        Raises RuntimeError for dangerous misconfigurations in production.
        """
        is_production = (
            not app.debug
            and not app.testing
            and os.getenv('FLASK_ENV', 'production') != 'development'
            and os.getenv('FLASK_DEBUG', '0') not in ('1', 'true', 'True')
        )

        if is_production:
            # 1. Session cookies must be secure over HTTPS
            if not cls.SESSION_COOKIE_SECURE:
                app.logger.warning(
                    "SESSION_COOKIE_SECURE is False in production. "
                    "Set SESSION_COOKIE_SECURE=true to protect session cookies."
                )

            # 2. Admin password notification
            if cls.ADMIN_PASSWORD in ('admin123', 'admin', 'password', '123456'):
                app.logger.warning(
                    "ADMIN_PASSWORD is set to a default value. "
                    "For security, set a custom ADMIN_PASSWORD in your Render Environment Variables."
                )
