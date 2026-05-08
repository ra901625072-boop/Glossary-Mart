from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Configure limiter to use the remote address
# In production, we'll use ProxyFix in app.py to get the real client IP
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
