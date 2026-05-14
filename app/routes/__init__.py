from flask import Blueprint

# Initialize blueprints with professional prefixes
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
customer_bp = Blueprint("customer", __name__)

# Import route modules to register all @route decorators onto the blueprints above
from . import admin, auth, customer  # noqa: F401, E402
