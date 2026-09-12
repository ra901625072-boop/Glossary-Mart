"""Customer-facing coupon validation API routes."""
from datetime import datetime, timezone
from flask import jsonify, request

from database.models import db
from database.models.promotion import Coupon
from . import api_bp


@api_bp.route('/coupons/validate', methods=['GET', 'POST'])
def validate_coupon():
    """
    Validate discount coupon code against live database promotions.
    Accepts JSON body or query parameters:
      code: string (required, e.g. "SAVE10")
      cart_total / subtotal: float (optional cart subtotal to calculate exact savings)
    """
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
    else:
        data = request.args

    code = (data.get('code') or '').strip().upper()
    if not code:
        return jsonify({'success': False, 'message': 'Coupon code is required.'}), 400

    coupon = db.session.query(Coupon).filter_by(code=code).first()
    if not coupon:
        return jsonify({'success': False, 'message': f'Coupon "{code}" is not valid.'}), 404

    if not coupon.is_active:
        return jsonify({'success': False, 'message': f'Coupon "{code}" is currently inactive.'}), 400

    now_utc = datetime.now(timezone.utc)
    if coupon.valid_until:
        # Handle both naive and aware datetimes safely
        coupon_expiry = coupon.valid_until
        if coupon_expiry.tzinfo is None:
            coupon_expiry = coupon_expiry.replace(tzinfo=timezone.utc)
        if now_utc > coupon_expiry:
            return jsonify({'success': False, 'message': f'Coupon "{code}" has expired.'}), 400

    if coupon.usage_limit and coupon.times_used >= coupon.usage_limit:
        return jsonify({'success': False, 'message': f'Coupon "{code}" usage limit reached.'}), 400

    raw_total = data.get('cart_total') or data.get('subtotal') or data.get('total') or 0.0
    try:
        cart_total = float(raw_total)
    except (ValueError, TypeError):
        cart_total = 0.0

    min_spend = float(coupon.min_order_amount or 0.0)
    if cart_total > 0 and cart_total < min_spend:
        return jsonify({
            'success': False,
            'message': f'Coupon "{code}" requires a minimum spend of ₹{min_spend:,.2f}. (Current: ₹{cart_total:,.2f})'
        }), 400

    discount_type = str(coupon.discount_type or 'percentage').lower()
    value = float(coupon.value or 0.0)

    if discount_type in ('percentage', 'percent'):
        discount_amount = round(cart_total * (value / 100.0), 2) if cart_total > 0 else 0.0
    else:
        discount_amount = min(cart_total, value) if cart_total > 0 else value

    return jsonify({
        'success': True,
        'message': f'Coupon "{code}" applied successfully!',
        'coupon': {
            'id': coupon.id,
            'code': coupon.code,
            'discount_type': discount_type,
            'value': value,
            'min_order_amount': min_spend,
            'discount_amount': discount_amount,
            'final_total': max(0.0, round(cart_total - discount_amount, 2)) if cart_total > 0 else 0.0
        }
    }), 200
