"""Admin Point-of-Sale routes (POS interface + checkout API)."""
from flask import current_app, jsonify, render_template, request

from database.models import db
from database.models.product import Product, Sale
from backend.services.inventory_service import InventoryService
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/pos')
@admin_required
def pos():
    """POS (Point of Sale) interface."""
    pos_products = (
        db.session.query(Product)
        .filter(Product.stock_quantity > 0, Product.is_active == True)  # noqa: E712
        .order_by(Product.name)
        .all()
    )
    return render_template('admin/pos.html', products=pos_products)


@admin_bp.route('/api/pos/checkout', methods=['POST'])
@admin_required
def pos_checkout():
    """
    POS checkout JSON API.

    Request body: {"cart": [{"id": <product_id>, "qty": <quantity>}, ...]}
    Returns:      {"success": true, "total": <float>}
                  {"success": false, "error": "<message>"}
    """
    data = request.get_json(silent=True) or {}
    cart_items = data.get('cart', [])

    if not cart_items:
        return jsonify({'success': False, 'error': 'Cart is empty.'})

    total_paid = 0.0

    try:
        for item in cart_items:
            try:
                product_id = int(item.get('id'))
                qty = int(item.get('qty', 0))
            except (ValueError, TypeError):
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Invalid product ID or quantity.'})

            if qty <= 0:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Quantity must be greater than zero.'})

            product = db.session.get(Product, product_id)

            if not product:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Product #{product_id} not found.'})

            if product.stock_quantity < qty:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Insufficient stock for "{product.name}". Available: {product.stock_quantity}.',
                })

            profit = (product.selling_price - product.cost_price) * qty
            ok, msg = InventoryService.deduct_stock(product.id, qty, triggered_by='pos')
            if not ok:
                db.session.rollback()
                return jsonify({'success': False, 'error': msg})

            sale = Sale(
                product_id=product.id,
                quantity=qty,
                total_price=product.selling_price * qty,
                profit=profit,
            )
            db.session.add(sale)
            total_paid += float(product.selling_price * qty)

        db.session.commit()
        return jsonify({'success': True, 'total': round(total_paid, 2)})

    except Exception:
        db.session.rollback()
        current_app.logger.exception("POS checkout failed")
        return jsonify({'success': False, 'error': 'A server error occurred. Please try again.'})
