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


@admin_bp.route('/coupons/add', methods=['POST'])
@admin_required
def add_coupon():
    """Create a new discount voucher."""
    from flask import request
    data = request.get_json(silent=True) or request.form
    code = (data.get('code') or '').strip().upper()
    if not code:
        return jsonify({'success': False, 'message': 'Coupon code is required.'}), 400

    if db.session.query(Coupon).filter_by(code=code).first():
        return jsonify({'success': False, 'message': f'Coupon "{code}" already exists.'}), 400

    try:
        val = float(data.get('value', 0) or data.get('discount_value', 0))
        min_spend = float(data.get('min_order_amount', 0) or data.get('min_spend', 0))
        limit = int(data.get('usage_limit', 100) or data.get('max_uses', 100))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid numeric values.'}), 400

    disc_type = str(data.get('discount_type', 'percentage')).lower()

    coupon = Coupon(
        code=code,
        discount_type=disc_type,
        value=val,
        min_order_amount=min_spend,
        usage_limit=limit,
        is_active=True
    )
    db.session.add(coupon)
    db.session.commit()

    return jsonify({'success': True, 'message': f'Coupon "{code}" created successfully!', 'id': coupon.id})


@admin_bp.route('/coupons/<int:coupon_id>/toggle', methods=['POST'])
@admin_required
def toggle_coupon(coupon_id):
    """Toggle coupon active status."""
    coupon = db.session.get(Coupon, coupon_id)
    if not coupon:
        return jsonify({'success': False, 'message': 'Coupon not found.'}), 404

    coupon.is_active = not coupon.is_active
    db.session.commit()
    return jsonify({
        'success': True,
        'message': f"Coupon '{coupon.code}' is now {'Active' if coupon.is_active else 'Inactive'}.",
        'is_active': coupon.is_active
    })

