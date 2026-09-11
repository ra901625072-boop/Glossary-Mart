"""Admin customer management routes (list customers, clear Udhar credit)."""
from flask import current_app, flash, redirect, render_template, request, url_for

from database.models import db
from database.models.user import User
from backend.routes.decorators import admin_required
from . import admin_bp


@admin_bp.route('/customers')
@admin_required
def customers():
    """View all customers and their store-credit (Udhar) balances."""
    customers_list = db.session.query(User).filter_by(role='customer').order_by(User.full_name).all()
    return render_template('admin/customers.html', customers=customers_list)


@admin_bp.route('/customers/<int:user_id>/clear_credit', methods=['POST'])
@admin_required
def clear_credit(user_id):
    """Partially or fully settle a customer's Udhar credit balance."""
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

        current_balance = float(customer.credit)
        if current_balance < amount_paid:
            flash(
                f'Amount paid ({amount_paid:.2f}) cannot exceed the current balance ({current_balance:.2f}).',
                'danger',
            )
            return redirect(url_for('admin.customers'))

        customer.credit = current_balance - amount_paid
        try:
            db.session.commit()
            flash(
                f'Cleared ₹{amount_paid:.2f} for {customer.full_name or customer.username}!',
                'success',
            )
        except Exception:
            db.session.rollback()
            current_app.logger.exception(f"Failed to clear credit for user #{user_id}")
            flash('Could not clear credit. Please try again.', 'danger')

    except (ValueError, TypeError):
        flash('Invalid amount entered.', 'danger')

    return redirect(url_for('admin.customers'))
