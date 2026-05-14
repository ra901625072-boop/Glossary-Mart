from datetime import datetime, timedelta

from flask import (Response, current_app, flash, jsonify, make_response,
                   redirect, render_template, request, url_for)

from app.models import db
from app.models.user import ActivityLog, User
from app.models.product import Category, Product, Sale
from app.models.order import Order, OrderItem
from app.models.inventory import Supplier, Purchase
from app.models.promotion import Coupon, Notification
from app.services.inventory_service import InventoryService
from app.services.storage_service import StorageService
from app.services.stats_service import (
    get_chart_data, get_monthly_comparison, get_sales_stats, 
    get_stock_stats, get_yearly_comparison
)
from app.services.export_service import generate_sales_csv, generate_sales_pdf
from app.utils.files import allowed_file

from . import admin_bp
from .decorators import admin_required
from app.forms.admin import CategoryForm, ProductForm, PurchaseForm, SupplierForm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_action(action: str, entity_type: str, entity_id: int, details: str = "") -> None:
    """Persist an audit log entry for a critical admin action."""
    from flask import request as flask_request
    from flask_login import current_user
    try:
        ip = flask_request.remote_addr
    except RuntimeError:
        ip = None
    db.session.add(ActivityLog(
        user_id=current_user.id if current_user and current_user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip,
    ))


def _create_notification(title: str, message: str, notif_type: str = "info", link: str = None) -> None:
    """Create a broadcast admin notification (not user-specific)."""
    db.session.add(Notification(
        user_id=None,
        title=title,
        message=message,
        notif_type=notif_type,
        link=link,
    ))


@admin_bp.route('/')
@admin_required
def admin_base():
    """Redirect /admin to /admin/dashboard"""
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Analytics dashboard"""
    stats_1_day = get_sales_stats(1)
    stats_7_days = get_sales_stats(7)
    stats_30_days = get_sales_stats(30)
    monthly_comparison = get_monthly_comparison()
    yearly_comparison = get_yearly_comparison()
    chart_data = get_chart_data(30)
    stock_stats = get_stock_stats()
    
    # Use SQL aggregation instead of loading all orders into memory
    from sqlalchemy import func
    order_stats = db.session.query(
        func.count(Order.id).label('total_orders'),
        func.coalesce(func.sum(Order.total_amount), 0).label('total_revenue')
    ).first()
    
    pending_orders = db.session.query(func.count(Order.id)).filter(
        Order.order_status == 'Pending'
    ).scalar() or 0
    
    # Calculate total order profit via OrderItem (since Order.total_profit is a property)
    # OrderItem already imported at module level
    total_order_profit = db.session.query(
        func.coalesce(func.sum(OrderItem.profit), 0)
    ).join(Order).filter(
        Order.order_status != 'Cancelled'
    ).scalar() or 0
    
    return render_template(
        'admin/dashboard.html',
        stats_1_day=stats_1_day,
        stats_7_days=stats_7_days,
        stats_30_days=stats_30_days,
        monthly_comparison=monthly_comparison,
        yearly_comparison=yearly_comparison,
        chart_data=chart_data,
        stock_stats=stock_stats,
        total_orders=order_stats.total_orders,
        total_order_revenue=float(order_stats.total_revenue),
        total_order_profit=float(total_order_profit),
        pending_orders=pending_orders
    )

@admin_bp.route('/products')
@admin_required
def products():
    """Product management page"""
    products = db.session.query(Product).filter_by(is_active=True).order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """Add new product"""
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
            image_path=image_path
        )
        
        try:
            db.session.add(product)
            db.session.commit()
            flash(f'Product "{product.name}" added successfully!', 'success')
            return redirect(url_for('admin.products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
    
    return render_template('admin/add_product.html', form=form, categories=categories)

@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit product"""
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
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
    
    return render_template('admin/edit_product.html', form=form, product=product, categories=categories)

@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    """Soft delete product"""
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
    except Exception as e:
        db.session.rollback()
        flash(f'Error disabling product: {str(e)}', 'danger')

    return redirect(url_for('admin.products'))

@admin_bp.route('/sales', methods=['GET', 'POST'])
@admin_required
def sales():
    """Sales entry page"""
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

        sale = Sale(
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
            profit=profit
        )

        ok, msg = InventoryService.deduct_stock(product_id, quantity, triggered_by='manual_sale')
        if not ok:
            flash(msg, 'danger')
            return redirect(url_for('admin.sales'))

        try:
            db.session.add(sale)
            db.session.commit()
            flash(f'Sale recorded! Profit: ₹{profit:.2f}', 'success')
            return redirect(url_for('admin.view_bill', sale_id=sale.id, print=1))
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording sale: {str(e)}', 'danger')

        return redirect(url_for('admin.sales'))
    
    products = db.session.query(Product).filter(Product.stock_quantity > 0).order_by(Product.name).all()
    return render_template('admin/sales.html', products=products)

@admin_bp.route('/sales/history')
@admin_required
def sales_history():
    """Sales history page"""
    sales = db.session.query(Sale).order_by(Sale.sale_date.desc()).limit(100).all()
    return render_template('admin/sales_history.html', sales=sales)

@admin_bp.route('/sales/export')
@admin_required
def export_sales():
    """Export sales data as CSV or PDF"""
    # Services already imported at module level
    
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
            # Include the full end day
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Sale.sale_date < end_date)
        except ValueError:
            flash('Invalid end date format.', 'danger')
            return redirect(url_for('admin.sales_history'))
        
    sales = query.order_by(Sale.sale_date.desc()).all()
    
    if not sales:
        flash('No sales records found for the selected period.', 'info')
        return redirect(url_for('admin.sales_history'))
        
    filename_prefix = f"sales_report_{datetime.now().strftime('%Y%m%d')}"
    
    if export_format == 'csv':
        csv_data = generate_sales_csv(sales)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename_prefix}.csv"}
        )
    elif export_format == 'pdf':
        pdf_data = generate_sales_pdf(sales, start_date_str, end_date_str)
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={filename_prefix}.pdf'
        return response
        
    return redirect(url_for('admin.sales_history'))

@admin_bp.route('/sales/bill/<int:sale_id>')
@admin_required
def view_bill(sale_id):
    """Printable bill for a sale"""
    sale = db.session.get(Sale, sale_id)
    if not sale:
        flash("Sale record not found.", "danger")
        return redirect(url_for('admin.sales_history'))
    return render_template('admin/bill.html', sale=sale)

@admin_bp.route('/orders')
@admin_required
def admin_orders():
    """Admin view of all customer orders"""
    orders = db.session.query(Order).order_by(Order.created_at.desc()).all()
    total_orders = len(orders)
    pending_orders = sum(1 for o in orders if o.order_status == 'Pending')
    total_revenue = sum(o.total_amount for o in orders)
    
    return render_template('admin/admin_orders.html', 
                         orders=orders,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         total_revenue=total_revenue)

@admin_bp.route('/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    """Admin view of order details"""
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for('admin.admin_orders'))
    return render_template('admin/admin_order_detail.html', order=order)

@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """Update order status"""
    ALLOWED_ORDER_STATUS = [
        'Pending', 'Processing', 'Packed',
        'Out for Delivery', 'Delivered', 'Cancelled', 'Returned'
    ]
    ALLOWED_PAYMENT_STATUS = ['Pending', 'Paid', 'Failed', 'Refunded']

    # State-machine: defines valid forward transitions
    VALID_TRANSITIONS = {
        'Pending':          {'Processing', 'Cancelled'},
        'Processing':       {'Packed', 'Cancelled'},
        'Packed':           {'Out for Delivery', 'Cancelled'},
        'Out for Delivery': {'Delivered', 'Returned'},
        'Delivered':        {'Returned'},
        'Cancelled':        set(),  # Terminal
        'Returned':         set(),  # Terminal
    }

    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for('admin.admin_orders'))

    new_status = request.form.get('order_status')
    payment_status = request.form.get('payment_status')

    if new_status and new_status not in ALLOWED_ORDER_STATUS:
        flash(f'Invalid order status.', 'danger')
        return redirect(url_for('admin.admin_order_detail', order_id=order_id))

    if payment_status and payment_status not in ALLOWED_PAYMENT_STATUS:
        flash(f'Invalid payment status.', 'danger')
        return redirect(url_for('admin.admin_order_detail', order_id=order_id))

    if new_status and new_status != order.order_status:
        allowed = VALID_TRANSITIONS.get(order.order_status, set())
        if new_status not in allowed:
            flash(
                f'Invalid transition: cannot move order from "{order.order_status}" '
                f'to "{new_status}". Allowed next states: {", ".join(allowed) or "None"}.',
                'danger'
            )
            return redirect(url_for('admin.admin_order_detail', order_id=order_id))

    # Restore stock on Cancellation or Return (only on first transition)
    if new_status in ('Cancelled', 'Returned') and order.order_status not in ('Cancelled', 'Returned'):
        InventoryService.restore_order_stock(order)

    prev_status = order.order_status
    prev_payment = order.payment_status

    if new_status:
        order.order_status = new_status
    if payment_status:
        order.payment_status = payment_status

    _log_action(
        'UPDATE_ORDER_STATUS', 'Order', order_id,
        details=(
            f'Status: {prev_status} → {order.order_status} | '
            f'Payment: {prev_payment} → {order.payment_status}'
        )
    )

    try:
        db.session.commit()
        flash(f'Order #{order.id} updated: {order.order_status} / {order.payment_status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating order: {str(e)}', 'danger')

    return redirect(url_for('admin.admin_order_detail', order_id=order_id))

@admin_bp.route('/api/product/<int:product_id>')
@admin_required
def get_product_api(product_id):
    """API endpoint to get product details"""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product.to_dict())

@admin_bp.route('/categories')
@admin_required
def categories():
    """Category management page"""
    categories = db.session.query(Category).order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def add_category():
    """Add new category"""
    form = CategoryForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        
        existing = db.session.query(Category).filter_by(name=name).first()
        if existing:
            flash(f'Category "{name}" already exists.', 'warning')
            return redirect(url_for('admin.add_category'))
        
        category = Category(name=name, description=description)
        try:
            db.session.add(category)
            db.session.commit()
            flash(f'Category "{name}" added successfully!', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding category: {str(e)}', 'danger')
    
    return render_template('admin/add_category.html', form=form)

@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    """Edit category"""
    category = db.session.get(Category, category_id)
    if not category:
        flash("Category not found.", "danger")
        return redirect(url_for('admin.categories'))
        
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        
        existing = db.session.query(Category).filter(Category.name == name, Category.id != category_id).first()
        if existing:
            flash(f'Category "{name}" already exists.', 'warning')
            return redirect(url_for('admin.edit_category', category_id=category_id))
        
        category.name = name
        category.description = description
        
        try:
            db.session.commit()
            flash(f'Category "{name}" updated successfully!', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {str(e)}', 'danger')
    
    return render_template('admin/edit_category.html', form=form, category=category)

@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def delete_category(category_id):
    """Delete category"""
    category = db.session.get(Category, category_id)
    if not category:
        flash("Category not found.", "danger")
        return redirect(url_for('admin.categories'))
        
    name = category.name
    
    # Check if category is used by products
    if category.products:
        flash(f'Cannot delete category "{name}" because it is associated with products.', 'danger')
        return redirect(url_for('admin.categories'))
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'danger')
        
    return redirect(url_for('admin.categories'))

# --- Supplier Management ---
@admin_bp.route('/suppliers')
@admin_required
def suppliers():
    """Supplier management page"""
    suppliers_list = db.session.query(Supplier).order_by(Supplier.name).all()
    return render_template('admin/suppliers.html', suppliers=suppliers_list)

@admin_bp.route('/suppliers/add', methods=['GET', 'POST'])
@admin_required
def add_supplier():
    """Add new supplier"""
    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data
        )
        try:
            db.session.add(supplier)
            db.session.commit()
            flash(f'Supplier "{supplier.name}" added successfully!', 'success')
            return redirect(url_for('admin.suppliers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding supplier: {str(e)}', 'danger')
    return render_template('admin/add_supplier.html', form=form)

@admin_bp.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
@admin_required
def edit_supplier(supplier_id):
    """Edit supplier"""
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        flash("Supplier not found.", "danger")
        return redirect(url_for('admin.suppliers'))
        
    form = SupplierForm(obj=supplier)
    
    if form.validate_on_submit():
        supplier.name = form.name.data
        supplier.contact_person = form.contact_person.data
        supplier.phone = form.phone.data
        supplier.email = form.email.data
        supplier.address = form.address.data
        
        try:
            db.session.commit()
            flash(f'Supplier "{supplier.name}" updated successfully!', 'success')
            return redirect(url_for('admin.suppliers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating supplier: {str(e)}', 'danger')
    
    return render_template('admin/edit_supplier.html', form=form, supplier=supplier)

@admin_bp.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
@admin_required
def delete_supplier(supplier_id):
    """Delete supplier"""
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        flash("Supplier not found.", "danger")
        return redirect(url_for('admin.suppliers'))
        
    name = supplier.name
    
    if supplier.purchases:
        flash(f'Cannot delete supplier "{name}" because it is linked to past purchases.', 'danger')
        return redirect(url_for('admin.suppliers'))
    
    try:
        db.session.delete(supplier)
        db.session.commit()
        flash(f'Supplier "{name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting supplier: {str(e)}', 'danger')
        
    return redirect(url_for('admin.suppliers'))

# --- Purchase Management ---
@admin_bp.route('/purchases')
@admin_required
def purchases():
    """Purchase tracking page"""
    purchases_list = db.session.query(Purchase).order_by(Purchase.purchase_date.desc()).all()
    return render_template('admin/purchases.html', purchases=purchases_list)

@admin_bp.route('/purchases/add', methods=['GET', 'POST'])
@admin_required
def add_purchase():
    """Add new purchase (increases stock)"""
    form = PurchaseForm()
    
    suppliers = db.session.query(Supplier).order_by(Supplier.name).all()
    form.supplier_id.choices = [(s.id, s.name) for s in suppliers]
    
    products = db.session.query(Product).filter_by(is_active=True).order_by(Product.name).all()
    form.product_id.choices = [(p.id, p.name) for p in products]
    
    if not suppliers:
        flash('Please add a supplier first before recording a purchase.', 'warning')
        return redirect(url_for('admin.add_supplier'))
        
    if not products:
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
            total_cost=total_cost
        )
        
        # Increase product stock
        product.stock_quantity += quantity
        
        # Optionally update product cost_price and supplier info based on latest purchase
        product.cost_price = price_per_unit
        product.supplier_name = purchase.supplier.name if purchase.supplier else product.supplier_name
        
        try:
            db.session.add(purchase)
            db.session.commit()
            flash(f'Purchase recorded successfully! Stock increased by {quantity}.', 'success')
            return redirect(url_for('admin.purchases'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording purchase: {str(e)}', 'danger')
    
    return render_template('admin/add_purchase.html', form=form)

# --- Customer & Credit Management ---
@admin_bp.route('/customers')
@admin_required
def customers():
    """View customers and their credit balances"""
    customers_list = db.session.query(User).filter_by(role='customer').order_by(User.full_name).all()
    return render_template('admin/customers.html', customers=customers_list)

@admin_bp.route('/customers/<int:user_id>/clear_credit', methods=['POST'])
@admin_required
def clear_credit(user_id):
    """Clear (settle) customer credit balance"""
    customer = db.session.get(User, user_id)
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for('admin.customers'))
    
    amount_paid_str = request.form.get('amount_paid')
    if not amount_paid_str:
        flash('Amount is required.', 'danger')
        return redirect(url_for('admin.customers'))
        
    try:
        amount_paid = float(amount_paid_str)
        if amount_paid <= 0:
            flash('Amount must be strictly positive.', 'danger')
            return redirect(url_for('admin.customers'))
            
        if float(customer.credit) < amount_paid:
            flash(f'Amount paid ({amount_paid}) cannot be more than the current credit balance ({customer.credit}).', 'danger')
            return redirect(url_for('admin.customers'))
            
        customer.credit = float(customer.credit) - amount_paid
        db.session.commit()
        flash(f'Successfully cleared ₹{amount_paid:.2f} credit for {customer.full_name or customer.username}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing credit: {str(e)}', 'danger')
        
    return redirect(url_for('admin.customers'))

@admin_bp.route('/pos')
@admin_required
def pos():
    products = db.session.query(Product).filter(Product.stock_quantity > 0, Product.is_active == True).all()
    return render_template('admin/pos.html', products=products)

@admin_bp.route('/api/pos/checkout', methods=['POST'])
@admin_required
def pos_checkout():
    data = request.json
    cart_items = data.get('cart', [])
    total_paid = 0
    
    try:
        for item in cart_items:
            product = db.session.get(Product, item['id'])
            if product and product.stock_quantity >= item['qty']:
                qty = item['qty']
                profit = (product.selling_price - product.cost_price) * qty
                ok, msg = InventoryService.deduct_stock(product.id, qty, triggered_by='pos')
                if not ok:
                    db.session.rollback()
                    return jsonify({'success': False, 'error': msg})
                sale = Sale(product_id=product.id, quantity=qty, total_price=product.selling_price * qty, profit=profit)
                db.session.add(sale)
                total_paid += float(product.selling_price * qty)
            else:
                db.session.rollback()
                name = product.name if product else f'Product #{item["id"]}'
                return jsonify({'success': False, 'error': f'Insufficient stock for {name}.'})
        db.session.commit()
        return jsonify({'success': True, 'total': total_paid})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/coupons')
@admin_required
def coupons():
    coupons = db.session.query(Coupon).all()
    return render_template('admin/coupons.html', coupons=coupons)


# ---------------------------------------------------------------------------
# Notification API
# ---------------------------------------------------------------------------

@admin_bp.route('/api/notifications')
@admin_required
def api_notifications():
    """Return the 20 most recent admin notifications with unread count."""
    notifications = (
        db.session.query(Notification)
        .filter(Notification.user_id.is_(None))   # Broadcast notifications
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )
    unread_count = db.session.query(Notification).filter(
        Notification.user_id.is_(None),
        Notification.is_read == False
    ).count()

    return jsonify({
        'unread_count': unread_count,
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'notif_type': n.notif_type,
                'is_read': n.is_read,
                'link': n.link or '',
                'created_at': n.created_at.strftime('%d %b %Y, %I:%M %p'),
            }
            for n in notifications
        ],
    })


@admin_bp.route('/api/notifications/mark-read', methods=['POST'])
@admin_required
def api_notifications_mark_read():
    """Mark all broadcast notifications as read."""
    db.session.query(Notification).filter(
        Notification.user_id.is_(None),
        Notification.is_read == False
    ).update({'is_read': True}, synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Activity Log Viewer
# ---------------------------------------------------------------------------

@admin_bp.route('/activity-log')
@admin_required
def activity_log():
    """Admin audit log viewer — last 200 entries, filterable by action."""
    action_filter = request.args.get('action', '')
    query = db.session.query(ActivityLog).order_by(ActivityLog.created_at.desc())
    if action_filter:
        query = query.filter(ActivityLog.action == action_filter)
    logs = query.limit(200).all()

    # Distinct action types for filter dropdown
    action_types = [
        row[0] for row in
        db.session.query(ActivityLog.action).distinct().order_by(ActivityLog.action).all()
    ]
    return render_template(
        'admin/activity_log.html',
        logs=logs,
        action_types=action_types,
        action_filter=action_filter,
    )
