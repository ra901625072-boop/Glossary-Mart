"""Admin product management routes (CRUD + API endpoint)."""
from flask import current_app, flash, jsonify, redirect, render_template, request, url_for

from database.models import db
from database.models.product import Category, Product
from backend.services.storage_service import StorageService
from backend.utils.files import allowed_file
from backend.routes.decorators import admin_required
from backend.forms.admin import ProductForm
from .helpers import _log_action
from . import admin_bp


@admin_bp.route('/products')
@admin_required
def products():
    """Product management page."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = db.session.query(Product).filter_by(is_active=True).order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/products.html', products=pagination.items, pagination=pagination)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """Add new product."""
    form = ProductForm()
    categories = db.session.query(Category).order_by(Category.name).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                image_path = StorageService.upload_file(file)

        product = Product(
            name=form.name.data,
            category_id=form.category_id.data,
            cost_price=form.cost_price.data,
            selling_price=form.selling_price.data,
            stock_quantity=form.stock_quantity.data,
            minimum_stock_alert=form.minimum_stock_alert.data,
            supplier_name=form.supplier_name.data,
            image_path=image_path,
        )

        try:
            db.session.add(product)
            db.session.commit()
            flash(f'Product "{product.name}" added successfully!', 'success')
            return redirect(url_for('admin.products'))
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to add product")
            flash('Could not add product. Please try again.', 'danger')

    return render_template('admin/add_product.html', form=form, categories=categories)


@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit product."""
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('admin.products'))

    form = ProductForm(obj=product)
    categories = db.session.query(Category).order_by(Category.name).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        product.name = form.name.data
        product.category_id = form.category_id.data
        product.cost_price = form.cost_price.data
        product.selling_price = form.selling_price.data
        product.stock_quantity = form.stock_quantity.data
        product.minimum_stock_alert = form.minimum_stock_alert.data
        product.supplier_name = form.supplier_name.data

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                if product.image_path:
                    StorageService.delete_file(product.image_path)
                product.image_path = StorageService.upload_file(file)

        try:
            db.session.commit()
            flash(f'Product "{product.name}" updated successfully!', 'success')
            return redirect(url_for('admin.products'))
        except Exception:
            db.session.rollback()
            current_app.logger.exception(f"Failed to update product #{product_id}")
            flash('Could not update product. Please try again.', 'danger')

    return render_template('admin/edit_product.html', form=form, product=product, categories=categories)


@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    """Soft-delete (deactivate) a product."""
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('admin.products'))

    name = product.name
    try:
        product.is_active = False
        _log_action('DEACTIVATE_PRODUCT', 'Product', product_id,
                    details=f'Product "{name}" soft-deleted.')
        db.session.commit()
        flash(f'Product "{name}" has been disabled.', 'success')
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to deactivate product #{product_id}")
        flash('Could not disable product. Please try again.', 'danger')

    return redirect(url_for('admin.products'))


@admin_bp.route('/api/product/<int:product_id>')
@admin_required
def get_product_api(product_id):
    """API endpoint — return product details as JSON."""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product.to_dict())
