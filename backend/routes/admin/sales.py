"""Admin sales management routes (record, history, export, bill)."""
from datetime import datetime, timedelta

from flask import Response, current_app, jsonify, make_response, request, url_for

from database.models import db
from database.models.product import Product, Sale
from backend.services.inventory_service import InventoryService
from backend.services.export_service import generate_sales_csv, generate_sales_pdf
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/sales', methods=['GET', 'POST'])
@admin_required
def sales():
    """Sales entry — GET returns products JSON, POST records a sale."""
    if request.method == 'POST':
        try:
            if request.is_json:
                product_id = int(request.json.get('product_id'))
                quantity = int(request.json.get('quantity'))
            else:
                product_id = int(request.form.get('product_id'))
                quantity = int(request.form.get('quantity'))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid product or quantity selection.'}), 400

        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be greater than zero.'}), 400

        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found.'}), 404

        if product.stock_quantity < quantity:
            return jsonify({'success': False, 'message': f'Insufficient stock! Only {product.stock_quantity} units available.'}), 400

        total_price = product.selling_price * quantity
        profit = (product.selling_price - product.cost_price) * quantity

        sale = Sale(product_id=product_id, quantity=quantity, total_price=total_price, profit=profit)

        ok, msg = InventoryService.deduct_stock(product_id, quantity, triggered_by='manual_sale')
        if not ok:
            return jsonify({'success': False, 'message': msg}), 400

        try:
            db.session.add(sale)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Sale recorded! Profit: ₹{profit:.2f}',
                'sale_id': sale.id,
                'bill_url': url_for('admin.view_bill', sale_id=sale.id),
            })
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to record sale")
            return jsonify({'success': False, 'message': 'Could not record sale. Please try again.'}), 500

    # GET — return available products for the sales form
    all_products = db.session.query(Product).filter(Product.stock_quantity > 0).order_by(Product.name).all()
    return jsonify({
        'products': [
            {
                'id': p.id,
                'name': p.name,
                'selling_price': float(p.selling_price),
                'cost_price': float(p.cost_price),
                'stock_quantity': p.stock_quantity,
                'category': p.category_rel.name if p.category_rel else 'General',
            }
            for p in all_products
        ]
    })


@admin_bp.route('/sales/history')
@admin_required
def sales_history():
    """Sales history — returns JSON with invoice/bill metadata."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    pagination = db.session.query(Sale).order_by(Sale.sale_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'success': True,
        'sales': [
            {
                'id': s.id,
                'bill_id': s.bill_id,
                'bill_number': s.bill_rel.bill_number if s.bill_rel else f"SAL-{s.id:04d}",
                'customer_name': s.bill_rel.customer_name if s.bill_rel else 'Walk-in Counter',
                'customer_phone': s.bill_rel.customer_phone if s.bill_rel and s.bill_rel.customer_phone else '',
                'payment_method': s.bill_rel.payment_method if s.bill_rel else 'Cash',
                'product_name': s.product.name if s.product else 'Unknown',
                'product_id': s.product_id,
                'quantity': s.quantity,
                'total_price': float(s.total_price),
                'profit': float(s.profit),
                'sale_date': s.sale_date.isoformat() if s.sale_date else None,
            }
            for s in pagination.items
        ],
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
        }
    })


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
            return jsonify({'error': 'Invalid start date format.'}), 400

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Sale.sale_date < end_date)
        except ValueError:
            return jsonify({'error': 'Invalid end date format.'}), 400

    all_sales = query.order_by(Sale.sale_date.desc()).all()

    if not all_sales:
        return jsonify({'error': 'No sales records found for the selected period.'}), 404

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

    return jsonify({'error': 'Invalid export format. Use csv or pdf.'}), 400


@admin_bp.route('/sales/bill/<int:sale_id>')
@admin_required
def view_bill(sale_id):
    """Printable bill for a sale or complete POS invoice — returns JSON bill data."""
    sale = db.session.get(Sale, sale_id)
    if not sale:
        return jsonify({'error': 'Sale record not found.'}), 404

    bill = sale.bill_rel
    if bill:
        items = [
            {
                'product_name': si.product.name if si.product else 'Unknown',
                'quantity': si.quantity,
                'unit_price': float(si.product.selling_price) if si.product else 0,
                'total_price': float(si.total_price),
            }
            for si in bill.sales
        ]
        return jsonify({
            'bill_id': bill.id,
            'bill_number': bill.bill_number,
            'customer_name': bill.customer_name or 'Walk-in Counter',
            'customer_phone': bill.customer_phone or '',
            'subtotal': float(bill.subtotal),
            'discount': float(bill.discount_amount),
            'tax': float(bill.tax_amount),
            'total_price': float(bill.total_amount),
            'payment_method': bill.payment_method,
            'sale_date': bill.created_at.strftime('%Y-%m-%d %H:%M:%S') if bill.created_at else None,
            'items': items,
        })

    return jsonify({
        'bill_id': sale.id,
        'bill_number': f"SAL-{sale.id:04d}",
        'customer_name': 'Walk-in Counter',
        'customer_phone': '',
        'product_name': sale.product.name if sale.product else 'Unknown',
        'quantity': sale.quantity,
        'total_price': float(sale.total_price),
        'subtotal': float(sale.total_price),
        'discount': 0.0,
        'tax': round(float(sale.total_price) * 0.05 / 1.05, 2),
        'payment_method': 'Cash',
        'profit': float(sale.profit),
        'sale_date': sale.sale_date.strftime('%Y-%m-%d %H:%M:%S') if sale.sale_date else None,
        'unit_price': float(sale.product.selling_price) if sale.product else 0,
        'items': [
            {
                'product_name': sale.product.name if sale.product else 'Unknown',
                'quantity': sale.quantity,
                'unit_price': float(sale.product.selling_price) if sale.product else 0,
                'total_price': float(sale.total_price),
            }
        ]
    })
