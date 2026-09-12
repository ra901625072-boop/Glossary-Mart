from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Register endpoints on api_bp
from . import products, cart, auth, orders, coupons  # noqa: F401, E402

@api_bp.route("/health")
def api_health():
    """API health status"""
    return {
        "status": "online",
        "service": "e-grossary-api",
        "message": "e Grossary API Backend is running. Frontend is hosted separately on Vercel."
    }, 200

__all__ = ["api_bp"]
