"""Admin purchase management routes (record stock-in, list purchases)."""
from flask import current_app, flash, redirect, render_template, url_for

from database.models import db
from database.models.product import Product
from database.models.inventory import Supplier, Purchase
from backend.routes.decorators import admin_required
from backend.forms.admin import PurchaseForm
from . import admin_bp


@admin_bp.route('/purchases')
@admin_required
def purchases():
    """Purchase tracking page."""
    purchases_list = db.session.query(Purchase).order_by(Purchase.purchase_date.desc()).all()
    return render_template('admin/purchases.html', purchases=purchases_list)


@admin_bp.route('/purchases/add', methods=['GET', 'POST'])
@admin_required
def add_purchase():
    """Record a new stock purchase (increases product stock)."""
    form = PurchaseForm()

    suppliers_list = db.session.query(Supplier).order_by(Supplier.name).all()
    form.supplier_id.choices = [(s.id, s.name) for s in suppliers_list]

    products_list = db.session.query(Product).filter_by(is_active=True).order_by(Product.name).all()
    form.product_id.choices = [(p.id, p.name) for p in products_list]

    if not suppliers_list:
        flash('Please add a supplier first before recording a purchase.', 'warning')
        return redirect(url_for('admin.add_supplier'))

    if not products_list:
        flash('Please add a product first before recording a purchase.', 'warning')
        return redirect(url_for('admin.add_product'))

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
            flash(f'Purchase recorded! Stock increased by {quantity}.', 'success')
            return redirect(url_for('admin.purchases'))
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to record purchase")
            flash('Could not record purchase. Please try again.', 'danger')

    return render_template('admin/add_purchase.html', form=form)
