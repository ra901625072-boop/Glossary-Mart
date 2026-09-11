from flask import jsonify, request
from flask_login import current_user, login_user, logout_user
from werkzeug.security import generate_password_hash
from database.models import db, User
from . import api_bp


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
def api_login():
    """
    Log in customer or admin via JSON.
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

    login_user(user, remember=remember)

    return jsonify({
        'success': True,
        'message': 'Logged in successfully',
        'user': user.to_dict()
    }), 200


@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    """
    Register customer via JSON.
    Body: { username, email, password, full_name, phone, address }
    """
    data = request.get_json(silent=True) or request.form
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')
    full_name = (data.get('full_name') or '').strip()
    phone = (data.get('phone') or '').strip()
    address = (data.get('address') or '').strip()

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'Username, email and password are required'}), 400

    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400

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

    login_user(new_user, remember=True)

    return jsonify({
        'success': True,
        'message': 'Registration successful',
        'user': new_user.to_dict()
    }), 201


@api_bp.route('/auth/logout', methods=['POST'])
def api_logout():
    """Log out current user"""
    if current_user.is_authenticated:
        logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


@api_bp.route('/auth/profile', methods=['PUT', 'POST'])
def api_update_profile():
    """Update current user profile (full_name, phone, address)"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    data = request.get_json(silent=True) or request.form
    full_name = data.get('full_name')
    phone = data.get('phone')
    address = data.get('address')

    if full_name is not None:
        current_user.full_name = full_name.strip()
    if phone is not None:
        current_user.phone = phone.strip()
    if address is not None:
        current_user.address = address.strip()

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully',
        'user': current_user.to_dict()
    }), 200
