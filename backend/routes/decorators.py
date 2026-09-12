from functools import wraps

from flask import flash, jsonify, redirect, request, url_for
from flask_login import current_user


def _is_api_or_json_request():
    """Detect if the incoming request expects a JSON response or is an API call."""
    return bool(
        request.is_json
        or request.path.startswith('/api/')
        or '/api/' in request.path
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('Accept', '')
    )


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if _is_api_or_json_request():
                return jsonify({'success': False, 'message': 'Authentication required.'}), 401
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            if _is_api_or_json_request():
                return jsonify({'success': False, 'message': 'Administrator privileges required.'}), 403
            flash('Admin access required.', 'danger')
            return redirect(url_for('customer.shop'))
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if _is_api_or_json_request():
                return jsonify({'success': False, 'message': 'Authentication required.'}), 401
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.customer_login'))
        if current_user.role != 'customer':
            if _is_api_or_json_request():
                return jsonify({'success': False, 'message': 'Customer access only. Admins cannot perform customer actions.'}), 403
            flash('Customer access only. Admins cannot perform customer actions.', 'warning')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function
