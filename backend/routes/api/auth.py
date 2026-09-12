import re
import time
import pyotp
from flask import current_app, jsonify, request, session
from flask_login import current_user, login_user, logout_user
from werkzeug.security import generate_password_hash

from backend.extensions import limiter
from database.models import db, User
from . import api_bp

COMMON_WEAK_PASSWORDS = {
    'password', 'password123', '12345678', '123456789', 'admin123', 'qwertyuiop', 'letmein1'
}

USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_.-]{3,50}$')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


@api_bp.route('/auth/me', methods=['GET'])
def get_current_user():
    """Get profile of currently logged-in user"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        }), 200
    return jsonify({
        'authenticated': False,
        'user': None
    }), 200


@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def api_login():
    """
    Log in customer or admin via JSON with brute-force protection and 2FA enforcement.
    Body: { username: string, password: string, remember: bool }
    """
    data = request.get_json(silent=True) or request.form
    username_or_email = (data.get('email_or_username') or data.get('username') or data.get('email') or '').strip()
    password = data.get('password', '')
    remember = bool(data.get('remember', True))

    if not username_or_email or not password:
        return jsonify({'success': False, 'message': 'Username/email and password required'}), 400

    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email.lower())
    ).first()

    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    if user.role == 'customer' and not getattr(user, 'is_verified', True):
        return jsonify({'success': False, 'message': 'Please verify your email before logging in.'}), 403

    # Enforce Two-Factor Authentication for any user with 2FA enabled
    if user.two_factor_enabled:
        session['2fa_user_id'] = user.id
        session['2fa_expires_at'] = time.time() + 300  # 5 minutes staging
        return jsonify({
            'success': True,
            'requires_2fa': True,
            'message': 'Two-factor authentication code required',
            'user_id': user.id
        }), 200

    # Session fixation defense
    old_cart = session.get('cart')
    session.clear()
    if old_cart:
        session['cart'] = old_cart

    login_user(user, remember=remember)

    return jsonify({
        'success': True,
        'message': 'Logged in successfully',
        'user': user.to_dict()
    }), 200


@api_bp.route('/auth/verify-2fa', methods=['POST'])
@limiter.limit("5 per minute")
def api_verify_2fa():
    """Verify 2FA TOTP code for staged login session via JSON API."""
    if '2fa_user_id' not in session or '2fa_expires_at' not in session:
        return jsonify({'success': False, 'message': 'No active 2FA login session found. Please log in first.'}), 400

    if time.time() > session['2fa_expires_at']:
        session.pop('2fa_user_id', None)
        session.pop('2fa_expires_at', None)
        return jsonify({'success': False, 'message': '2FA session expired. Please log in again.'}), 400

    user = db.session.get(User, session['2fa_user_id'])
    if not user or not user.two_factor_secret:
        return jsonify({'success': False, 'message': 'Invalid 2FA user state.'}), 400

    data = request.get_json(silent=True) or request.form
    token = str(data.get('token') or data.get('code') or '').strip()

    if not token or len(token) != 6 or not token.isdigit():
        return jsonify({'success': False, 'message': 'A valid 6-digit TOTP code is required.'}), 400

    totp = pyotp.TOTP(user.two_factor_secret)
    if not totp.verify(token, valid_window=1):
        return jsonify({'success': False, 'message': 'Invalid 2FA authentication code.'}), 400

    session.pop('2fa_user_id', None)
    session.pop('2fa_expires_at', None)

    # Session fixation defense
    old_cart = session.get('cart')
    session.clear()
    if old_cart:
        session['cart'] = old_cart

    login_user(user, remember=True)

    return jsonify({
        'success': True,
        'message': 'Two-factor authentication verified successfully!',
        'user': user.to_dict()
    }), 200


@api_bp.route('/auth/register', methods=['POST'])
@limiter.limit("3 per minute")
def api_register():
    """
    Register customer via JSON with strict input validation.
    Body: { username, email, password, full_name, phone, address }
    """
    data = request.get_json(silent=True) or request.form
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')
    full_name = (data.get('full_name') or '').strip()[:100]
    phone = (data.get('phone') or '').strip()[:20]
    address = (data.get('address') or '').strip()[:500]

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'Username, email and password are required'}), 400

    if not USERNAME_REGEX.match(username):
        return jsonify({
            'success': False,
            'message': 'Username must be 3-50 characters long and contain only letters, numbers, hyphens, dots, or underscores.'
        }), 400

    if not EMAIL_REGEX.match(email) or len(email) > 120:
        return jsonify({'success': False, 'message': 'Invalid email address format.'}), 400

    min_length = current_app.config.get('MIN_PASSWORD_LENGTH', 8)
    if len(password) < min_length:
        return jsonify({'success': False, 'message': f'Password must be at least {min_length} characters'}), 400

    if password.lower() in COMMON_WEAK_PASSWORDS or password == username:
        return jsonify({'success': False, 'message': 'Password is too common or easily guessed.'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username is already taken'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email is already registered'}), 409

    new_user = User(
        username=username,
        email=email,
        full_name=full_name or username,
        phone=phone,
        address=address,
        role='customer',
        password_hash=generate_password_hash(password),
        is_verified=True  # Can require verification if mail is configured
    )

    db.session.add(new_user)
    db.session.commit()

    # Session fixation defense
    old_cart = session.get('cart')
    session.clear()
    if old_cart:
        session['cart'] = old_cart

    login_user(new_user, remember=True)

    return jsonify({
        'success': True,
        'message': 'Registration successful',
        'user': new_user.to_dict()
    }), 201


@api_bp.route('/auth/logout', methods=['GET', 'POST'])
def api_logout():
    """Log out current user and clear session"""
    if current_user.is_authenticated:
        logout_user()
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


@api_bp.route('/auth/profile', methods=['GET', 'PUT', 'POST'])
@limiter.limit("20 per minute")
def api_update_profile():
    """Get or update current user profile with length and character constraints"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    if request.method == 'GET':
        return jsonify({
            'success': True,
            'user': current_user.to_dict()
        }), 200

    data = request.get_json(silent=True) or request.form
    full_name = data.get('full_name')
    phone = data.get('phone')
    address = data.get('address')

    if full_name is not None:
        clean_name = full_name.strip()[:100]
        if clean_name:
            current_user.full_name = clean_name

    if phone is not None:
        clean_phone = phone.strip()[:20]
        current_user.phone = clean_phone

    if address is not None:
        clean_address = address.strip()[:500]
        current_user.address = clean_address

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully',
        'user': current_user.to_dict()
    }), 200
