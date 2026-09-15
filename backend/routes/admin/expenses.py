"""Admin operating expenses management routes."""
from datetime import datetime, timezone
from flask import current_app, jsonify, request
from sqlalchemy import func

from backend.models import db
from backend.models.expense import Expense
from backend.routes.decorators import admin_required
from .helpers import _log_action
from . import admin_bp


@admin_bp.route('/expenses')
@admin_required
def get_expenses():
    """List operating expenses with summary analytics and audit-compliant filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category_filter = request.args.get('category', '').strip()
    type_filter = request.args.get('type', '').strip()

    query = db.session.query(Expense).filter(Expense.is_deleted == False).order_by(Expense.expense_date.desc(), Expense.id.desc())
    if category_filter:
        query = query.filter(Expense.category == category_filter)
    if type_filter:
        query = query.filter(Expense.expense_type == type_filter)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Monthly Summary (excluding soft-deleted)
    now = datetime.now(timezone.utc)
    current_month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    # OpEx Monthly Total
    opex_monthly = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.is_deleted == False,
        Expense.expense_type == 'OpEx',
        Expense.expense_date >= current_month_start
    ).scalar() or 0

    # CapEx Monthly Total
    capex_monthly = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.is_deleted == False,
        Expense.expense_type == 'CapEx',
        Expense.expense_date >= current_month_start
    ).scalar() or 0

    monthly_total = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.is_deleted == False,
        Expense.expense_type.in_(['OpEx', 'CapEx']),
        Expense.expense_date >= current_month_start
    ).scalar() or 0

    category_aggregates = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.is_deleted == False,
        Expense.expense_type.in_(['OpEx', 'CapEx']),
        Expense.expense_date >= current_month_start
    ).group_by(Expense.category).all()

    return jsonify({
        'success': True,
        'expenses': [e.to_dict() for e in pagination.items],
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
        },
        'summary': {
            'monthly_total': float(monthly_total),
            'monthly_opex': float(opex_monthly),
            'monthly_capex': float(capex_monthly),
            'categories': [{'category': row[0], 'total': float(row[1])} for row in category_aggregates]
        }
    })


@admin_bp.route('/expenses/add', methods=['POST'])
@admin_required
def add_expense():
    """Record a new operating or capital expense."""
    data = request.get_json(silent=True) or request.form
    category = (data.get('category') or 'Other').strip()
    try:
        amount = float(data.get('amount', 0))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid numerical amount.'}), 400

    if amount <= 0:
        return jsonify({'success': False, 'message': 'Expense amount must be strictly greater than zero.'}), 400

    payment_mode = (data.get('payment_mode') or 'Cash').strip()
    expense_type = (data.get('expense_type') or 'OpEx').strip()
    description = (data.get('description') or '').strip()
    is_recurring = bool(data.get('is_recurring', False))

    exp_date_str = data.get('expense_date')
    if exp_date_str:
        try:
            expense_date = datetime.strptime(exp_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except ValueError:
            expense_date = datetime.now(timezone.utc)
    else:
        expense_date = datetime.now(timezone.utc)

    expense = Expense(
        category=category,
        amount=amount,
        payment_mode=payment_mode,
        expense_type=expense_type,
        description=description,
        is_recurring=is_recurring,
        expense_date=expense_date,
        is_deleted=False
    )

    try:
        db.session.add(expense)
        db.session.commit()
        _log_action(
            action='RECORD_EXPENSE',
            entity_type='Expense',
            entity_id=expense.id,
            details=f"Recorded ₹{amount:.2f} under {category} ({payment_mode} - {expense_type})"
        )
        return jsonify({
            'success': True,
            'message': f'Expense of ₹{amount:.2f} recorded under {category}!',
            'expense': expense.to_dict()
        }), 201
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to record expense")
        return jsonify({'success': False, 'message': 'Could not save expense record.'}), 500


@admin_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
@admin_bp.route('/expenses/delete/<int:expense_id>', methods=['POST', 'DELETE'])
@admin_required
def delete_expense(expense_id):
    """
    Void/Soft-delete an expense entry to preserve immutable audit trail.
    """
    expense = db.session.get(Expense, expense_id)
    if not expense or expense.is_deleted:
        return jsonify({'success': False, 'message': 'Expense not found.'}), 404

    try:
        amt = float(expense.amount)
        cat = expense.category
        expense.is_deleted = True
        db.session.commit()
        _log_action(
            action='VOID_EXPENSE',
            entity_type='Expense',
            entity_id=expense_id,
            details=f"Voided ₹{amt:.2f} expense under {cat} (Audit-preserved soft deletion)"
        )
        return jsonify({'success': True, 'message': 'Expense voided and removed from ledger.'})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to void expense")
        return jsonify({'success': False, 'message': 'Failed to void expense.'}), 500
