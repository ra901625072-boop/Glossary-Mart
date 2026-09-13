"""Admin dashboard and analytics routes."""
from datetime import datetime, timezone
from sqlalchemy import func

from flask import jsonify, redirect, url_for

from database.models import db, User, Product, Sale
from database.models.expense import Expense
from database.models.order import Order, OrderItem
from backend.services.stats_service import (
    get_chart_data, get_monthly_comparison, get_sales_stats,
    get_stock_stats, get_yearly_comparison,
)
from backend.services.intelligence_service import IntelligenceService
from backend.routes.decorators import admin_required
from backend.routes.pages import serve_frontend_page
from . import admin_bp


@admin_bp.route('/')
@admin_required
def admin_base():
    """Redirect /admin to /admin/dashboard."""
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Analytics dashboard — returns JSON stats data for SPA."""
    now = datetime.now(timezone.utc)
    current_month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    stats_1_day = get_sales_stats(1)
    stats_7_days = get_sales_stats(7)
    stats_30_days = get_sales_stats(30)
    monthly_comparison = get_monthly_comparison()
    yearly_comparison = get_yearly_comparison()
    chart_data = get_chart_data(30)
    stock_stats = get_stock_stats()

    # 1. Online Orders (excluding cancelled)
    order_count = db.session.query(func.count(Order.id)).filter(Order.order_status != 'Cancelled').scalar() or 0
    all_order_count = db.session.query(func.count(Order.id)).scalar() or 0
    order_rev = float(db.session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
        Order.order_status != 'Cancelled'
    ).scalar() or 0)
    order_profit = float(db.session.query(
        func.coalesce(func.sum(OrderItem.profit), 0)
    ).join(Order).filter(
        Order.order_status != 'Cancelled'
    ).scalar() or 0)
    order_units = int(db.session.query(
        func.coalesce(func.sum(OrderItem.quantity), 0)
    ).join(Order).filter(
        Order.order_status != 'Cancelled'
    ).scalar() or 0)

    # 2. POS Counter Sales
    pos_count = db.session.query(func.count(Sale.id)).scalar() or 0
    pos_rev = float(db.session.query(func.coalesce(func.sum(Sale.total_price), 0)).scalar() or 0)
    pos_profit = float(db.session.query(func.coalesce(func.sum(Sale.profit), 0)).scalar() or 0)
    pos_units = int(db.session.query(func.coalesce(func.sum(Sale.quantity), 0)).scalar() or 0)

    # 3. Combined Store Financials
    total_sales_count = order_count + pos_count
    total_units_sold = order_units + pos_units
    total_revenue = round(order_rev + pos_rev, 2)
    gross_profit = round(order_profit + pos_profit, 2)

    # 4. Operating Expenses
    total_expenses = float(db.session.query(func.coalesce(func.sum(Expense.amount), 0)).scalar() or 0)
    monthly_expenses = float(db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.expense_date >= current_month_start
    ).scalar() or 0)

    # 5. Net Profit & Margin
    net_profit = round(gross_profit - total_expenses, 2)
    profit_margin_pct = round((net_profit / total_revenue * 100), 1) if total_revenue > 0 else 0.0

    # 6. Operational Inventory & Outstanding Receivables
    pending_orders = db.session.query(func.count(Order.id)).filter(
        Order.order_status == 'Pending'
    ).scalar() or 0

    inventory_valuation = float(db.session.query(
        func.coalesce(func.sum(Product.stock_quantity * Product.cost_price), 0)
    ).scalar() or 0)

    active_catalog_count = db.session.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0

    critical_low_stock = db.session.query(func.count(Product.id)).filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.minimum_stock_alert
    ).scalar() or 0

    total_udhar = float(db.session.query(func.coalesce(func.sum(User.credit), 0)).scalar() or 0)

    def _stats_dict(s):
        if not s:
            return {'count': 0, 'revenue': 0.0, 'profit': 0.0}
        return {
            'count': getattr(s, 'count', 0) or 0,
            'revenue': float(getattr(s, 'revenue', 0) or 0),
            'profit': float(getattr(s, 'profit', 0) or 0),
        }

    financials = {
        'total_revenue': total_revenue,
        'online_revenue': round(order_rev, 2),
        'pos_revenue': round(pos_rev, 2),
        'total_sales_count': total_sales_count,
        'total_units_sold': total_units_sold,
        'gross_profit': gross_profit,
        'total_expenses': round(total_expenses, 2),
        'monthly_expenses': round(monthly_expenses, 2),
        'net_profit': net_profit,
        'profit_margin_pct': profit_margin_pct,
        'inventory_valuation': round(inventory_valuation, 2),
        'total_udhar': round(total_udhar, 2),
        'pending_orders': pending_orders,
        'active_catalog_count': active_catalog_count,
        'critical_low_stock': critical_low_stock,
    }

    stats_dict = {
        'stats_1_day': _stats_dict(stats_1_day),
        'stats_7_days': _stats_dict(stats_7_days),
        'stats_30_days': _stats_dict(stats_30_days),
        'monthly_comparison': monthly_comparison,
        'yearly_comparison': yearly_comparison,
        'chart_data': chart_data,
        'stock_stats': stock_stats,
        'total_orders': all_order_count,
        'total_order_revenue': float(order_rev),
        'total_order_profit': float(order_profit),
        'pending_orders': pending_orders,
        'total_sales': total_sales_count,
        'total_units_sold': total_units_sold,
        'total_revenue': total_revenue,
        'gross_profit': gross_profit,
        'total_expenses': round(total_expenses, 2),
        'monthly_expenses': round(monthly_expenses, 2),
        'net_profit': net_profit,
        'profit_margin_pct': profit_margin_pct,
        'inventory_valuation': round(inventory_valuation, 2),
        'total_udhar': round(total_udhar, 2),
        'active_catalog_count': active_catalog_count,
        'critical_low_stock': critical_low_stock,
        'financials': financials,
    }

    intelligence = IntelligenceService.get_full_intelligence_payload()
    stats_dict['intelligence'] = intelligence

    return jsonify({
        'success': True,
        'stats': stats_dict,
        'intelligence': intelligence,
        'financials': financials,
        **stats_dict
    })


@admin_bp.route('/admin.html')
@admin_bp.route('/console')
@admin_bp.route('/erp')
@admin_bp.route('/master')
def admin_erp_console():
    """Consolidated Admin ERP Super-App Console — serves the SPA."""
    return serve_frontend_page('admin.html')

