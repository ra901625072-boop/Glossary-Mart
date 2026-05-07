from flask import Blueprint

# Initialize blueprints
auth_bp = Blueprint("auth", __name__)
admin_bp = Blueprint("admin", __name__)
customer_bp = Blueprint("customer", __name__)

# Import route modules to register all @route decorators onto the blueprints above
from routes import admin, auth, customer  # noqa: F401, E402
