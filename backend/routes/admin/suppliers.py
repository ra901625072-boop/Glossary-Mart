"""Admin supplier management routes (CRUD + AP settlement)."""
from datetime import datetime, timezone
from flask import current_app, jsonify, request

from database.models import db
from database.models.inventory import Supplier
from database.models.expense import Expense
from backend.routes.decorators import admin_required
from .helpers import _log_action
from . import admin_bp


@admin_bp.route('/suppliers')
@admin_required
def suppliers():
    """Supplier management — returns JSON list with Accounts Payable balances."""
    suppliers_list = db.session.query(Supplier).order_by(Supplier.name).all()
    return jsonify({
        'suppliers': [
            {
                'id': s.id,
                'name': s.name,
                'contact_person': s.contact_person or '',
                'phone': s.phone or '',
                'email': s.email or '',
                'address': s.address or '',
                'gstin': s.gstin or '',
                'bank_details': s.bank_details or '',
                'outstanding_balance': float(s.outstanding_balance or 0.0),
            }
            for s in suppliers_list
        ]
    })


@admin_bp.route('/suppliers', methods=['POST'])
@admin_bp.route('/suppliers/add', methods=['GET', 'POST'])
@admin_required
def add_supplier():
    """Add a new supplier — returns JSON."""
    if request.method == 'GET':
        return jsonify({'fields': ['name', 'contact_person', 'phone', 'email', 'address', 'gstin', 'bank_details']})

    data = request.get_json(silent=True) if request.is_json else (request.form.to_dict() if request.form else {})
    if not data:
        data = request.get_json(force=True, silent=True) or {}

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Supplier name is required.'}), 400

    supplier = Supplier(
        name=name,
        contact_person=(data.get('contact_person') or data.get('contact') or '').strip(),
        phone=(data.get('phone') or '').strip(),
        email=(data.get('email') or '').strip(),
        address=(data.get('address') or '').strip(),
        gstin=(data.get('gstin') or '').strip(),
        bank_details=(data.get('bank_details') or '').strip(),
        outstanding_balance=0.0,
    )
    try:
        db.session.add(supplier)
        db.session.commit()

        _log_action(
            action='ADD_SUPPLIER',
            entity_type='Supplier',
            entity_id=supplier.id,
            details=f"Registered new supplier '{supplier.name}' (Phone: {supplier.phone or 'N/A'}, GSTIN: {supplier.gstin or 'N/A'})"
        )

        return jsonify({
            'success': True,
            'message': f'Supplier "{supplier.name}" added successfully!',
            'supplier_id': supplier.id,
            'supplier': supplier.to_dict(),
        }), 201
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to add supplier")
        return jsonify({'success': False, 'message': 'Could not add supplier. Please try again.'}), 500


@admin_bp.route('/suppliers/<int:supplier_id>', methods=['GET', 'PUT', 'PATCH'])
@admin_bp.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
@admin_required
def edit_supplier(supplier_id):
    """Edit an existing supplier — returns JSON."""
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({'error': 'Supplier not found.'}), 404

    if request.method == 'GET':
        return jsonify({
            'success': True,
            'supplier': supplier.to_dict(),
            'id': supplier.id,
            'name': supplier.name,
            'contact_person': supplier.contact_person or '',
            'phone': supplier.phone or '',
            'email': supplier.email or '',
            'address': supplier.address or '',
            'gstin': supplier.gstin or '',
            'bank_details': supplier.bank_details or '',
            'outstanding_balance': float(supplier.outstanding_balance or 0.0),
        })

    data = request.get_json(silent=True) if request.is_json else (request.form.to_dict() if request.form else {})
    if not data:
        data = request.get_json(force=True, silent=True) or {}

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Supplier name is required.'}), 400

    supplier.name = name
    if 'contact_person' in data or 'contact' in data:
        supplier.contact_person = (data.get('contact_person') or data.get('contact') or '').strip()
    if 'phone' in data:
        supplier.phone = (data.get('phone') or '').strip()
    if 'email' in data:
        supplier.email = (data.get('email') or '').strip()
    if 'address' in data:
        supplier.address = (data.get('address') or '').strip()
    if 'gstin' in data:
        supplier.gstin = (data.get('gstin') or '').strip()
    if 'bank_details' in data:
        supplier.bank_details = (data.get('bank_details') or '').strip()

    try:
        db.session.commit()

        _log_action(
            action='EDIT_SUPPLIER',
            entity_type='Supplier',
            entity_id=supplier.id,
            details=f"Updated details for supplier '{supplier.name}'"
        )

        return jsonify({
            'success': True,
            'message': f'Supplier "{supplier.name}" updated successfully!',
            'supplier': supplier.to_dict(),
        })
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to update supplier #{supplier_id}")
        return jsonify({'success': False, 'message': 'Could not update supplier. Please try again.'}), 500


@admin_bp.route('/suppliers/<int:supplier_id>/pay', methods=['POST'])
@admin_required
def pay_supplier(supplier_id):
    """
    Disburse payment to supplier against Accounts Payable balance.
    Reduces supplier.outstanding_balance and records cash/bank outflow in Expense ledger.
    """
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({'success': False, 'message': 'Supplier not found.'}), 404

    data = request.get_json(silent=True) or request.form
    try:
        amount_paid = float(data.get('amount_paid') or data.get('amount') or 0.0)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid payment amount.'}), 400

    if amount_paid <= 0:
        return jsonify({'success': False, 'message': 'Payment amount must be strictly greater than zero.'}), 400

    current_balance = float(supplier.outstanding_balance or 0.0)
    payment_mode = (data.get('payment_mode') or 'Bank Transfer').strip()
    notes = (data.get('notes') or '').strip()

    supplier.outstanding_balance = max(0.0, current_balance - amount_paid)

    # Record cash outflow in operating ledger to maintain accurate cash balance
    expense = Expense(
        category='Supplier Payment (AP)',
        amount=amount_paid,
        payment_mode=payment_mode,
        expense_type='Supplier Payment',
        description=f"AP settlement to vendor '{supplier.name}'. Ref/Notes: {notes or 'N/A'}",
        expense_date=datetime.now(timezone.utc),
    )
    db.session.add(expense)

    _log_action(
        action='SUPPLIER_PAYMENT',
        entity_type='Supplier',
        entity_id=supplier_id,
        details=f"Paid ₹{amount_paid:.2f} ({payment_mode}) to {supplier.name}. New AP balance: ₹{float(supplier.outstanding_balance):.2f}"
    )

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Disbursed ₹{amount_paid:.2f} to {supplier.name} via {payment_mode}.',
            'new_balance': float(supplier.outstanding_balance),
        })
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to record payment for supplier #{supplier_id}")
        return jsonify({'success': False, 'message': 'Could not record supplier payment. Please try again.'}), 500


@admin_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
@admin_bp.route('/suppliers/delete/<int:supplier_id>', methods=['POST', 'DELETE'])
@admin_required
def delete_supplier(supplier_id):
    """Delete a supplier — blocked if linked to past purchases or has outstanding AP."""
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({'error': 'Supplier not found.'}), 404

    if float(supplier.outstanding_balance or 0.0) > 0:
        return jsonify({
            'success': False,
            'message': f'Cannot delete "{supplier.name}" — outstanding Accounts Payable of ₹{float(supplier.outstanding_balance):.2f} must be settled first.'
        }), 400

    if supplier.purchases:
        return jsonify({
            'success': False,
            'message': f'Cannot delete "{supplier.name}" — it is linked to past purchase orders. Deleting would violate accounting and stock audit integrity.'
        }), 409

    name = supplier.name
    try:
        db.session.delete(supplier)
        db.session.commit()

        _log_action(
            action='DELETE_SUPPLIER',
            entity_type='Supplier',
            entity_id=supplier_id,
            details=f"Deleted supplier record for '{name}'"
        )

        return jsonify({'success': True, 'message': f'Supplier "{name}" deleted successfully!'})
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete supplier #{supplier_id}")
        return jsonify({'success': False, 'message': 'Could not delete supplier. Please try again.'}), 500

