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
    shipping_address = (data.get('shipping_address') or data.get('delivery_address') or data.get('address') or current_user.address or '').strip()
    raw_method = (data.get('payment_method') or 'COD').strip().upper()
    if raw_method in ('CASH_ON_DELIVERY', 'CASH'):
        payment_method = 'COD'
    elif raw_method in ('ONLINE', 'GPAY', 'PHONEPE', 'PAYTM'):
        payment_method = 'UPI'
    elif raw_method in ('CREDIT_CARD', 'DEBIT_CARD'):
        payment_method = 'CARD'
    else:
        payment_method = raw_method

    valid_methods = {'COD', 'UPI', 'CARD', 'UDHAR'}
    if payment_method not in valid_methods:
        return jsonify({'success': False, 'message': 'Invalid payment method'}), 400

    if not shipping_address or len(shipping_address) < 10 or len(shipping_address) > 500:
        return jsonify({'success': False, 'message': 'Shipping address must be between 10 and 500 characters'}), 400

    # If DB cart is empty, but items were provided in payload, populate them first
    from database.models.order import Cart
    from backend.services.cart_service import CartService
    db_cart_count = db.session.query(Cart).filter_by(user_id=current_user.id).count()
    if db_cart_count == 0 and data.get('items'):
        for item in data.get('items'):
            pid = item.get('product_id') or item.get('productId') or item.get('id')
            qty = item.get('quantity') or item.get('qty', 1)
            try:
                pid = int(pid)
                qty = int(qty)
                if pid > 0 and qty > 0:
                    CartService.add_item(pid, qty)
            except (ValueError, TypeError):
                pass

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


@api_bp.route('/orders/<int:order_id>/invoice', methods=['GET'])
def get_order_invoice(order_id):
    """Download printable PDF tax invoice for order"""
    from flask import make_response
    from backend.services.export_service import generate_order_invoice_pdf

    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    if current_user.role == 'admin':
        order = db.session.get(Order, order_id)
    else:
        order = db.session.query(Order).filter_by(id=order_id, user_id=current_user.id).first()

    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    pdf_bytes = generate_order_invoice_pdf(order)
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="invoice-order-{order.id}.pdf"'
    return response

