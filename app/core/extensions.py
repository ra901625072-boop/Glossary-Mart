from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Rate limiter — storage_uri is injected from app.config['RATELIMIT_STORAGE_URI'].
# In development (no REDIS_URL set) → falls back to in-memory with a warning.
# In production → set REDIS_URL env var to a Redis Cloud / Upstash URL
#   e.g.  REDIS_URL=redis://default:password@host:6379
# Flask-Limiter will automatically pick it up via init_app(app).
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=None,  # Overridden by app.config['RATELIMIT_STORAGE_URI'] at init_app()
)
