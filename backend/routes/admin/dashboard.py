"""Admin dashboard and analytics routes."""
from sqlalchemy import func

from flask import redirect, render_template, url_for

from database.models import db
from database.models.order import Order, OrderItem
from backend.services.stats_service import (
    get_chart_data, get_monthly_comparison, get_sales_stats,
    get_stock_stats, get_yearly_comparison,
)
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/')
@admin_required
def admin_base():
    """Redirect /admin to /admin/dashboard."""
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Analytics dashboard."""
    stats_1_day = get_sales_stats(1)
    stats_7_days = get_sales_stats(7)
    stats_30_days = get_sales_stats(30)
    monthly_comparison = get_monthly_comparison()
    yearly_comparison = get_yearly_comparison()
    chart_data = get_chart_data(30)
    stock_stats = get_stock_stats()

    order_stats = db.session.query(
        func.count(Order.id).label('total_orders'),
        func.coalesce(func.sum(Order.total_amount), 0).label('total_revenue')
    ).first()

    pending_orders = db.session.query(func.count(Order.id)).filter(
        Order.order_status == 'Pending'
    ).scalar() or 0

    total_order_profit = db.session.query(
        func.coalesce(func.sum(OrderItem.profit), 0)
    ).join(Order).filter(
        Order.order_status != 'Cancelled'
    ).scalar() or 0

    return render_template(
        'admin/dashboard.html',
        stats_1_day=stats_1_day,
        stats_7_days=stats_7_days,
        stats_30_days=stats_30_days,
        monthly_comparison=monthly_comparison,
        yearly_comparison=yearly_comparison,
        chart_data=chart_data,
        stock_stats=stock_stats,
        total_orders=order_stats.total_orders,
        total_order_revenue=float(order_stats.total_revenue),
        total_order_profit=float(total_order_profit),
        pending_orders=pending_orders,
    )


@admin_bp.route('/admin.html')
@admin_bp.route('/console')
@admin_bp.route('/erp')
@admin_bp.route('/master')
def admin_erp_console():
    """Consolidated Admin ERP Super-App Console."""
    return render_template('admin.html')


