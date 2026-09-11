from flask import jsonify, request
from flask_login import current_user
from database.models import db
from database.models.product import Category, Product, Review
from . import api_bp


@api_bp.route('/products', methods=['GET'])
def get_products():
    """
    Get paginated/filtered list of active products.
    Query params:
      - search: string
      - category: category name or id
      - min_price: float
      - max_price: float
      - in_stock: 1 or 0
      - sort: price_low, price_high, latest, name (default)
      - page: int (default 1)
      - per_page: int (default 24)
    """
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    sort_by = request.args.get('sort', 'name')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    in_stock = request.args.get('in_stock')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 24, type=int)

    query = db.session.query(Product).filter_by(is_active=True)

    if search:
        safe_search = search.replace('%', '\\%').replace('_', '\\_')
        query = query.filter(Product.name.ilike(f'%{safe_search}%'))

    if category:
        if category.isdigit():
            query = query.filter(Product.category_id == int(category))
        else:
            query = query.join(Product.category_rel).filter(Category.name == category)

    if min_price is not None:
        query = query.filter(Product.selling_price >= min_price)

    if max_price is not None:
        query = query.filter(Product.selling_price <= max_price)

    if in_stock == '1':
        query = query.filter(Product.stock_quantity > 0)

    if sort_by == 'price_low':
        query = query.order_by(Product.selling_price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.selling_price.desc())
    elif sort_by == 'latest':
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.name.asc())

    total = query.count()
    products = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'success': True,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page if per_page else 1,
        'products': [p.to_dict() for p in products]
    }), 200


@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product details with reviews"""
    product = db.session.query(Product).filter_by(id=product_id, is_active=True).first()
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    data = product.to_dict()
    reviews = db.session.query(Review).filter_by(product_id=product.id).order_by(Review.created_at.desc()).all()
    data['reviews'] = [{
        'id': r.id,
        'rating': r.rating,
        'comment': r.comment,
        'user_name': r.user.full_name or r.user.username if r.user else 'Anonymous',
        'created_at': r.created_at.strftime('%Y-%m-%d')
    } for r in reviews]

    return jsonify({'success': True, 'product': data}), 200


@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories with active product counts"""
    categories = db.session.query(Category).order_by(Category.name).all()
    results = []
    for cat in categories:
        count = db.session.query(Product).filter_by(category_id=cat.id, is_active=True).count()
        results.append({
            'id': cat.id,
            'name': cat.name,
            'description': cat.description,
            'product_count': count
        })
    return jsonify({'success': True, 'categories': results}), 200


@api_bp.route('/products/<int:product_id>/reviews', methods=['POST'])
def add_product_review(product_id):
    """Add a review for a product. Requires authentication."""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required to submit review'}), 401

    product = db.session.query(Product).filter_by(id=product_id, is_active=True).first()
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    data = request.get_json(silent=True) or request.form
    rating = data.get('rating')
    comment = (data.get('comment') or '').strip()

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Rating must be an integer between 1 and 5'}), 400

    review = Review(
        product_id=product.id,
        user_id=current_user.id,
        rating=rating,
        comment=comment
    )
    db.session.add(review)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Review submitted successfully',
        'review': {
            'id': review.id,
            'rating': review.rating,
            'comment': review.comment,
            'user_name': current_user.full_name or current_user.username,
            'created_at': review.created_at.strftime('%Y-%m-%d')
        }
    }), 201
