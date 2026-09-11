from flask import Blueprint

# Auth and Customer blueprints — defined here (small, single-file route modules)
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
customer_bp = Blueprint("customer", __name__)

# Admin blueprint — defined in routes/admin/__init__.py (split into sub-modules)
from .admin import admin_bp  # noqa: F401, E402

# Register all route decorators onto the blueprints above
from . import auth, customer  # noqa: F401, E402
from .security import security_bp

__all__ = ['auth_bp', 'customer_bp', 'admin_bp', 'security_bp']
