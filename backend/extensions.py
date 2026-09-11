"""
Centralized Flask extension instances.

All extensions are created here WITHOUT an app object (init_app pattern).
They are initialized in create_app() via extension.init_app(app).

Import from here — never create extension instances elsewhere.
"""
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Rate limiter — storage_uri is injected from backend.config['RATELIMIT_STORAGE_URI'].
# In development (no REDIS_URL set) → falls back to in-memory with a warning.
# In production → set REDIS_URL env var to a Redis Cloud / Upstash URL.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=None,  # Overridden by app.config['RATELIMIT_STORAGE_URI'] at init_app()
)

csrf = CSRFProtect()
mail = Mail()
login_manager = LoginManager()
migrate = Migrate()
cors = CORS()

