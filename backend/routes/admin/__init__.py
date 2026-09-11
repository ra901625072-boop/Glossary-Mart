"""
Admin blueprint package.

Imports all sub-modules to register their routes onto admin_bp.
"""
from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Import all sub-modules — order matters for avoiding circular imports
from . import (  # noqa: F401, E402
    dashboard,
    products,
    sales,
    orders,
    categories,
    suppliers,
    purchases,
    customers,
    pos,
    coupons,
    notifications,
    activity,
)
