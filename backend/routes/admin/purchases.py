"""Admin purchase management routes (record stock-in, list purchases)."""
from flask import current_app, jsonify, request

from backend.models import db
from backend.models.product import Product
from backend.models.inventory import Supplier, Purchase
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
                'invoice_number': pu.invoice_number or f"INV-RESTOCK-{pu.id}",
                'payment_status': pu.payment_status or 'Unpaid',
                'payment_mode': pu.payment_mode or 'Credit',
                'purchase_date': pu.purchase_date.isoformat() if pu.purchase_date else None,
            }
            for pu in purchases_list
        ]
    })


@admin_bp.route('/purchases/add', methods=['GET', 'POST'])
@admin_required
def add_purchase():
    """Record a new stock purchase with Weighted Average Cost (WAC) valuation."""
    suppliers_list = db.session.query(Supplier).order_by(Supplier.name).all()
    products_list = db.session.query(Product).filter_by(is_active=True).order_by(Product.name).all()

    if request.method == 'GET':
        if not suppliers_list:
            return jsonify({'error': 'Please add a supplier first before recording a purchase.'}), 400
        if not products_list:
            return jsonify({'error': 'Please add a product first before recording a purchase.'}), 400
        return jsonify({
            'suppliers': [{'id': s.id, 'name': s.name, 'outstanding_balance': float(s.outstanding_balance or 0)} for s in suppliers_list],
            'products': [{'id': p.id, 'name': p.name, 'current_stock': p.stock_quantity, 'cost_price': float(p.cost_price or 0)} for p in products_list],
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

    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({'success': False, 'message': 'Selected supplier not found.'}), 404

    invoice_num = (data.get('invoice_number') or data.get('supplier_invoice') or '').strip()
    payment_status = (data.get('payment_status') or 'Unpaid').strip()
    payment_mode = (data.get('payment_mode') or 'Credit').strip()

    total_cost = quantity * purchase_price

    # 1. Compute Weighted Average Cost (WAC) to preserve accurate inventory valuation
    prior_stock = product.stock_quantity
    prior_cost = float(product.cost_price or 0.0)
    inward_qty = quantity
    inward_cost = purchase_price
    new_total_stock = prior_stock + inward_qty

    if new_total_stock > 0 and prior_stock > 0:
        blended_wac = round(((prior_stock * prior_cost) + (inward_qty * inward_cost)) / new_total_stock, 2)
        product.cost_price = max(0.01, blended_wac)
    else:
        product.cost_price = inward_cost

    product.supplier_name = supplier.name

    # 2. Add Stock with concurrency-safe locking
    ok, msg = InventoryService.add_stock(product_id, quantity, triggered_by='purchase')
    if not ok:
        db.session.rollback()
        return jsonify({'success': False, 'message': msg}), 400

    # 3. Create purchase record
    purchase = Purchase(
        supplier_id=supplier_id,
        product_id=product_id,
        quantity=quantity,
        purchase_price=purchase_price,
        total_cost=total_cost,
        invoice_number=invoice_num,
        payment_status=payment_status,
        payment_mode=payment_mode,
    )
    db.session.add(purchase)

    # 4. Update Supplier Accounts Payable (AP) liability
    if payment_status != 'Paid':
        supplier.outstanding_balance = float(supplier.outstanding_balance or 0.0) + total_cost

    try:
        db.session.commit()
        if not purchase.invoice_number:
            purchase.invoice_number = f"INV-RESTOCK-{purchase.id:04d}"
            db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Stock received! Added {quantity} units. Blended WAC Cost: ₹{float(product.cost_price):.2f}',
            'purchase_id': purchase.id,
            'new_cost_price': float(product.cost_price),
            'supplier_ap_balance': float(supplier.outstanding_balance or 0.0),
        })
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to record purchase")
        return jsonify({'success': False, 'message': 'Could not record purchase. Please try again.'}), 500
