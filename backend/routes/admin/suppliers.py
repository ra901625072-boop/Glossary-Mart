"""Admin supplier management routes (CRUD)."""
from flask import current_app, jsonify, request

from database.models import db
from database.models.inventory import Supplier
from backend.routes.decorators import admin_required
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

    data = request.get_json() if request.is_json else request.form
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Supplier name is required.'}), 400

    supplier = Supplier(
        name=name,
        contact_person=(data.get('contact_person') or '').strip(),
        phone=(data.get('phone') or '').strip(),
        email=(data.get('email') or '').strip(),
        address=(data.get('address') or '').strip(),
    )
    try:
        db.session.add(supplier)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Supplier "{supplier.name}" added successfully!', 'supplier_id': supplier.id})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to add supplier")
        return jsonify({'success': False, 'message': 'Could not add supplier. Please try again.'}), 500


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

    data = request.get_json() if request.is_json else request.form
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Supplier name is required.'}), 400

    supplier.name = name
    if 'contact_person' in data:
        supplier.contact_person = (data.get('contact_person') or '').strip()
    if 'phone' in data:
        supplier.phone = (data.get('phone') or '').strip()
    if 'email' in data:
        supplier.email = (data.get('email') or '').strip()
    if 'address' in data:
        supplier.address = (data.get('address') or '').strip()

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': f'Supplier "{supplier.name}" updated successfully!'})
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to update supplier #{supplier_id}")
        return jsonify({'success': False, 'message': 'Could not update supplier. Please try again.'}), 500


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
