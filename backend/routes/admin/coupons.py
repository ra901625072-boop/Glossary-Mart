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
                'discount_value': float(c.value) if c.value is not None else 0.0,
                'value': float(c.value) if c.value is not None else 0.0,
                'min_order_amount': float(c.min_order_amount) if c.min_order_amount else 0,
                'max_uses': c.usage_limit,
                'usage_limit': c.usage_limit,
                'used_count': c.times_used,
                'times_used': c.times_used,
                'is_active': c.is_active,
                'expires_at': c.valid_until.isoformat() if c.valid_until else None,
                'valid_until': c.valid_until.isoformat() if c.valid_until else None,
                'created_at': c.created_at.isoformat() if c.created_at else None,
            }
            for c in coupons_list
        ]
    })
