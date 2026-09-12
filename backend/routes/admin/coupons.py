"""Admin coupon management route."""
from flask import jsonify

from database.models import db
from database.models.promotion import Coupon
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/coupons')
@admin_required
def coupons():
    """List all discount coupons — returns JSON."""
    coupons_list = db.session.query(Coupon).order_by(Coupon.created_at.desc()).all()
    return jsonify({
        'coupons': [
            {
                'id': c.id,
                'code': c.code,
                'discount_type': c.discount_type,
                'discount_value': float(c.discount_value),
                'min_order_amount': float(c.min_order_amount) if c.min_order_amount else 0,
                'max_uses': c.max_uses,
                'used_count': c.used_count,
                'is_active': c.is_active,
                'expires_at': c.expires_at.isoformat() if c.expires_at else None,
                'created_at': c.created_at.isoformat() if c.created_at else None,
            }
            for c in coupons_list
        ]
    })
