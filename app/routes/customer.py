import stripe
from flask import (current_app, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import current_user
from flask_mail import Message

from app.models import db
from app.models.product import Category, Product, Review
from app.models.order import Order, Wishlist
from app.services.cart_service import CartService
from app.services.order_service import OrderService

from . import customer_bp
from .decorators import customer_required
from app.forms.customer import ProfileForm

@customer_bp.route('/')
def index():
    """Public landing page — visible to all visitors"""
    return render_template('landing.html')

@customer_bp.route('/shop')
@customer_required
def shop():
    """Customer shop page with products"""
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    sort_by = request.args.get('sort', '')
    
    query = db.session.query(Product).filter_by(is_active=True)
    
    if search:
        safe_search = search.replace('%', '\\%').replace('_', '\\_')
        query = query.filter(Product.name.ilike(f'%{safe_search}%'))
    if category:
        query = query.join(Product.category_rel).filter(Category.name == category)
    
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    in_stock = request.args.get('in_stock')
    
    if min_price is not None:
        query = query.filter(Product.selling_price >= min_price)
    if max_price is not None:
        query = query.filter(Product.selling_price <= max_price)
    if in_stock == '1':
        query = query.filter(Product.stock_quantity > 0)
        
    if sort_by == 'price_low':
        query = query.order_by(Product.selling_price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.selling_price.desc())
    elif sort_by == 'latest':
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.name.asc())
    
    products = query.all()
    categories = db.session.query(Category).order_by(Category.name).all()
    
    return render_template('customer/shop.html', 
                         products=products,
                         categories=categories,
                         search=search,
                         selected_category=category,
                         sort_by=sort_by)

@customer_bp.route('/product/<int:product_id>')
@customer_required
def product_detail(product_id):
    """Product detail page"""
    product = db.session.query(Product).filter_by(id=product_id, is_active=True).first_or_404()
    return render_template('customer/product_detail.html', product=product)

@customer_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart (Guest and Authenticated)"""
    try:
        quantity = int(request.form.get('quantity', 1))
        success, message = CartService.add_item(product_id, quantity)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    except Exception as e:
        if current_user.is_authenticated:
            db.session.rollback()
        message = f'Error adding to cart: {str(e)}'
        flash(message, 'danger')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': message}), 400
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': message})
        
    return redirect(url_for('customer.view_cart'))

@customer_bp.route('/cart')
def view_cart():
    """View shopping cart"""
    cart_items, total = CartService.get_cart_items()
    return render_template('customer/cart.html', cart_items=cart_items, total=total)

@customer_bp.route('/cart/update/<cart_id>', methods=['POST'])
def update_cart(cart_id):
    """Update cart item quantity"""
    try:
        quantity = int(request.form.get('quantity', 1))
        success, message = CartService.update_item(cart_id, quantity)
        if success:
            flash(message, 'success' if 'updated' in message else 'info')
        else:
            flash(message, 'danger')
    except Exception as e:
        if current_user.is_authenticated:
            db.session.rollback()
        flash(f'Error updating cart: {str(e)}', 'danger')
    return redirect(url_for('customer.view_cart'))

@customer_bp.route('/cart/remove/<cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    """Remove item from cart"""
    try:
        success, message = CartService.remove_item(cart_id)
        if success:
            flash(message, 'info')
        else:
            flash(message, 'danger')
    except Exception as e:
        if current_user.is_authenticated:
            db.session.rollback()
        flash(f'Error removing item: {str(e)}', 'danger')
    return redirect(url_for('customer.view_cart'))

@customer_bp.route('/checkout', methods=['GET', 'POST'])
@customer_required
def checkout():
    """Checkout page"""
    cart_items, total = CartService.get_cart_items()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('customer.shop'))
    
    if request.method == 'POST':
        try:
            shipping_address = request.form.get('shipping_address')
            payment_method = request.form.get('payment_method', 'COD')

            if not shipping_address or len(shipping_address.strip()) < 15:
                flash('Please enter a complete shipping address (minimum 15 characters).', 'danger')
                return redirect(url_for('customer.checkout'))
            
            success, order, message = OrderService.process_checkout(cart_items, shipping_address, payment_method)
            
            if not success:
                flash(message, 'danger')
                return redirect(url_for('customer.view_cart'))
            
            if payment_method == 'UDHAR':
                flash(f'Order placed successfully on Store Credit!', 'success')
                return redirect(url_for('customer.order_confirmation', order_id=order.id))
            elif payment_method in ['UPI', 'CARD']:
                return redirect(url_for('customer.process_payment', order_id=order.id))
            
            # COD Flow - Send email
            try:
                from app import mail
                msg = Message(
                    f"Order Confirmation - #{order.id} | Jay Goga Kirana Store",
                    recipients=[current_user.email]
                )
                msg.html = render_template('emails/order_confirmation.html', order=order, user=current_user)
                mail.send(msg)
            except Exception as e:
                current_app.logger.error(f"Error sending email: {str(e)}")
            
            flash(f'Order placed successfully with Cash on Delivery!', 'success')
            return redirect(url_for('customer.order_confirmation', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error placing order: {str(e)}', 'danger')
            return redirect(url_for('customer.checkout'))
    
    return render_template('customer/checkout.html', cart_items=cart_items, total=total, user=current_user)

@customer_bp.route('/order/confirmation/<int:order_id>')
@customer_required
def order_confirmation(order_id):
    """Order confirmation page"""
    order = db.session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('customer.shop'))
    return render_template('customer/order_confirmation.html', order=order)

@customer_bp.route('/payment/process/<int:order_id>')
@customer_required
def process_payment(order_id):
    """Simulated payment processing page"""
    order = db.session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('customer.shop'))
    return render_template('customer/payment_processing.html', order=order)

@customer_bp.route('/payment/success/<int:order_id>', methods=['POST'])
@customer_required
def payment_success(order_id):
    """Update order after successful simulated payment"""
    order = db.session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        return redirect(url_for('customer.shop'))
    
    # Verify Stripe Session if API key is configured
    session_id = request.args.get('session_id')
    stripe_key = current_app.config.get('STRIPE_SECRET_KEY')
    
    if stripe_key and session_id:
        try:
            stripe.api_key = stripe_key
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                order.payment_status = 'Paid'
                # Record transaction ID if needed
                # order.transaction_id = session.payment_intent
            else:
                flash('Payment verification failed. Please contact support.', 'danger')
                return redirect(url_for('customer.order_confirmation', order_id=order.id))
        except Exception as e:
            current_app.logger.error(f"Stripe verification error: {str(e)}")
            flash('Error verifying payment. We will update your order status once confirmed.', 'warning')
    else:
        # Fallback for demo mode or UPI simulation
        order.payment_status = 'Paid'
    
    db.session.commit()
    
    # Send order confirmation email
    if current_app.config.get('MAIL_USERNAME'):
        try:
            from app import mail
            msg = Message(
                f"Order Confirmation - #{order.id} | Jay Goga Kirana Store",
                recipients=[current_user.email]
            )
            msg.html = render_template('emails/order_confirmation.html', order=order, user=current_user)
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Error sending email: {str(e)}")
            
    flash('Payment successful! Your order has been placed.', 'success')
    return redirect(url_for('customer.order_confirmation', order_id=order.id))

@customer_bp.route('/profile')
@customer_required
def profile():
    """View customer profile"""
    recent_orders = db.session.query(Order).filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    return render_template('customer/profile.html', user=current_user, recent_orders=recent_orders)

@customer_bp.route('/profile/edit', methods=['GET', 'POST'])
@customer_required
def edit_profile():
    """Edit customer profile"""
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('customer.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
    return render_template('customer/edit_profile.html', form=form, user=current_user)

@customer_bp.route('/product/<int:product_id>/review', methods=['POST'])
@customer_required
def submit_review(product_id):
    """Submit a product review"""
    product = db.session.query(Product).filter_by(id=product_id, is_active=True).first_or_404()
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '')
    
    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating (1-5).', 'danger')
        return redirect(url_for('customer.product_detail', product_id=product_id))
    
    existing_review = db.session.query(Review).filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
        flash('Your review has been updated!', 'success')
    else:
        review = Review(user_id=current_user.id, product_id=product_id, rating=rating, comment=comment)
        db.session.add(review)
        flash('Thank you for your review!', 'success')
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting review: {str(e)}', 'danger')
    
    return redirect(url_for('customer.product_detail', product_id=product_id))

@customer_bp.route('/my-orders')
@customer_required
def my_orders():
    """View customer order history"""
    orders = db.session.query(Order).filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('customer/orders.html', orders=orders)

@customer_bp.route('/my-orders/<int:order_id>')
@customer_required
def order_detail(order_id):
    """View specific order details"""
    order = db.session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('customer.my_orders'))
    return render_template('customer/order_detail.html', order=order)

@customer_bp.route('/api/search')
@customer_required
def api_search():
    """API endpoint for live search suggestions"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    safe_search = query.replace('%', '\\%').replace('_', '\\_')
    products = db.session.query(Product).filter(
        Product.is_active == True,
        Product.name.ilike(f'%{safe_search}%')
    ).limit(5).all()
    
    results = []
    for p in products:
        results.append({
            'id': p.id,
            'name': p.name,
            'price': float(p.selling_price),
            'category': p.category_rel.name if p.category_rel else 'Essentials',
            'image': url_for('static', filename=p.image_path) if p.image_path else '',
            'url': url_for('customer.product_detail', product_id=p.id)
        })
    return jsonify(results)

@customer_bp.route('/api/cart')
@customer_required
def api_get_cart():
    """API endpoint to get current cart items and total for the Mini-Cart drawer"""
    cart_items, total = CartService.get_cart_items()
    items = []
    for item in cart_items:
        p = item.product
        items.append({
            'name': p.name,
            'price': float(p.selling_price),
            'quantity': item.quantity,
            'image': p.image_path if p.image_path else 'images/placeholder-product.png',
            'product_id': p.id
        })
    return jsonify({'items': items, 'total': float(total)})

@customer_bp.route('/wishlist')
@customer_required
def view_wishlist():
    items = db.session.query(Wishlist).filter_by(user_id=current_user.id).all()
    return render_template('customer/wishlist.html', items=items)

@customer_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@customer_required
def add_to_wishlist(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('customer.shop'))
        
    exists = db.session.query(Wishlist).filter_by(user_id=current_user.id, product_id=product_id).first()
    if not exists:
        db.session.add(Wishlist(user_id=current_user.id, product_id=product_id))
        db.session.commit()
        flash(f'{product.name} added to your wishlist.', 'success')
    else:
        flash(f'{product.name} is already in your wishlist.', 'info')
    return redirect(request.referrer or url_for('customer.shop'))

@customer_bp.route('/wishlist/remove/<int:id>', methods=['POST'])
@customer_required
def remove_from_wishlist(id):
    item = db.session.get(Wishlist, id)
    if item and item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash('Item removed from wishlist.', 'info')
    return redirect(url_for('customer.view_wishlist'))

@customer_bp.route('/create-checkout-session/<int:order_id>', methods=['POST'])
@customer_required
def create_checkout_session(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(error="Order not found"), 404
        
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY', 'sk_test_dummy')
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': f'Order #{order.id}',
                    },
                    'unit_amount': int(order.total_amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('customer.payment_success', order_id=order.id, _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for('customer.order_confirmation', order_id=order.id, _external=True),
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify(error=str(e)), 403
