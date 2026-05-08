import logging
import secrets

from flask import flash, redirect, render_template, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Message

from extensions import limiter
from models import User, db, Cart, Product
from . import auth_bp
from .forms import LoginForm, RegistrationForm

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
            return redirect(url_for('admin.dashboard'))
        else:
            flash('You are logged in as a customer. Please logout to access admin login.', 'warning')
            return redirect(url_for('customer.shop'))
            
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
                return redirect(url_for('security.verify_2fa'))
            else:
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('admin.dashboard'))
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
            new_user = User(
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
                password_hash=generate_password_hash(form.password.data),
                role='customer',
                full_name=form.full_name.data,
                phone=form.phone.data,
                address=form.address.data,
                verification_token=token,
                is_verified=False
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            # Send verification email
            try:
                from app import mail
                msg = Message("Verify Your Email | Jay Goga Kirana Store", recipients=[new_user.email])
                verify_url = url_for('security.verify_email', token=token, _external=True)
                msg.body = f"Welcome! Click here to verify your email address: {verify_url}"
                mail.send(msg)
            except Exception as e:
                logging.error(f"Error sending verification email: {str(e)}")

            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('auth.customer_login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error during registration: {str(e)}', 'danger')
    
    return render_template('customer/customer_register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def customer_login():
    """Customer login page (Supported for all users now)"""
    if current_user.is_authenticated:
        if current_user.role == 'customer':
            return redirect(url_for('customer.shop'))
        else:
            return redirect(url_for('admin.dashboard'))
            
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
                return redirect(url_for('admin.dashboard'))
            
            merge_session_cart(user)
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            return redirect(url_for('customer.shop'))
        else:
            flash('Invalid email/username or password.', 'danger')
    
    return render_template('customer/customer_login.html', form=form)
