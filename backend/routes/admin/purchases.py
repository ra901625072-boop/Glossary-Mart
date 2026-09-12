"""Admin purchase management routes (record stock-in, list purchases)."""
from flask import current_app, jsonify, request

from database.models import db
from database.models.product import Product
from database.models.inventory import Supplier, Purchase
from backend.services.inventory_service import InventoryService
from backend.routes.decorators import admin_required
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

    data = request.get_json() if request.is_json else request.form
    try:
        supplier_id = int(data.get('supplier_id'))
        product_id = int(data.get('product_id'))
        quantity = int(data.get('quantity'))
        purchase_price = float(data.get('purchase_price'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid input data. All fields are required.'}), 400

    if quantity <= 0 or purchase_price <= 0:
        return jsonify({'success': False, 'message': 'Quantity and purchase price must be greater than zero.'}), 400

    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Selected product not found.'}), 404

    total_cost = quantity * purchase_price
    purchase = Purchase(
        supplier_id=supplier_id,
        product_id=product_id,
        quantity=quantity,
        purchase_price=purchase_price,
        total_cost=total_cost,
    )

    # Use InventoryService for row-locked, concurrency-safe stock addition with audit logging
    ok, msg = InventoryService.add_stock(product_id, quantity, triggered_by='purchase')
    if not ok:
        db.session.rollback()
        return jsonify({'success': False, 'message': msg}), 400

    product.cost_price = purchase_price
    supplier = db.session.get(Supplier, supplier_id)
    if supplier:
        product.supplier_name = supplier.name

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
