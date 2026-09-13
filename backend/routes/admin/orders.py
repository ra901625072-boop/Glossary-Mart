"""Admin order management routes (list, detail, status update)."""
from flask import current_app, jsonify, request
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database.models import db
from database.models.order import Order
from backend.services.inventory_service import InventoryService
from backend.services.email_service import EmailService
from backend.constants import OrderStatus, PaymentStatus, ORDER_STATUS_TRANSITIONS
from backend.routes.decorators import admin_required
from .helpers import _log_action
from . import admin_bp


@admin_bp.route('/orders')
@admin_required
def admin_orders():
    """Order list — returns JSON with customer profile details."""
    page = request.args.get('page', 1, type=int)
    per_page = min(max(request.args.get('per_page', 20, type=int), 1), 100)
    pagination = (
        db.session.query(Order)
        .options(joinedload(Order.user))
        .order_by(Order.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    agg = db.session.query(
        func.count(Order.id).label('total'),
        func.sum(Order.total_amount).label('revenue'),
    ).first()
    pending_count = db.session.query(func.count(Order.id)).filter(
        Order.order_status == OrderStatus.PENDING
    ).scalar() or 0

    return jsonify({
        'orders': [
            {
                'id': o.id,
                'user_id': o.user_id,
                'customer_name': (o.user.full_name or o.user.username) if o.user else f'Customer #{o.user_id}',
                'customer_phone': o.user.phone if o.user else '',
                'customer_email': o.user.email if o.user else '',
                'total_amount': float(o.total_amount),
                'order_status': o.order_status,
                'payment_status': o.payment_status,
                'payment_method': o.payment_method,
                'shipping_address': o.shipping_address or '',
                'created_at': o.created_at.isoformat() if o.created_at else None,
            }
            for o in pagination.items
        ],
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
        },
        'summary': {
            'total_orders': agg.total or 0,
            'pending_orders': pending_count,
            'total_revenue': float(agg.revenue or 0),
        }
    })


@admin_bp.route('/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    """Admin view of a single order's details — returns JSON with customer info."""
    order = db.session.query(Order).options(joinedload(Order.user)).filter(Order.id == order_id).first()
    if not order:
        return jsonify({'error': 'Order not found.'}), 404

    items = []
    for oi in order.order_items:
        items.append({
            'product_name': oi.product.name if oi.product else 'Unknown',
            'product_id': oi.product_id,
            'quantity': oi.quantity,
            'price': float(oi.price),
            'profit': float(oi.profit) if oi.profit else 0,
            'subtotal': float(oi.price * oi.quantity),
        })

    return jsonify({
        'id': order.id,
        'user_id': order.user_id,
        'customer_name': (order.user.full_name or order.user.username) if order.user else f'Customer #{order.user_id}',
        'customer_phone': order.user.phone if order.user else '',
        'customer_email': order.user.email if order.user else '',
        'total_amount': float(order.total_amount),
        'order_status': order.order_status,
        'payment_status': order.payment_status,
        'payment_method': order.payment_method,
        'shipping_address': order.shipping_address or '',
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'items': items,
    })


@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@admin_bp.route('/orders/<int:order_id>/status', methods=['POST', 'PUT'])
@admin_required
def update_order_status(order_id):
    """Update order and/or payment status with state-machine validation and alias normalization."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'error': 'Order not found.'}), 404

    if request.is_json:
        new_status = request.json.get('order_status')
        payment_status = request.json.get('payment_status')
    else:
        new_status = request.form.get('order_status')
        payment_status = request.form.get('payment_status')

    # Normalize status aliases
    status_aliases = {
        'CONFIRMED': OrderStatus.PROCESSING.value,
        'ORDER PLACED': OrderStatus.PROCESSING.value,
        'SHIPPED': OrderStatus.OUT_FOR_DELIVERY.value,
        'DISPATCHED': OrderStatus.OUT_FOR_DELIVERY.value,
    }
    if new_status:
        clean_upper = str(new_status).strip().upper()
        if clean_upper in status_aliases:
            new_status = status_aliases[clean_upper]
        else:
            for s in OrderStatus:
                if s.value.lower() == str(new_status).strip().lower():
                    new_status = s.value
                    break

    # Validate values against enum members
    valid_order_statuses = {s.value for s in OrderStatus}
    valid_payment_statuses = {s.value for s in PaymentStatus}

    if new_status and new_status not in valid_order_statuses:
        return jsonify({'success': False, 'message': 'Invalid order status.'}), 400

    if payment_status and payment_status not in valid_payment_statuses:
        return jsonify({'success': False, 'message': 'Invalid payment status.'}), 400

    # State-machine transition check
    if new_status and new_status != order.order_status:
        allowed = ORDER_STATUS_TRANSITIONS.get(order.order_status, set())
        if new_status not in allowed:
            return jsonify({
                'success': False,
                'message': f'Invalid transition: cannot move order from "{order.order_status}" to "{new_status}". Allowed: {", ".join(allowed) or "None"}.'
            }), 400

    # Restore stock on first cancellation or return
    if new_status in (OrderStatus.CANCELLED, OrderStatus.RETURNED):
        if order.order_status not in (OrderStatus.CANCELLED, OrderStatus.RETURNED):
            InventoryService.restore_order_stock(order)

    prev_status = order.order_status
    prev_payment = order.payment_status

    if new_status:
        order.order_status = new_status
    if payment_status:
        order.payment_status = payment_status

    _log_action(
        'UPDATE_ORDER_STATUS', 'Order', order_id,
        details=(
            f'Status: {prev_status} → {order.order_status} | '
            f'Payment: {prev_payment} → {order.payment_status}'
        ),
    )

    try:
        db.session.commit()

        # Trigger customer email sequence based on state machine transitions
        try:
            if new_status and new_status != prev_status:
                if new_status == OrderStatus.PACKED.value:
                    EmailService.send_order_packed_email(order)
                elif new_status == OrderStatus.OUT_FOR_DELIVERY.value:
                    EmailService.send_out_for_delivery_email(order)
                elif new_status == OrderStatus.DELIVERED.value:
                    EmailService.send_order_delivered_email(order, attach_invoice=True)
                elif new_status == OrderStatus.CANCELLED.value:
                    cancel_reason = (
                        (request.json.get('reason') if request.is_json else request.form.get('reason'))
                        or 'Cancelled by Store Administrator'
                    )
                    EmailService.send_order_cancelled_email(order, reason=cancel_reason)

            if payment_status and payment_status != prev_payment:
                if payment_status == PaymentStatus.REFUNDED.value:
                    EmailService.send_refund_confirmation_email(order)
                elif payment_status == PaymentStatus.PAID.value and prev_payment != PaymentStatus.PAID.value:
                    EmailService.send_payment_confirmation_email(order)
        except Exception as email_err:
            current_app.logger.warning("Order status email dispatch error for order #%s: %s", order_id, email_err)

        return jsonify({
            'success': True,
            'message': f'Order #{order.id} updated: {order.order_status} / {order.payment_status}',
            'order_status': order.order_status,
            'payment_status': order.payment_status,
        })
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to update order #{order_id}")
        return jsonify({'success': False, 'message': 'Could not update order. Please try again.'}), 500
