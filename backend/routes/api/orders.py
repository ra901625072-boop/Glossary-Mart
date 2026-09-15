from datetime import datetime

from flask import current_app, jsonify, request
from flask_login import current_user

from backend.extensions import limiter
from backend.services.email_service import EmailService
from backend.services.order_service import OrderService
from backend.models import db
from backend.models.order import Order
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
    elif raw_method in ('NETBANKING', 'NET_BANKING', 'NET'):
        payment_method = 'NETBANKING'
    else:
        payment_method = raw_method

    valid_methods = {'COD', 'UPI', 'CARD', 'UDHAR', 'NETBANKING'}
    if payment_method not in valid_methods:
        return jsonify({'success': False, 'message': 'Invalid payment method'}), 400

    if not shipping_address or len(shipping_address) < 10 or len(shipping_address) > 500:
        return jsonify({'success': False, 'message': 'Shipping address must be between 10 and 500 characters'}), 400

    # If items were explicitly provided in checkout payload, validate each item first before syncing into DB cart
    from backend.models.order import Cart
    from backend.models.product import Product
    from backend.services.cart_service import CartService
    payload_items = data.get('items')
    if payload_items and isinstance(payload_items, list) and len(payload_items) > 0:
        parsed_items = []
        for item in payload_items:
            pid = item.get('product_id') or item.get('productId') or item.get('id')
            qty = item.get('quantity') or item.get('qty', 1)
            try:
                pid = int(pid)
                qty = int(qty)
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Invalid product item format in checkout request.'}), 400

            if pid <= 0 or qty <= 0:
                continue

            product = db.session.get(Product, pid)
            if not product or not product.is_active:
                return jsonify({
                    'success': False,
                    'message': 'One or more items in your cart are unavailable or discontinued.',
                    'product_id': pid,
                    'out_of_stock': True
                }), 400

            if product.stock_quantity <= 0:
                return jsonify({
                    'success': False,
                    'message': f'"{product.name}" is currently Out Of Stock. Please remove it from your cart to proceed.',
                    'error_code': 'OUT_OF_STOCK',
                    'product_id': product.id,
                    'product_name': product.name,
                    'out_of_stock': True
                }), 400

            if product.stock_quantity < qty:
                return jsonify({
                    'success': False,
                    'message': f'Only {product.stock_quantity} unit(s) available for "{product.name}". Please adjust quantity to proceed.',
                    'error_code': 'INSUFFICIENT_STOCK',
                    'product_id': product.id,
                    'product_name': product.name,
                    'available_stock': product.stock_quantity
                }), 400

            parsed_items.append((pid, qty))

        if not parsed_items:
            return jsonify({'success': False, 'message': 'Your shopping cart contains no valid items.'}), 400

        # All items verified in stock — safe to sync into DB cart
        db.session.query(Cart).filter_by(user_id=current_user.id).delete()
        for pid, qty in parsed_items:
            CartService.add_item(pid, qty)

    order, message = OrderService.create_order_from_cart(
        user_id=current_user.id,
        shipping_address=shipping_address,
        payment_method=payment_method
    )

    if not order:
        return jsonify({'success': False, 'message': message}), 400

    # Dispatch customer order confirmation email sequence
    email_status = {'sent': False}
    try:
        email_res = EmailService.send_order_confirmation_email(order, current_user)
        email_status = {
            'sent': bool(email_res and email_res.get('success')),
            'provider': email_res.get('provider') if email_res else None,
            'is_sandbox_restriction': bool(email_res and email_res.get('is_sandbox_restriction')),
            'sandbox_recipient': email_res.get('sandbox_recipient') if email_res else None,
            'message': email_res.get('message') if email_res else 'Email dispatched'
        }
        if order.payment_status == 'Paid':
            EmailService.send_payment_confirmation_email(order, current_user)
    except Exception as email_err:
        current_app.logger.warning("Order confirmation email skipped: %s", email_err)
        email_status['error'] = str(email_err)

    return jsonify({
        'success': True,
        'message': message,
        'order': order.to_dict(),
        'email_status': email_status
    }), 201


@api_bp.route('/orders/<int:order_id>/pay', methods=['POST'])
def confirm_order_payment(order_id):
    """Mark order as Paid and dispatch Stage 2 payment receipt email"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    if current_user.role == 'admin':
        order = db.session.get(Order, order_id)
    else:
        order = db.session.query(Order).filter_by(id=order_id, user_id=current_user.id).first()

    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    data = request.get_json(silent=True) or {}
    payment_method = data.get('payment_method') or order.payment_method or 'UPI'
    txn_id = data.get('transaction_id') or f"TXN-{order.id}-{int(datetime.utcnow().timestamp())}"

    order.payment_status = 'Paid'
    if payment_method:
        order.payment_method = payment_method

    db.session.commit()

    # Dispatch payment receipt email
    try:
        EmailService.send_payment_confirmation_email(order, current_user, transaction_id=txn_id)
    except Exception as err:
        current_app.logger.warning("Payment confirmation email skipped: %s", err)

    return jsonify({
        'success': True,
        'message': 'Payment confirmed successfully.',
        'order': order.to_dict(),
        'transaction_id': txn_id
    })


@api_bp.route('/orders/<int:order_id>/slip', methods=['GET'])
def get_order_slip(order_id):
    """Return JSON thermal receipt slip data for any order (Customer & Admin compatible)"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    if current_user.role == 'admin':
        order = db.session.get(Order, order_id)
    else:
        order = db.session.query(Order).filter_by(id=order_id, user_id=current_user.id).first()

    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    items = [
        {
            'product_name': oi.product.name if oi.product else 'Grocery Item',
            'quantity': oi.quantity,
            'unit_price': float(oi.price if hasattr(oi, 'price') and oi.price is not None else (oi.product.selling_price if oi.product else 0)),
            'total_price': float((oi.price if hasattr(oi, 'price') and oi.price is not None else (oi.product.selling_price if oi.product else 0)) * oi.quantity),
        }
        for oi in order.order_items
    ]

    tot = float(order.total_amount)
    subtot = sum(item['total_price'] for item in items) if items else tot
    disc = max(0.0, subtot - tot)
    taxable = round(tot / 1.05, 2)
    tax = round(tot - taxable, 2)
    cgst = round(tax / 2.0, 2)
    sgst = round(tax / 2.0, 2)

    cust_name = getattr(order.user, 'full_name', None) or getattr(order.user, 'username', None) or 'Valued Shopper'
    cust_phone = getattr(order.user, 'phone', '') or ''

    return jsonify({
        'success': True,
        'bill_id': order.id,
        'bill_number': f"#EGM-{order.id:06d}",
        'order_id': order.id,
        'customer_name': cust_name,
        'customer_phone': cust_phone,
        'payment_method': order.payment_method or 'COD',
        'payment_status': order.payment_status or 'Pending',
        'subtotal': subtot,
        'discount': disc,
        'taxable_amount': taxable,
        'cgst': cgst,
        'sgst': sgst,
        'tax': tax,
        'total_price': tot,
        'sale_date': order.created_at.strftime('%d/%m/%Y, %I:%M:%S %p') if order.created_at else None,
        'items': items,
    })


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

