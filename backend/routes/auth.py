import logging
import secrets
import time

from flask import current_app, flash, jsonify, redirect, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Message

from backend.extensions import limiter, mail
from backend.services import EmailService
from database.models import db
from database.models.user import User
from database.models.order import Cart
from database.models.product import Product
from backend.utils.security import hash_token
from . import auth_bp
from .pages import serve_frontend_page

def merge_session_cart(user):
    """Merge guest session cart into user's DB cart"""
    if 'cart' in session and session['cart'] and user.role == 'customer':
        for pid_str, qty in session['cart'].items():
            product_id = int(pid_str)
            product = db.session.get(Product, product_id)
            if product:
                cart_item = db.session.query(Cart).filter_by(user_id=user.id, product_id=product_id).first()
                if cart_item:
                    cart_item.quantity = min(cart_item.quantity + qty, product.stock_quantity)
                else:
                    new_item = Cart(user_id=user.id, product_id=product_id, quantity=min(qty, product.stock_quantity))
                    db.session.add(new_item)
        db.session.commit()
        session.pop('cart', None)

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Admin login — GET serves SPA page, POST returns JSON."""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('admin.admin_erp_console')})
            return redirect(url_for('admin.admin_erp_console'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': 'You are logged in as a customer. Please logout to access admin login.'}), 403
            flash('You are logged in as a customer. Please logout to access admin login.', 'warning')
            return redirect(url_for('customer.customer_portal'))
            
    if request.method == 'GET':
        # Serve the admin SPA page (which has the login UI built-in)
        return serve_frontend_page('admin.html')
    
    # POST — process login
    data = request.get_json() if request.is_json else request.form
    login_id = (data.get('email') or data.get('username') or '').strip()
    password = data.get('password') or ''
    
    if not login_id or not password:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Username/email and password are required.'}), 400
        flash('Username/email and password are required.', 'danger')
        return redirect(url_for('auth.login'))
    
    user = db.session.query(User).filter(
        (User.email == login_id.lower()) | (User.username == login_id)
    ).first()
    
    if user and check_password_hash(user.password_hash, password):
        if user.role != 'admin':
            if request.is_json:
                return jsonify({'success': False, 'message': 'Admin access only. Please use customer login.'}), 403
            flash('Admin access only. Please use customer login.', 'warning')
            return redirect(url_for('auth.customer_login'))
        
        if user.two_factor_enabled:
            session['2fa_user_id'] = user.id
            session['2fa_expires_at'] = time.time() + 300  # 5 minutes timeout
            if request.is_json:
                return jsonify({'success': True, 'requires_2fa': True, 'redirect': url_for('security.verify_2fa')})
            return redirect(url_for('security.verify_2fa'))
        else:
            session.clear()
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'message': 'Login successful!', 'redirect': url_for('admin.admin_erp_console')})
            flash('Login successful!', 'success')
            return redirect(url_for('admin.admin_erp_console'))
    else:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Invalid username/email or password.'}), 401
        flash('Invalid username/email or password.', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    if request.is_json:
        return jsonify({'success': True, 'message': 'You have been logged out.', 'redirect': url_for('auth.customer_login')})
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.customer_login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def customer_register():
    """Customer registration — GET serves SPA page, POST returns JSON."""
    if current_user.is_authenticated:
        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('customer.shop')})
        return redirect(url_for('customer.shop'))

    if request.method == 'GET':
        return serve_frontend_page('customer.html')

    data = request.get_json() if request.is_json else request.form
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    
    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'Username, email, and password are required.'}), 400
    
    existing_user = db.session.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Username or email is already registered.'}), 409
    
    try:
        token = secrets.token_urlsafe(32)
        has_mail = EmailService.is_configured()
        is_verified = not has_mail
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='customer',
            full_name=data.get('full_name', ''),
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            verification_token=hash_token(token),
            is_verified=is_verified
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        if not is_verified:
            email_result = EmailService.send_verification_email(new_user, token)
            if email_result.get('success'):
                message = 'Registration successful! Please check your email to verify your account.'
                return jsonify({'success': True, 'message': message, 'redirect': url_for('auth.customer_login')})
            elif email_result.get('is_sandbox_restriction'):
                current_app.logger.warning(
                    f"Resend Sandbox Mode: recipient {new_user.email} cannot receive sandbox emails. "
                    "Auto-verifying user for test session to prevent account lockout."
                )
                new_user.is_verified = True
                new_user.verification_token = None
                db.session.commit()
                login_user(new_user)
                return jsonify({
                    'success': True,
                    'message': 'Registration successful! Welcome to eGrossary.',
                    'redirect': url_for('customer.customer_portal')
                })
            else:
                current_app.logger.error("Failed to send verification email: %s", email_result.get("message"))
                message = "Account created, but verification email could not be delivered."
                return jsonify({'success': True, 'message': message, 'redirect': url_for('auth.customer_login')})
        else:
            login_user(new_user)
            return jsonify({'success': True, 'message': 'Registration successful! Welcome to e Grossary Store.', 'redirect': url_for('customer.customer_portal')})
        
    except Exception:
        db.session.rollback()
        logging.exception("Customer registration failed")
        return jsonify({'success': False, 'message': 'Registration failed due to a server error. Please try again.'}), 500

@auth_bp.route('/customer/register', methods=['GET', 'POST'])
def customer_register_redirect():
    """Convenience alias redirecting /customer/register to /register"""
    return redirect(url_for('auth.customer_register'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_alias():
    """Convenience alias routing /forgot-password to /security/forgot-password"""
    from .security import forgot_password
    return forgot_password()

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def customer_login():
    """Customer login — GET serves SPA page, POST returns JSON."""
    if current_user.is_authenticated:
        if current_user.role == 'customer':
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('customer.customer_portal')})
            return redirect(url_for('customer.customer_portal'))
        else:
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('admin.admin_erp_console')})
            return redirect(url_for('admin.admin_erp_console'))
            
    if request.method == 'GET':
        return serve_frontend_page('customer.html')
    
    data = request.get_json() if request.is_json else request.form
    login_id = (data.get('email') or data.get('username') or '').strip()
    password = data.get('password') or ''
    
    if not login_id or not password:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Email/username and password are required.'}), 400
        flash('Email/username and password are required.', 'danger')
        return redirect(url_for('auth.customer_login'))
    
    # Check both email (lowercase) and username
    user = db.session.query(User).filter(
        (User.email == login_id.lower()) | (User.username == login_id)
    ).first()
    
    if user and check_password_hash(user.password_hash, password):
        if user.role == 'customer' and not getattr(user, 'is_verified', True):
            if request.is_json:
                return jsonify({'success': False, 'message': 'Please verify your email address before logging in.'}), 403
            flash('Please verify your email address before logging in.', 'warning')
            return redirect(url_for('auth.customer_login'))
            
        if user.two_factor_enabled:
            session['2fa_user_id'] = user.id
            session['2fa_expires_at'] = time.time() + 300
            if request.is_json:
                return jsonify({'success': True, 'requires_2fa': True, 'redirect': url_for('security.verify_2fa')})
            return redirect(url_for('security.verify_2fa'))

        old_cart = session.get('cart')
        session.clear()
        if old_cart:
            session['cart'] = old_cart
        login_user(user)
        
        if user.role == 'admin':
            if request.is_json:
                return jsonify({'success': True, 'message': 'Welcome back, Admin!', 'redirect': url_for('admin.admin_erp_console')})
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin.admin_erp_console'))
        
        merge_session_cart(user)
        if request.is_json:
            return jsonify({'success': True, 'message': f'Welcome back, {user.full_name or user.username}!', 'redirect': url_for('customer.customer_portal')})
        flash(f'Welcome back, {user.full_name or user.username}!', 'success')
        return redirect(url_for('customer.customer_portal'))
    else:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Invalid email/username or password.'}), 401
        flash('Invalid email/username or password.', 'danger')
        return redirect(url_for('auth.customer_login'))

@auth_bp.route('/customer/login', methods=['GET', 'POST'])
def customer_login_redirect():
    """Convenience alias redirecting /customer/login to /login"""
    return redirect(url_for('auth.customer_login'))
