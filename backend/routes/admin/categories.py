"""Admin category management routes (CRUD)."""
from flask import current_app, flash, redirect, render_template, url_for

from database.models import db
from database.models.product import Category
from backend.routes.decorators import admin_required
from backend.forms.admin import CategoryForm
from . import admin_bp


@admin_bp.route('/categories')
@admin_required
def categories():
    """Category management page."""
    all_categories = db.session.query(Category).order_by(Category.name).all()
    return render_template('admin/categories.html', categories=all_categories)


@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def add_category():
    """Add a new category."""
    form = CategoryForm()
    if form.validate_on_submit():
        name = form.name.data
        existing = db.session.query(Category).filter_by(name=name).first()
        if existing:
            flash(f'Category "{name}" already exists.', 'warning')
            return redirect(url_for('admin.add_category'))

        category = Category(name=name, description=form.description.data)
        try:
            db.session.add(category)
            db.session.commit()
            flash(f'Category "{name}" added successfully!', 'success')
            return redirect(url_for('admin.categories'))
        except Exception:
            db.session.rollback()
            current_app.logger.exception(f"Failed to add category '{name}'")
            flash('Could not add category. Please try again.', 'danger')

    return render_template('admin/add_category.html', form=form)


@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    """Edit an existing category."""
    category = db.session.get(Category, category_id)
    if not category:
        flash("Category not found.", "danger")
        return redirect(url_for('admin.categories'))

    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        name = form.name.data
        existing = db.session.query(Category).filter(
            Category.name == name, Category.id != category_id
        ).first()
        if existing:
            flash(f'Category "{name}" already exists.', 'warning')
            return redirect(url_for('admin.edit_category', category_id=category_id))

        category.name = name
        category.description = form.description.data

        try:
            db.session.commit()
            flash(f'Category "{name}" updated successfully!', 'success')
            return redirect(url_for('admin.categories'))
        except Exception:
            db.session.rollback()
            current_app.logger.exception(f"Failed to update category #{category_id}")
            flash('Could not update category. Please try again.', 'danger')

    return render_template('admin/edit_category.html', form=form, category=category)


@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def delete_category(category_id):
    """Delete a category — blocked if products are associated."""
    category = db.session.get(Category, category_id)
    if not category:
        flash("Category not found.", "danger")
        return redirect(url_for('admin.categories'))

    if category.products:
        flash(f'Cannot delete "{category.name}" — it is associated with products.', 'danger')
        return redirect(url_for('admin.categories'))

    name = category.name
    try:
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{name}" deleted successfully!', 'success')
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete category #{category_id}")
        flash('Could not delete category. Please try again.', 'danger')

    return redirect(url_for('admin.categories'))
