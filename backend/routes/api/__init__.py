from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Register endpoints on api_bp
from . import products, cart, auth, orders  # noqa: F401, E402

@api_bp.route("/health")
def api_health():
    """API health status"""
    return {"status": "healthy", "service": "jay-goga-mart-api"}, 200

__all__ = ["api_bp"]
