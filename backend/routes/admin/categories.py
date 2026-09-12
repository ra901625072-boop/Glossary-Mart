"""Admin category management routes (CRUD)."""
from flask import current_app, jsonify, redirect, request, url_for

from database.models import db
from database.models.product import Category
from backend.routes.decorators import admin_required
from backend.forms.admin import CategoryForm
from . import admin_bp


@admin_bp.route('/categories')
@admin_required
def categories():
    """Category management — returns JSON list."""
    all_categories = db.session.query(Category).order_by(Category.name).all()
    return jsonify({
        'categories': [
            {
                'id': c.id,
                'name': c.name,
                'description': c.description or '',
                'product_count': len(c.products) if hasattr(c, 'products') else 0,
            }
            for c in all_categories
        ]
    })


@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def add_category():
    """Add a new category — returns JSON."""
    if request.method == 'GET':
        return jsonify({'fields': ['name', 'description']})

    form = CategoryForm()
    if form.validate_on_submit():
        name = form.name.data
        existing = db.session.query(Category).filter_by(name=name).first()
        if existing:
            return jsonify({'success': False, 'message': f'Category "{name}" already exists.'}), 409

        category = Category(name=name, description=form.description.data)
        try:
            db.session.add(category)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Category "{name}" added successfully!', 'category_id': category.id})
        except Exception:
            db.session.rollback()
            current_app.logger.exception(f"Failed to add category '{name}'")
            return jsonify({'success': False, 'message': 'Could not add category. Please try again.'}), 500

    errors = {field: errs for field, errs in form.errors.items()} if form.errors else {}
    return jsonify({'success': False, 'errors': errors}), 400


@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    """Edit an existing category — returns JSON."""
    category = db.session.get(Category, category_id)
    if not category:
        return jsonify({'error': 'Category not found.'}), 404

    if request.method == 'GET':
        return jsonify({
            'id': category.id,
            'name': category.name,
            'description': category.description or '',
        })

    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        name = form.name.data
        existing = db.session.query(Category).filter(
            Category.name == name, Category.id != category_id
        ).first()
        if existing:
            return jsonify({'success': False, 'message': f'Category "{name}" already exists.'}), 409

        category.name = name
        category.description = form.description.data

        try:
            db.session.commit()
            return jsonify({'success': True, 'message': f'Category "{name}" updated successfully!'})
        except Exception:
            db.session.rollback()
            current_app.logger.exception(f"Failed to update category #{category_id}")
            return jsonify({'success': False, 'message': 'Could not update category. Please try again.'}), 500

    errors = {field: errs for field, errs in form.errors.items()} if form.errors else {}
    return jsonify({'success': False, 'errors': errors}), 400


@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def delete_category(category_id):
    """Delete a category — blocked if products are associated."""
    category = db.session.get(Category, category_id)
    if not category:
        return jsonify({'error': 'Category not found.'}), 404

    if category.products:
        return jsonify({'success': False, 'message': f'Cannot delete "{category.name}" — it is associated with products.'}), 409

    name = category.name
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Category "{name}" deleted successfully!'})
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete category #{category_id}")
        return jsonify({'success': False, 'message': 'Could not delete category. Please try again.'}), 500
