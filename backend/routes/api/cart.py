from flask import jsonify, request, session
from flask_login import current_user
from backend.services.cart_service import CartService
from database.models import db
from database.models.order import Cart
from . import api_bp


@api_bp.route('/cart', methods=['GET'])
def get_cart():
    """Get current user or session cart items and totals"""
    cart_items, total = CartService.get_cart_items()
    items = []
    for item in cart_items:
        if hasattr(item, 'to_dict'):
            items.append(item.to_dict())
        else:
            # GuestCartItem object
            items.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': item.product.name,
                'product_price': float(item.product.selling_price),
                'product_image': item.product.image_path,
                'quantity': item.quantity,
                'subtotal': float(item.subtotal),
                'added_at': None
            })

    return jsonify({
        'success': True,
        'items': items,
        'total': float(total),
        'item_count': sum(i['quantity'] for i in items)
    }), 200


@api_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add product to cart. JSON body: { product_id: int, quantity: int }"""
    data = request.get_json(silent=True) or request.form
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid product ID or quantity'}), 400

    success, message = CartService.add_item(product_id, quantity)
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message': message}), status_code


@api_bp.route('/cart/update', methods=['PUT', 'POST'])
def update_cart():
    """Update cart item quantity. JSON body: { cart_id: int/str, quantity: int }"""
    data = request.get_json(silent=True) or request.form
    cart_id = data.get('cart_id')
    quantity = data.get('quantity')

    if cart_id is None or quantity is None:
        return jsonify({'success': False, 'message': 'cart_id and quantity are required'}), 400

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Quantity must be an integer'}), 400

    success, message = CartService.update_item(cart_id, quantity)
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message': message}), status_code


@api_bp.route('/cart/item/<cart_id>', methods=['DELETE', 'POST'])
def remove_from_cart(cart_id):
    """Remove item from cart"""
    success, message = CartService.remove_item(cart_id)
    status_code = 200 if success else 400
    return jsonify({'success': success, 'message': message}), status_code


@api_bp.route('/cart/clear', methods=['DELETE', 'POST'])
def clear_cart():
    """Clear all items in current cart"""
    if current_user.is_authenticated and current_user.role == 'customer':
        db.session.query(Cart).filter_by(user_id=current_user.id).delete()
        db.session.commit()
    else:
        session['cart'] = {}
        session.modified = True
    return jsonify({'success': True, 'message': 'Cart cleared'}), 200
