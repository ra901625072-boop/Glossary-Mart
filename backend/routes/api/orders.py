from flask import jsonify, request
from flask_login import current_user

from backend.extensions import limiter
from backend.services.order_service import OrderService
from database.models import db
from database.models.order import Order
from . import api_bp


@api_bp.route('/orders', methods=['GET'])
def get_orders():
    """List orders of authenticated customer"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    orders = db.session.query(Order).filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return jsonify({
        'success': True,
        'orders': [o.to_dict() for o in orders]
    }), 200


@api_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order_detail(order_id):
    """Get single order details and line items (excluding sensitive wholesale profit data)"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    if current_user.role == 'admin':
        order = db.session.get(Order, order_id)
    else:
        order = db.session.query(Order).filter_by(id=order_id, user_id=current_user.id).first()

    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    data = order.to_dict()
    is_admin = current_user.role == 'admin'
    data['items'] = [
        item.to_dict(is_admin=is_admin) if hasattr(item, 'to_dict') and 'is_admin' in item.to_dict.__code__.co_varnames
        else {
            'id': item.id,
            'order_id': item.order_id,
            'product_id': item.product_id,
            'product_name': item.product.name if item.product else 'Deleted Product',
            'quantity': item.quantity,
            'price': float(item.price) if item.price is not None else 0.0,
            'subtotal': float(item.subtotal) if item.subtotal is not None else 0.0
        }
        for item in order.order_items
    ]

    return jsonify({
        'success': True,
        'order': data
    }), 200


@api_bp.route('/orders/checkout', methods=['POST'])
@limiter.limit("10 per minute")
def api_checkout():
    """
    Checkout current cart to create an order.
    Body: { shipping_address: string, payment_method: string }
    """
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required to checkout'}), 401

    if current_user.role != 'customer':
        return jsonify({'success': False, 'message': 'Only customers can checkout online orders'}), 403

    data = request.get_json(silent=True) or request.form
    shipping_address = (data.get('shipping_address') or current_user.address or '').strip()
    payment_method = (data.get('payment_method') or 'COD').strip().upper()

    valid_methods = {'COD', 'UPI', 'CARD', 'UDHAR'}
    if payment_method not in valid_methods:
        return jsonify({'success': False, 'message': 'Invalid payment method'}), 400

    if not shipping_address or len(shipping_address) < 15 or len(shipping_address) > 500:
        return jsonify({'success': False, 'message': 'Shipping address must be between 15 and 500 characters'}), 400

    order, message = OrderService.create_order_from_cart(
        user_id=current_user.id,
        shipping_address=shipping_address,
        payment_method=payment_method
    )

    if not order:
        return jsonify({'success': False, 'message': message}), 400

    return jsonify({
        'success': True,
        'message': message,
        'order': order.to_dict()
    }), 201
