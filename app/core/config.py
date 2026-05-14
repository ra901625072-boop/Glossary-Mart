import os
from datetime import timedelta

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""

    # ------------------------------------------------------------------ #
    # Core
    # ------------------------------------------------------------------ #
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    # Render provides DATABASE_URL. SQLAlchemy 1.4+ requires 'postgresql://'
    database_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URI') or 'sqlite:///store.db'
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,      # Detect stale connections
        "pool_recycle": 300,        # Recycle connections every 5 min
    }

    # Production guard: set SKIP_DB_CREATE=true in Render env vars
    # so init_db() uses Flask-Migrate only, never auto-creates tables.
    SKIP_DB_CREATE = os.getenv('SKIP_DB_CREATE', 'false').lower() == 'true'

    # ------------------------------------------------------------------ #
    # Session & Cookie Security
    # ------------------------------------------------------------------ #
    # Expire session after 30 minutes of inactivity
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.getenv('SESSION_TIMEOUT_MINUTES', 30)))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Set to True in production (requires HTTPS). Set env var: SESSION_COOKIE_SECURE=true
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

    # ------------------------------------------------------------------ #
    # Rate Limiter
    # ------------------------------------------------------------------ #
    # In production: set REDIS_URL to a Redis Cloud / Upstash URL.
    # In development: leave unset → falls back to in-memory (warning shown).
    RATELIMIT_STORAGE_URI = os.getenv('REDIS_URL', None)

    # ------------------------------------------------------------------ #
    # File Uploads
    # ------------------------------------------------------------------ #
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 5 * 1024 * 1024))  # 5MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # ------------------------------------------------------------------ #
    # Admin Credentials (seed only — override in production .env)
    # ------------------------------------------------------------------ #
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    # ------------------------------------------------------------------ #
    # Mail
    # ------------------------------------------------------------------ #
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'jaygogakiranastore@gmail.com')

    # ------------------------------------------------------------------ #
    # Payments
    # ------------------------------------------------------------------ #
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
