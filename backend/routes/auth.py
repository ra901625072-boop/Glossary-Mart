import logging
import secrets
import time

from flask import current_app, flash, redirect, render_template, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Message

from backend.extensions import limiter, mail
from database.models import db
from database.models.user import User
from database.models.order import Cart
from database.models.product import Product
from backend.forms.auth import LoginForm, RegistrationForm
from backend.utils.security import hash_token
from . import auth_bp

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
    """Admin login page"""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.admin_erp_console'))
        else:
            flash('You are logged in as a customer. Please logout to access admin login.', 'warning')
            return redirect(url_for('customer.customer_portal'))
            
    form = LoginForm()
    if form.validate_on_submit():
        login_id = form.email.data.strip()
        password = form.password.data
        
        user = db.session.query(User).filter(
            (User.email == login_id.lower()) | (User.username == login_id)
        ).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.role != 'admin':
                flash('Admin access only. Please use customer login.', 'warning')
                return redirect(url_for('auth.customer_login'))
            
            if user.two_factor_enabled:
                session['2fa_user_id'] = user.id
                session['2fa_expires_at'] = time.time() + 300  # 5 minutes timeout
                return redirect(url_for('security.verify_2fa'))
            else:
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('admin.admin_erp_console'))
        else:
            flash('Invalid username/email or password.', 'danger')
    
    return render_template('admin/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.customer_login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def customer_register():
    """Customer registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('customer.shop'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            token = secrets.token_urlsafe(32)
            is_verified = not current_app.config.get('MAIL_USERNAME')
            new_user = User(
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
                password_hash=generate_password_hash(form.password.data),
                role='customer',
                full_name=form.full_name.data,
                phone=form.phone.data,
                address=form.address.data,
                verification_token=hash_token(token),
                is_verified=is_verified
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            if not is_verified:
                # Send verification email
                try:
                    msg = Message("Verify Your Email | Jay Goga Mart Store", recipients=[new_user.email])
                    verify_url = url_for('security.verify_email', token=token, _external=True)
                    msg.body = f"Welcome! Click here to verify your email address: {verify_url}"
                    mail.send(msg)
                    flash('Registration successful! Please check your email to verify your account.', 'success')
                except Exception:
                    current_app.logger.exception("Failed to send verification email")
                    flash('Account created, but we couldn\'t send a verification email.', 'warning')
                return redirect(url_for('auth.customer_login'))
            else:
                flash('Registration successful! Welcome to Jay Goga Mart Store.', 'success')
                login_user(new_user)
                return redirect(url_for('customer.customer_portal'))
            
        except Exception:
            db.session.rollback()
            logging.exception("Customer registration failed")
            flash('Registration failed due to a server error. Please try again.', 'danger')
    
    return render_template('customer/customer_register.html', form=form)

@auth_bp.route('/customer/register', methods=['GET', 'POST'])
def customer_register_redirect():
    """Convenience alias redirecting /customer/register to /register"""
    return redirect(url_for('auth.customer_register'))

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def customer_login():
    """Customer login page (Supported for all users now)"""
    if current_user.is_authenticated:
        if current_user.role == 'customer':
            return redirect(url_for('customer.customer_portal'))
        else:
            return redirect(url_for('admin.admin_erp_console'))
            
    form = LoginForm()
    if form.validate_on_submit():
        login_id = form.email.data.strip()
        password = form.password.data
        
        # Check both email (lowercase) and username
        user = db.session.query(User).filter(
            (User.email == login_id.lower()) | (User.username == login_id)
        ).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.role == 'customer' and not getattr(user, 'is_verified', True):
                flash('Please verify your email address before logging in.', 'warning')
                return redirect(url_for('auth.customer_login'))
            login_user(user)
            
            if user.role == 'admin':
                flash(f'Welcome back, Admin!', 'success')
                return redirect(url_for('admin.admin_erp_console'))
            
            merge_session_cart(user)
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            return redirect(url_for('customer.customer_portal'))
        else:
            flash('Invalid email/username or password.', 'danger')
    
    return render_template('customer/customer_login.html', form=form)

@auth_bp.route('/customer/login', methods=['GET', 'POST'])
def customer_login_redirect():
    """Convenience alias redirecting /customer/login to /login"""
    return redirect(url_for('auth.customer_login'))
