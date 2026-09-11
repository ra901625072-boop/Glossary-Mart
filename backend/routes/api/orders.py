from flask import jsonify, request
from flask_login import current_user
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
    """Get single order details and line items"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    order = db.session.query(Order).filter_by(id=order_id, user_id=current_user.id).first()
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    data = order.to_dict()
    data['items'] = [item.to_dict() for item in order.order_items]

    return jsonify({
        'success': True,
        'order': data
    }), 200


@api_bp.route('/orders/checkout', methods=['POST'])
def api_checkout():
    """
    Checkout current cart to create an order.
    Body: { shipping_address: string, payment_method: string }
    """
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required to checkout'}), 401

    data = request.get_json(silent=True) or request.form
    shipping_address = data.get('shipping_address') or current_user.address
    payment_method = data.get('payment_method', 'COD').upper()

    if not shipping_address:
        return jsonify({'success': False, 'message': 'Shipping address is required'}), 400

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
