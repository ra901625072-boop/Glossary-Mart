"""Admin order management routes (list, detail, status update)."""
from flask import current_app, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from database.models import db
from database.models.order import Order
from backend.services.inventory_service import InventoryService
from backend.constants import OrderStatus, PaymentStatus, ORDER_STATUS_TRANSITIONS
from backend.routes.decorators import admin_required
from .helpers import _log_action
from . import admin_bp


@admin_bp.route('/orders')
@admin_required
def admin_orders():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = db.session.query(Order).order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    agg = db.session.query(
        func.count(Order.id).label('total'),
        func.sum(Order.total_amount).label('revenue'),
    ).first()
    pending_count = db.session.query(func.count(Order.id)).filter(
        Order.order_status == OrderStatus.PENDING
    ).scalar() or 0

    return render_template(
        'admin/admin_orders.html',
        orders=pagination.items,
        pagination=pagination,
        total_orders=agg.total or 0,
        pending_orders=pending_count,
        total_revenue=float(agg.revenue or 0),
    )


@admin_bp.route('/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    """Admin view of a single order's details."""
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for('admin.admin_orders'))
    return render_template('admin/admin_order_detail.html', order=order)


@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """Update order and/or payment status with state-machine validation."""
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for('admin.admin_orders'))

    new_status = request.form.get('order_status')
    payment_status = request.form.get('payment_status')

    # Validate values against enum members
    valid_order_statuses = {s.value for s in OrderStatus}
    valid_payment_statuses = {s.value for s in PaymentStatus}

    if new_status and new_status not in valid_order_statuses:
        flash('Invalid order status.', 'danger')
        return redirect(url_for('admin.admin_order_detail', order_id=order_id))

    if payment_status and payment_status not in valid_payment_statuses:
        flash('Invalid payment status.', 'danger')
        return redirect(url_for('admin.admin_order_detail', order_id=order_id))

    # State-machine transition check
    if new_status and new_status != order.order_status:
        allowed = ORDER_STATUS_TRANSITIONS.get(order.order_status, set())
        if new_status not in allowed:
            flash(
                f'Invalid transition: cannot move order from "{order.order_status}" '
                f'to "{new_status}". Allowed: {", ".join(allowed) or "None"}.',
                'danger',
            )
            return redirect(url_for('admin.admin_order_detail', order_id=order_id))

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
        flash(f'Order #{order.id} updated: {order.order_status} / {order.payment_status}', 'success')
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to update order #{order_id}")
        flash('Could not update order. Please try again.', 'danger')

    return redirect(url_for('admin.admin_order_detail', order_id=order_id))
