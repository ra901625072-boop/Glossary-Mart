"""Admin supplier management routes (CRUD)."""
from flask import current_app, jsonify, redirect, request, url_for

from database.models import db
from database.models.inventory import Supplier
from backend.routes.decorators import admin_required
from backend.forms.admin import SupplierForm
from . import admin_bp


@admin_bp.route('/suppliers')
@admin_required
def suppliers():
    """Supplier management — returns JSON list."""
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
            }
            for s in suppliers_list
        ]
    })


@admin_bp.route('/suppliers/add', methods=['GET', 'POST'])
@admin_required
def add_supplier():
    """Add a new supplier — returns JSON."""
    if request.method == 'GET':
        return jsonify({'fields': ['name', 'contact_person', 'phone', 'email', 'address']})

    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
        )
        try:
            db.session.add(supplier)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Supplier "{supplier.name}" added successfully!', 'supplier_id': supplier.id})
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to add supplier")
            return jsonify({'success': False, 'message': 'Could not add supplier. Please try again.'}), 500

    errors = {field: errs for field, errs in form.errors.items()} if form.errors else {}
    return jsonify({'success': False, 'errors': errors}), 400


@admin_bp.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
@admin_required
def edit_supplier(supplier_id):
    """Edit an existing supplier — returns JSON."""
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({'error': 'Supplier not found.'}), 404

    if request.method == 'GET':
        return jsonify({
            'id': supplier.id,
            'name': supplier.name,
            'contact_person': supplier.contact_person or '',
            'phone': supplier.phone or '',
            'email': supplier.email or '',
            'address': supplier.address or '',
        })

    form = SupplierForm(obj=supplier)

    if form.validate_on_submit():
        supplier.name = form.name.data
        supplier.contact_person = form.contact_person.data
        supplier.phone = form.phone.data
        supplier.email = form.email.data
        supplier.address = form.address.data

        try:
            db.session.commit()
            return jsonify({'success': True, 'message': f'Supplier "{supplier.name}" updated successfully!'})
        except Exception:
            db.session.rollback()
            current_app.logger.exception(f"Failed to update supplier #{supplier_id}")
            return jsonify({'success': False, 'message': 'Could not update supplier. Please try again.'}), 500

    errors = {field: errs for field, errs in form.errors.items()} if form.errors else {}
    return jsonify({'success': False, 'errors': errors}), 400


@admin_bp.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
@admin_required
def delete_supplier(supplier_id):
    """Delete a supplier — blocked if linked to past purchases."""
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({'error': 'Supplier not found.'}), 404

    if supplier.purchases:
        return jsonify({'success': False, 'message': f'Cannot delete "{supplier.name}" — it is linked to past purchases.'}), 409

    name = supplier.name
    try:
        db.session.delete(supplier)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Supplier "{name}" deleted successfully!'})
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete supplier #{supplier_id}")
        return jsonify({'success': False, 'message': 'Could not delete supplier. Please try again.'}), 500
