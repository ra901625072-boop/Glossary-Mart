"""Admin purchase management routes (record stock-in, list purchases)."""
from flask import current_app, jsonify, redirect, request, url_for

from database.models import db
from database.models.product import Product
from database.models.inventory import Supplier, Purchase
from backend.routes.decorators import admin_required
from backend.forms.admin import PurchaseForm
from . import admin_bp


@admin_bp.route('/purchases')
@admin_required
def purchases():
    """Purchase tracking — returns JSON list."""
    purchases_list = db.session.query(Purchase).order_by(Purchase.purchase_date.desc()).all()
    return jsonify({
        'purchases': [
            {
                'id': pu.id,
                'supplier_name': pu.supplier.name if pu.supplier else 'Unknown',
                'supplier_id': pu.supplier_id,
                'product_name': pu.product.name if pu.product else 'Unknown',
                'product_id': pu.product_id,
                'quantity': pu.quantity,
                'purchase_price': float(pu.purchase_price),
                'total_cost': float(pu.total_cost),
                'purchase_date': pu.purchase_date.isoformat() if pu.purchase_date else None,
            }
            for pu in purchases_list
        ]
    })


@admin_bp.route('/purchases/add', methods=['GET', 'POST'])
@admin_required
def add_purchase():
    """Record a new stock purchase — GET returns form options, POST records purchase."""
    suppliers_list = db.session.query(Supplier).order_by(Supplier.name).all()
    products_list = db.session.query(Product).filter_by(is_active=True).order_by(Product.name).all()

    if request.method == 'GET':
        if not suppliers_list:
            return jsonify({'error': 'Please add a supplier first before recording a purchase.'}), 400
        if not products_list:
            return jsonify({'error': 'Please add a product first before recording a purchase.'}), 400
        return jsonify({
            'suppliers': [{'id': s.id, 'name': s.name} for s in suppliers_list],
            'products': [{'id': p.id, 'name': p.name, 'current_stock': p.stock_quantity} for p in products_list],
        })

    if not suppliers_list:
        return jsonify({'error': 'Please add a supplier first before recording a purchase.'}), 400
    if not products_list:
        return jsonify({'error': 'Please add a product first before recording a purchase.'}), 400

    form = PurchaseForm()
    form.supplier_id.choices = [(s.id, s.name) for s in suppliers_list]
    form.product_id.choices = [(p.id, p.name) for p in products_list]

    if form.validate_on_submit():
        product = db.session.get(Product, form.product_id.data)
        quantity = form.quantity.data
        price_per_unit = form.purchase_price.data
        total_cost = quantity * price_per_unit

        purchase = Purchase(
            supplier_id=form.supplier_id.data,
            product_id=form.product_id.data,
            quantity=quantity,
            purchase_price=price_per_unit,
            total_cost=total_cost,
        )

        # Increase stock and update cost/supplier info from latest purchase
        product.stock_quantity += quantity
        product.cost_price = price_per_unit
        if purchase.supplier:
            product.supplier_name = purchase.supplier.name

        try:
            db.session.add(purchase)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Purchase recorded! Stock increased by {quantity}.',
                'purchase_id': purchase.id,
            })
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to record purchase")
            return jsonify({'success': False, 'message': 'Could not record purchase. Please try again.'}), 500

    errors = {field: errs for field, errs in form.errors.items()} if form.errors else {}
    return jsonify({'success': False, 'errors': errors}), 400
