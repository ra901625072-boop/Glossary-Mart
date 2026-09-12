import stripe
from flask import current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from flask_mail import Message

from backend.extensions import mail
from database.models import db
from database.models.product import Category, Product, Review
from database.models.order import Order, Wishlist
from backend.services.cart_service import CartService
from backend.services.order_service import OrderService

from . import customer_bp
from .decorators import customer_required
from .pages import serve_frontend_page

@customer_bp.route('/favicon.ico')
def favicon():
    return '', 204

@customer_bp.route('/')
@customer_bp.route('/index.html')
def index():
    """Backend API Root — returns backend online status (matching standalone API mode)"""
    frontend_url = current_app.config.get('FRONTEND_URL', 'https://glossary-mart.vercel.app')
    return jsonify({
        "status": "online",
        "message": "e Grossary API Backend is running. Frontend is hosted separately on Vercel.",
        "frontend_url": frontend_url,
        "version": "1.0.0"
    }), 200

@customer_bp.route('/customer')
@customer_bp.route('/customer.html')
def customer_portal():
    """Customer Portal Route — returns backend status indicating frontend is separate"""
    return serve_frontend_page('customer.html')

@customer_bp.route('/admin.html')
def admin_html():
    """Admin ERP Route — returns backend status indicating frontend is separate"""
    return serve_frontend_page('admin.html')

@customer_bp.route('/api-portal')
def api_portal():
    """Backend service portal and API documentation page"""
    frontend_url = current_app.config.get('FRONTEND_URL', 'https://glossary-mart.vercel.app')
    return jsonify({
        'service': 'e Grossary Backend API',
        'status': 'healthy',
        'frontend_url': frontend_url,
        'endpoints': {
            'health': '/api/health',
            'products': '/api/products',
            'cart': '/api/cart',
            'cart_add': '/api/cart/add',
            'checkout': '/api/orders/checkout',
        },
        'admin_login': '/auth/admin/login',
    })

@customer_bp.route('/orders')
def orders_redirect():
    """Convenience alias redirecting /orders to /my-orders"""
    return redirect(url_for('customer.my_orders'))

@customer_bp.route('/shop')
@customer_required
def shop():
    """Customer shop page — returns JSON product data for SPA."""
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
    
    return jsonify({
        'products': [
            {
                'id': p.id,
                'name': p.name,
                'category': p.category_rel.name if p.category_rel else 'General',
                'selling_price': float(p.selling_price),
                'cost_price': float(p.cost_price),
                'stock_quantity': p.stock_quantity,
                'image_path': p.image_path or '',
                'created_at': p.created_at.isoformat() if p.created_at else None,
            }
            for p in products
        ],
        'categories': [{'id': c.id, 'name': c.name} for c in categories],
        'filters': {
            'search': search,
            'category': category,
            'sort': sort_by,
        }
    })

@customer_bp.route('/product/<int:product_id>')
@customer_required
def product_detail(product_id):
    """Product detail — returns JSON for SPA."""
    product = db.session.query(Product).filter_by(id=product_id, is_active=True).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    reviews = []
    if hasattr(product, 'reviews'):
        reviews = [
            {
                'id': r.id,
                'user': r.user.username if r.user else 'Anonymous',
                'rating': r.rating,
                'comment': r.comment,
                'created_at': r.created_at.isoformat() if r.created_at else None,
            }
            for r in product.reviews
        ]
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'category': product.category_rel.name if product.category_rel else 'General',
        'selling_price': float(product.selling_price),
        'cost_price': float(product.cost_price),
        'stock_quantity': product.stock_quantity,
        'image_path': product.image_path or '',
        'description': getattr(product, 'description', '') or '',
        'reviews': reviews,
    })

@customer_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart (Guest and Authenticated)"""
    try:
        # Support both form data and JSON
        if request.is_json:
            quantity = int(request.json.get('quantity', 1))
        else:
            quantity = int(request.form.get('quantity', 1))
        success, message = CartService.add_item(product_id, quantity)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': success, 'message': message}), 200 if success else 400
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
    except Exception as e:
        if current_user.is_authenticated:
            db.session.rollback()
        message = f'Error adding to cart: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': message}), 400
        flash(message, 'danger')
    
    return redirect(url_for('customer.view_cart'))

@customer_bp.route('/cart')
def view_cart():
    """View shopping cart — returns JSON for SPA."""
    cart_items, total = CartService.get_cart_items()
    items = []
    for item in cart_items:
        p = item.product
        items.append({
            'cart_id': item.id if hasattr(item, 'id') else str(p.id),
            'product_id': p.id,
            'name': p.name,
            'price': float(p.selling_price),
            'quantity': item.quantity,
            'subtotal': float(p.selling_price * item.quantity),
            'image': p.image_path or '',
            'stock_available': p.stock_quantity,
        })
    return jsonify({'items': items, 'total': float(total)})

@customer_bp.route('/cart/update/<cart_id>', methods=['POST'])
def update_cart(cart_id):
    """Update cart item quantity"""
    try:
        if request.is_json:
            quantity = int(request.json.get('quantity', 1))
        else:
            quantity = int(request.form.get('quantity', 1))
        success, message = CartService.update_item(cart_id, quantity)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': success, 'message': message}), 200 if success else 400
        if success:
            flash(message, 'success' if 'updated' in message else 'info')
        else:
            flash(message, 'danger')
    except Exception as e:
        if current_user.is_authenticated:
            db.session.rollback()
        msg = f'Error updating cart: {str(e)}'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'danger')
    return redirect(url_for('customer.view_cart'))

@customer_bp.route('/cart/remove/<cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    """Remove item from cart"""
    try:
        success, message = CartService.remove_item(cart_id)
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': success, 'message': message}), 200 if success else 400
        if success:
            flash(message, 'info')
        else:
            flash(message, 'danger')
    except Exception as e:
        if current_user.is_authenticated:
            db.session.rollback()
        msg = f'Error removing item: {str(e)}'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'danger')
    return redirect(url_for('customer.view_cart'))

@customer_bp.route('/checkout', methods=['GET', 'POST'])
@customer_required
def checkout():
    """Checkout — GET returns cart summary JSON, POST processes order."""
    cart_items, total = CartService.get_cart_items()
    if not cart_items:
        if request.is_json:
            return jsonify({'error': 'Your cart is empty.'}), 400
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('customer.shop'))
    
    if request.method == 'GET':
        # Return cart data for the SPA checkout page
        items = []
        for item in cart_items:
            p = item.product
            items.append({
                'product_id': p.id,
                'name': p.name,
                'price': float(p.selling_price),
                'quantity': item.quantity,
                'subtotal': float(p.selling_price * item.quantity),
            })
        return jsonify({
            'items': items,
            'total': float(total),
            'user': {
                'full_name': current_user.full_name or '',
                'email': current_user.email or '',
                'phone': current_user.phone or '',
                'address': current_user.address or '',
            }
        })
    
    # POST — process checkout
    try:
        if request.is_json:
            shipping_address = request.json.get('shipping_address', '')
            payment_method = request.json.get('payment_method', 'COD')
        else:
            shipping_address = request.form.get('shipping_address')
            payment_method = request.form.get('payment_method', 'COD')

        if not shipping_address or len(shipping_address.strip()) < 15:
            msg = 'Please enter a complete shipping address (minimum 15 characters).'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('customer.checkout'))
        
        success, order, message = OrderService.process_checkout(cart_items, shipping_address, payment_method)
        
        if not success:
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 400
            flash(message, 'danger')
            return redirect(url_for('customer.view_cart'))
        
        if payment_method == 'UDHAR':
            if request.is_json:
                return jsonify({'success': True, 'order_id': order.id, 'message': 'Order placed on Store Credit!', 'redirect': url_for('customer.order_confirmation', order_id=order.id)})
            flash(f'Order placed successfully on Store Credit!', 'success')
            return redirect(url_for('customer.order_confirmation', order_id=order.id))
        elif payment_method in ['UPI', 'CARD']:
            if request.is_json:
                return jsonify({'success': True, 'order_id': order.id, 'redirect': url_for('customer.process_payment', order_id=order.id)})
            return redirect(url_for('customer.process_payment', order_id=order.id))
        
        # COD Flow - Send email
        try:
            msg = Message(
                f"Order Confirmation - #{order.id} | e Grossary Store",
                recipients=[current_user.email]
            )
            msg.html = render_template('emails/order_confirmation.html', order=order, user=current_user)
            mail.send(msg)
        except Exception:
            current_app.logger.exception(f"Failed to send order confirmation email for order #{order.id}")
        
        if request.is_json:
            return jsonify({'success': True, 'order_id': order.id, 'message': 'Order placed with Cash on Delivery!', 'redirect': url_for('customer.order_confirmation', order_id=order.id)})
        flash(f'Order placed successfully with Cash on Delivery!', 'success')
        return redirect(url_for('customer.order_confirmation', order_id=order.id))
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Checkout failed")
        if request.is_json:
            return jsonify({'success': False, 'message': 'Could not place your order. Please try again.'}), 500
        flash('Could not place your order. Please try again.', 'danger')
        return redirect(url_for('customer.checkout'))

@customer_bp.route('/order/confirmation/<int:order_id>')
@customer_required
def order_confirmation(order_id):
    """Order confirmation — returns JSON."""
    order = db.session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access.'}), 403
    return jsonify({
        'order_id': order.id,
        'total_amount': float(order.total_amount),
        'order_status': order.order_status,
        'payment_status': order.payment_status,
        'payment_method': order.payment_method,
        'shipping_address': order.shipping_address or '',
        'created_at': order.created_at.isoformat() if order.created_at else None,
    })

@customer_bp.route('/payment/process/<int:order_id>')
@customer_required
def process_payment(order_id):
    """Simulated payment processing — returns JSON with payment info."""
    order = db.session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access.'}), 403
    return jsonify({
        'order_id': order.id,
        'total_amount': float(order.total_amount),
        'payment_method': order.payment_method,
        'payment_status': order.payment_status,
        'stripe_publishable_key': current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''),
    })

@customer_bp.route('/payment/success/<int:order_id>', methods=['POST'])
@customer_required
def payment_success(order_id):
    """Update order after successful simulated payment"""
    order = db.session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        if request.is_json:
            return jsonify({'error': 'Unauthorized.'}), 403
        return redirect(url_for('customer.shop'))
    
    # Verify Stripe Session if API key is configured
    session_id = request.args.get('session_id')
    stripe_key = current_app.config.get('STRIPE_SECRET_KEY')
    
    if stripe_key:
        if not session_id:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Invalid or missing payment session.'}), 400
            flash('Invalid or missing payment session.', 'danger')
            return redirect(url_for('customer.order_confirmation', order_id=order.id))
            
        try:
            stripe.api_key = stripe_key
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                order.payment_status = 'Paid'
            else:
                msg = 'Payment verification failed. Please contact support.'
                if request.is_json:
                    return jsonify({'success': False, 'message': msg}), 400
                flash(msg, 'danger')
                return redirect(url_for('customer.order_confirmation', order_id=order.id))
        except Exception as e:
            current_app.logger.error(f"Stripe verification error: {str(e)}")
            msg = 'Error verifying payment. We will update your order status once confirmed.'
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'warning')
            return redirect(url_for('customer.order_confirmation', order_id=order.id))
    else:
        # Fallback for demo mode (only executes if NO Stripe key is configured server-side)
        order.payment_status = 'Paid'
    
    db.session.commit()
    
    # Send order confirmation email
    if current_app.config.get('MAIL_USERNAME'):
        try:
            msg = Message(
                f"Order Confirmation - #{order.id} | e Grossary Store",
                recipients=[current_user.email]
            )
            msg.html = render_template('emails/order_confirmation.html', order=order, user=current_user)
            mail.send(msg)
        except Exception:
            current_app.logger.exception(f"Failed to send payment confirmation email for order #{order.id}")
            
    if request.is_json:
        return jsonify({'success': True, 'message': 'Payment successful! Your order has been placed.', 'order_id': order.id})
    flash('Payment successful! Your order has been placed.', 'success')
    return redirect(url_for('customer.order_confirmation', order_id=order.id))

@customer_bp.route('/profile')
@customer_required
def profile():
    """View customer profile — returns JSON."""
    recent_orders = db.session.query(Order).filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    return jsonify({
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'full_name': current_user.full_name or '',
            'phone': current_user.phone or '',
            'address': current_user.address or '',
        },
        'recent_orders': [
            {
                'id': o.id,
                'total_amount': float(o.total_amount),
                'order_status': o.order_status,
                'payment_status': o.payment_status,
                'created_at': o.created_at.isoformat() if o.created_at else None,
            }
            for o in recent_orders
        ]
    })

@customer_bp.route('/profile/edit', methods=['GET', 'POST'])
@customer_required
def edit_profile():
    """Edit customer profile — JSON API."""
    if request.method == 'GET':
        return jsonify({
            'username': current_user.username,
            'email': current_user.email,
            'full_name': current_user.full_name or '',
            'phone': current_user.phone or '',
            'address': current_user.address or '',
        })
    
    # POST — update profile
    data = request.get_json() if request.is_json else request.form
    if 'full_name' in data:
        current_user.full_name = data.get('full_name', '').strip()
    if 'email' in data and data.get('email'):
        current_user.email = data.get('email', '').strip().lower()
    if 'phone' in data:
        current_user.phone = data.get('phone', '').strip()
    if 'address' in data:
        current_user.address = data.get('address', '').strip()
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully!'})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update profile")
        return jsonify({'success': False, 'message': 'Could not update profile.'}), 500

@customer_bp.route('/product/<int:product_id>/review', methods=['POST'])
@customer_required
def submit_review(product_id):
    """Submit a product review"""
    product = db.session.query(Product).filter_by(id=product_id, is_active=True).first()
    if not product:
        if request.is_json:
            return jsonify({'error': 'Product not found.'}), 404
        flash('Product not found.', 'danger')
        return redirect(url_for('customer.shop'))
    
    if request.is_json:
        rating = request.json.get('rating', type=int) if hasattr(request.json.get('rating', 0), '__int__') else None
        comment = request.json.get('comment', '')
        try:
            rating = int(request.json.get('rating'))
        except (TypeError, ValueError):
            rating = None
    else:
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment', '')
    
    if not rating or rating < 1 or rating > 5:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Please provide a valid rating (1-5).'}), 400
        flash('Please provide a valid rating (1-5).', 'danger')
        return redirect(url_for('customer.product_detail', product_id=product_id))
    
    existing_review = db.session.query(Review).filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
        msg = 'Your review has been updated!'
    else:
        review = Review(user_id=current_user.id, product_id=product_id, rating=rating, comment=comment)
        db.session.add(review)
        msg = 'Thank you for your review!'
    
    try:
        db.session.commit()
        if request.is_json:
            return jsonify({'success': True, 'message': msg})
        flash(msg, 'success')
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to submit review for product #{product_id}")
        if request.is_json:
            return jsonify({'success': False, 'message': 'Could not submit review.'}), 500
        flash('Could not submit review. Please try again.', 'danger')
    
    return redirect(url_for('customer.product_detail', product_id=product_id))

@customer_bp.route('/my-orders')
@customer_required
def my_orders():
    """View customer order history — returns JSON."""
    orders = db.session.query(Order).filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return jsonify({
        'orders': [
            {
                'id': o.id,
                'total_amount': float(o.total_amount),
                'order_status': o.order_status,
                'payment_status': o.payment_status,
                'payment_method': o.payment_method,
                'created_at': o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ]
    })

@customer_bp.route('/my-orders/<int:order_id>')
@customer_required
def order_detail(order_id):
    """View specific order details — returns JSON."""
    order = db.session.get(Order, order_id)
    if not order or order.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access.'}), 403
    
    items = []
    if hasattr(order, 'items'):
        for oi in order.items:
            items.append({
                'product_name': oi.product.name if oi.product else 'Unknown',
                'quantity': oi.quantity,
                'price': float(oi.price),
                'subtotal': float(oi.price * oi.quantity),
            })
    
    return jsonify({
        'id': order.id,
        'total_amount': float(order.total_amount),
        'order_status': order.order_status,
        'payment_status': order.payment_status,
        'payment_method': order.payment_method,
        'shipping_address': order.shipping_address or '',
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'items': items,
    })

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
    """View wishlist — returns JSON."""
    items = db.session.query(Wishlist).filter_by(user_id=current_user.id).all()
    return jsonify({
        'items': [
            {
                'id': w.id,
                'product_id': w.product_id,
                'product_name': w.product.name if w.product else 'Unknown',
                'price': float(w.product.selling_price) if w.product else 0,
                'image': w.product.image_path or '' if w.product else '',
                'in_stock': w.product.stock_quantity > 0 if w.product else False,
            }
            for w in items
        ]
    })

@customer_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@customer_required
def add_to_wishlist(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Product not found.'}), 404
        flash('Product not found.', 'danger')
        return redirect(url_for('customer.shop'))
        
    exists = db.session.query(Wishlist).filter_by(user_id=current_user.id, product_id=product_id).first()
    if not exists:
        db.session.add(Wishlist(user_id=current_user.id, product_id=product_id))
        db.session.commit()
        msg = f'{product.name} added to your wishlist.'
        if request.is_json:
            return jsonify({'success': True, 'message': msg})
        flash(msg, 'success')
    else:
        msg = f'{product.name} is already in your wishlist.'
        if request.is_json:
            return jsonify({'success': False, 'message': msg})
        flash(msg, 'info')
    return redirect(request.referrer or url_for('customer.shop'))

@customer_bp.route('/wishlist/remove/<int:id>', methods=['POST'])
@customer_required
def remove_from_wishlist(id):
    item = db.session.get(Wishlist, id)
    if item and item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        if request.is_json:
            return jsonify({'success': True, 'message': 'Item removed from wishlist.'})
        flash('Item removed from wishlist.', 'info')
    else:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Item not found.'}), 404
    return redirect(url_for('customer.view_wishlist'))

@customer_bp.route('/create-checkout-session/<int:order_id>', methods=['POST'])
@customer_required
def create_checkout_session(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(error="Order not found"), 404
        
    stripe_key = current_app.config.get('STRIPE_SECRET_KEY')
    if not stripe_key:
        return jsonify(error="Stripe payments are not configured on this server"), 400
        
    stripe.api_key = stripe_key
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
