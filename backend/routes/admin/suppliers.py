"""Admin supplier management routes (CRUD)."""
from flask import current_app, flash, redirect, render_template, url_for

from database.models import db
from database.models.inventory import Supplier
from backend.routes.decorators import admin_required
from backend.forms.admin import SupplierForm
from . import admin_bp


@admin_bp.route('/suppliers')
@admin_required
def suppliers():
    """Supplier management page."""
    suppliers_list = db.session.query(Supplier).order_by(Supplier.name).all()
    return render_template('admin/suppliers.html', suppliers=suppliers_list)


@admin_bp.route('/suppliers/add', methods=['GET', 'POST'])
@admin_required
def add_supplier():
    """Add a new supplier."""
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
            flash(f'Supplier "{supplier.name}" added successfully!', 'success')
            return redirect(url_for('admin.suppliers'))
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to add supplier")
            flash('Could not add supplier. Please try again.', 'danger')

    return render_template('admin/add_supplier.html', form=form)


@admin_bp.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
@admin_required
def edit_supplier(supplier_id):
    """Edit an existing supplier."""
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        flash("Supplier not found.", "danger")
        return redirect(url_for('admin.suppliers'))

    form = SupplierForm(obj=supplier)

    if form.validate_on_submit():
        supplier.name = form.name.data
        supplier.contact_person = form.contact_person.data
        supplier.phone = form.phone.data
        supplier.email = form.email.data
        supplier.address = form.address.data

        try:
            db.session.commit()
            flash(f'Supplier "{supplier.name}" updated successfully!', 'success')
            return redirect(url_for('admin.suppliers'))
        except Exception:
            db.session.rollback()
            current_app.logger.exception(f"Failed to update supplier #{supplier_id}")
            flash('Could not update supplier. Please try again.', 'danger')

    return render_template('admin/edit_supplier.html', form=form, supplier=supplier)


@admin_bp.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
@admin_required
def delete_supplier(supplier_id):
    """Delete a supplier — blocked if linked to past purchases."""
    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        flash("Supplier not found.", "danger")
        return redirect(url_for('admin.suppliers'))

    if supplier.purchases:
        flash(f'Cannot delete "{supplier.name}" — it is linked to past purchases.', 'danger')
        return redirect(url_for('admin.suppliers'))

    name = supplier.name
    try:
        db.session.delete(supplier)
        db.session.commit()
        flash(f'Supplier "{name}" deleted successfully!', 'success')
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete supplier #{supplier_id}")
        flash('Could not delete supplier. Please try again.', 'danger')

    return redirect(url_for('admin.suppliers'))
