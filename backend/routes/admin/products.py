"""Admin product management routes (CRUD + API endpoint)."""
from flask import current_app, jsonify, request

from database.models import db
from database.models.product import Category, Product
from backend.services.storage_service import StorageService
from backend.utils.files import allowed_file
from backend.routes.decorators import admin_required
from .helpers import _log_action
from . import admin_bp


@admin_bp.route('/products')
@admin_required
def products():
    """Product management — returns JSON product list."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = db.session.query(Product).filter_by(is_active=True).order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'products': [
            {
                'id': p.id,
                'name': p.name,
                'category': p.category_rel.name if p.category_rel else 'General',
                'category_id': p.category_id,
                'cost_price': float(p.cost_price),
                'selling_price': float(p.selling_price),
                'stock_quantity': p.stock_quantity,
                'minimum_stock_alert': p.minimum_stock_alert,
                'supplier_name': p.supplier_name or '',
                'image_path': p.image_path or '',
                'is_active': p.is_active,
                'created_at': p.created_at.isoformat() if p.created_at else None,
            }
            for p in pagination.items
        ],
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
        }
    })


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """Add new product — GET returns categories for form, POST creates product."""
    categories = db.session.query(Category).order_by(Category.name).all()
    
    if request.method == 'GET':
        return jsonify({
            'categories': [{'id': c.id, 'name': c.name} for c in categories]
        })

    data = request.get_json() if request.is_json else request.form
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Product name is required.'}), 400

    try:
        category_id = int(data.get('category_id'))
        cost_price = float(data.get('cost_price', 0.0))
        selling_price = float(data.get('selling_price', 0.0))
        stock_quantity = int(data.get('stock_quantity', 0))
        minimum_stock_alert = int(data.get('minimum_stock_alert', 5))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid numerical inputs for price or stock.'}), 400

    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            try:
                image_path = StorageService.upload_file(file)
            except ValueError as ve:
                return jsonify({'success': False, 'message': str(ve)}), 400

    product = Product(
        name=name,
        category_id=category_id,
        cost_price=cost_price,
        selling_price=selling_price,
        stock_quantity=stock_quantity,
        minimum_stock_alert=minimum_stock_alert,
        supplier_name=(data.get('supplier_name') or '').strip(),
        image_path=image_path,
    )

    try:
        db.session.add(product)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Product "{product.name}" added successfully!', 'product_id': product.id})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to add product")
        return jsonify({'success': False, 'message': 'Could not add product. Please try again.'}), 500


@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit product — GET returns product + categories, POST updates product."""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'error': 'Product not found.'}), 404

    categories = db.session.query(Category).order_by(Category.name).all()

    if request.method == 'GET':
        return jsonify({
            'product': {
                'id': product.id,
                'name': product.name,
                'category_id': product.category_id,
                'cost_price': float(product.cost_price),
                'selling_price': float(product.selling_price),
                'stock_quantity': product.stock_quantity,
                'minimum_stock_alert': product.minimum_stock_alert,
                'supplier_name': product.supplier_name or '',
                'image_path': product.image_path or '',
            },
            'categories': [{'id': c.id, 'name': c.name} for c in categories]
        })

    data = request.get_json() if request.is_json else request.form
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Product name is required.'}), 400

    try:
        if 'category_id' in data:
            product.category_id = int(data.get('category_id'))
        if 'cost_price' in data:
            product.cost_price = float(data.get('cost_price'))
        if 'selling_price' in data:
            product.selling_price = float(data.get('selling_price'))
        if 'stock_quantity' in data:
            product.stock_quantity = int(data.get('stock_quantity'))
        if 'minimum_stock_alert' in data:
            product.minimum_stock_alert = int(data.get('minimum_stock_alert'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid numerical inputs for price or stock.'}), 400

    product.name = name
    if 'supplier_name' in data:
        product.supplier_name = (data.get('supplier_name') or '').strip()

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            try:
                new_image_path = StorageService.upload_file(file)
                if product.image_path:
                    StorageService.delete_file(product.image_path)
                product.image_path = new_image_path
            except ValueError as ve:
                return jsonify({'success': False, 'message': str(ve)}), 400

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': f'Product "{product.name}" updated successfully!'})
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to update product #{product_id}")
        return jsonify({'success': False, 'message': 'Could not update product. Please try again.'}), 500


@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    """Soft-delete (deactivate) a product."""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'error': 'Product not found.'}), 404

    name = product.name
    try:
        product.is_active = False
        _log_action('DEACTIVATE_PRODUCT', 'Product', product_id,
                    details=f'Product "{name}" soft-deleted.')
        db.session.commit()
        return jsonify({'success': True, 'message': f'Product "{name}" has been disabled.'})
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to deactivate product #{product_id}")
        return jsonify({'success': False, 'message': 'Could not disable product. Please try again.'}), 500


@admin_bp.route('/api/product/<int:product_id>')
@admin_required
def get_product_api(product_id):
    """API endpoint — return product details as JSON."""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product.to_dict(is_admin=True))
