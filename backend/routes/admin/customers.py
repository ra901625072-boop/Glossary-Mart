"""Admin customer management routes (list customers, clear Udhar credit)."""
from flask import current_app, jsonify, request

from database.models import db
from database.models.user import User
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/customers')
@admin_required
def customers():
    """View all customers and their store-credit (Udhar) balances — returns JSON."""
    customers_list = db.session.query(User).filter_by(role='customer').order_by(User.full_name).all()
    return jsonify({
        'customers': [
            {
                'id': c.id,
                'username': c.username,
                'email': c.email,
                'full_name': c.full_name or '',
                'phone': c.phone or '',
                'address': c.address or '',
                'credit': float(c.credit) if hasattr(c, 'credit') and c.credit else 0.0,
                'is_verified': getattr(c, 'is_verified', True),
            }
            for c in customers_list
        ]
    })


@admin_bp.route('/customers/<int:user_id>/clear_credit', methods=['POST'])
@admin_required
def clear_credit(user_id):
    """Partially or fully settle a customer's Udhar credit balance."""
    customer = db.session.get(User, user_id)
    if not customer:
        return jsonify({'success': False, 'message': 'Customer not found.'}), 404

    if request.is_json:
        amount_paid_str = request.json.get('amount_paid')
    else:
        amount_paid_str = request.form.get('amount_paid')
    
    if not amount_paid_str:
        return jsonify({'success': False, 'message': 'Amount is required.'}), 400

    try:
        amount_paid = float(amount_paid_str)
        if amount_paid <= 0:
            return jsonify({'success': False, 'message': 'Amount must be strictly positive.'}), 400

        current_balance = float(customer.credit)
        if current_balance < amount_paid:
            return jsonify({
                'success': False,
                'message': f'Amount paid ({amount_paid:.2f}) cannot exceed the current balance ({current_balance:.2f}).'
            }), 400

        customer.credit = current_balance - amount_paid
        try:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Cleared ₹{amount_paid:.2f} for {customer.full_name or customer.username}!',
                'new_balance': float(customer.credit),
            })
        except Exception:
            db.session.rollback()
            current_app.logger.exception(f"Failed to clear credit for user #{user_id}")
            return jsonify({'success': False, 'message': 'Could not clear credit. Please try again.'}), 500

    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid amount entered.'}), 400
