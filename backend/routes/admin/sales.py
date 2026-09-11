"""Admin sales management routes (record, history, export, bill)."""
from datetime import datetime, timedelta

from flask import Response, current_app, flash, make_response, redirect, render_template, request, url_for

from database.models import db
from database.models.product import Product, Sale
from backend.services.inventory_service import InventoryService
from backend.services.export_service import generate_sales_csv, generate_sales_pdf
from backend.constants import MAX_SALES_HISTORY
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/sales', methods=['GET', 'POST'])
@admin_required
def sales():
    """Sales entry page — record a manual sale."""
    if request.method == 'POST':
        try:
            product_id = int(request.form.get('product_id'))
            quantity = int(request.form.get('quantity'))
        except (ValueError, TypeError):
            flash('Invalid product or quantity selection.', 'danger')
            return redirect(url_for('admin.sales'))

        if quantity <= 0:
            flash('Quantity must be greater than zero.', 'danger')
            return redirect(url_for('admin.sales'))

        product = db.session.get(Product, product_id)
        if not product:
            flash("Product not found.", "danger")
            return redirect(url_for('admin.sales'))

        if product.stock_quantity < quantity:
            flash(f'Insufficient stock! Only {product.stock_quantity} units available.', 'danger')
            return redirect(url_for('admin.sales'))

        total_price = product.selling_price * quantity
        profit = (product.selling_price - product.cost_price) * quantity

        sale = Sale(product_id=product_id, quantity=quantity, total_price=total_price, profit=profit)

        ok, msg = InventoryService.deduct_stock(product_id, quantity, triggered_by='manual_sale')
        if not ok:
            flash(msg, 'danger')
            return redirect(url_for('admin.sales'))

        try:
            db.session.add(sale)
            db.session.commit()
            flash(f'Sale recorded! Profit: ₹{profit:.2f}', 'success')
            return redirect(url_for('admin.view_bill', sale_id=sale.id, print=1))
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to record sale")
            flash('Could not record sale. Please try again.', 'danger')

        return redirect(url_for('admin.sales'))

    all_products = db.session.query(Product).filter(Product.stock_quantity > 0).order_by(Product.name).all()
    return render_template('admin/sales.html', products=all_products)


@admin_bp.route('/sales/history')
@admin_required
def sales_history():
    """Sales history page."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    pagination = db.session.query(Sale).order_by(Sale.sale_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/sales_history.html', sales=pagination.items, pagination=pagination)


@admin_bp.route('/sales/export')
@admin_required
def export_sales():
    """Export sales data as CSV or PDF."""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    export_format = request.args.get('format', 'csv')

    query = db.session.query(Sale)

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(Sale.sale_date >= start_date)
        except ValueError:
            flash('Invalid start date format.', 'danger')
            return redirect(url_for('admin.sales_history'))

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Sale.sale_date < end_date)
        except ValueError:
            flash('Invalid end date format.', 'danger')
            return redirect(url_for('admin.sales_history'))

    all_sales = query.order_by(Sale.sale_date.desc()).all()

    if not all_sales:
        flash('No sales records found for the selected period.', 'info')
        return redirect(url_for('admin.sales_history'))

    filename_prefix = f"sales_report_{datetime.now().strftime('%Y%m%d')}"

    if export_format == 'csv':
        csv_data = generate_sales_csv(all_sales)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename_prefix}.csv"},
        )
    elif export_format == 'pdf':
        pdf_data = generate_sales_pdf(all_sales, start_date_str, end_date_str)
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={filename_prefix}.pdf'
        return response

    return redirect(url_for('admin.sales_history'))


@admin_bp.route('/sales/bill/<int:sale_id>')
@admin_required
def view_bill(sale_id):
    """Printable bill for a manual sale."""
    sale = db.session.get(Sale, sale_id)
    if not sale:
        flash("Sale record not found.", "danger")
        return redirect(url_for('admin.sales_history'))
    return render_template('admin/bill.html', sale=sale)
