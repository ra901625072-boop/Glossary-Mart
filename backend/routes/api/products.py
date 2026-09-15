from flask import jsonify, request
from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload
from backend.models import db
from backend.models.product import Category, Product, Review
from backend.models.order import Order, OrderItem
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
    # Eager load category_rel and reviews to eliminate N+1 roundtrips
    products = (
        query.options(
            joinedload(Product.category_rel),
            selectinload(Product.reviews)
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    is_admin = current_user.is_authenticated and current_user.role == 'admin'

    return jsonify({
        'success': True,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page if per_page else 1,
        'products': [p.to_dict(is_admin=is_admin) for p in products]
    }), 200


@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product details with reviews (wholesale data redacted for non-admins)"""
    product = (
        db.session.query(Product)
        .options(joinedload(Product.category_rel), selectinload(Product.reviews))
        .filter_by(id=product_id, is_active=True)
        .first()
    )
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    is_admin = current_user.is_authenticated and current_user.role == 'admin'
    data = product.to_dict(is_admin=is_admin)
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
    """Get all categories with active product counts in a single batch query"""
    categories = db.session.query(Category).order_by(Category.name).all()
    counts_map = dict(
        db.session.query(Product.category_id, func.count(Product.id))
        .filter(Product.is_active == True)
        .group_by(Product.category_id)
        .all()
    )
    results = [
        {
            'id': cat.id,
            'name': cat.name,
            'description': cat.description,
            'product_count': counts_map.get(cat.id, 0)
        }
        for cat in categories
    ]
    return jsonify({'success': True, 'categories': results}), 200


@api_bp.route('/products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    """Get all reviews for a product with rating breakdown, summary metrics, and verified status."""
    product = db.session.query(Product).filter_by(id=product_id, is_active=True).first()
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    reviews = (
        db.session.query(Review)
        .options(joinedload(Review.user))
        .filter_by(product_id=product.id)
        .order_by(Review.created_at.desc())
        .all()
    )

    # Find verified buyers (users who have ordered this product)
    verified_user_ids = set()
    purchased_records = (
        db.session.query(Order.user_id)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(OrderItem.product_id == product.id)
        .distinct()
        .all()
    )
    verified_user_ids = {r[0] for r in purchased_records}

    total_reviews = len(reviews)
    breakdown = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in reviews:
        if r.rating in breakdown:
            breakdown[r.rating] += 1

    avg_rating = round(sum(r.rating for r in reviews) / total_reviews, 1) if total_reviews else 0.0
    recommended_count = breakdown.get(4, 0) + breakdown.get(5, 0)
    recommend_percent = round((recommended_count / total_reviews) * 100) if total_reviews else 100

    current_user_id = current_user.id if current_user.is_authenticated else None
    user_review_data = None
    reviews_list = []

    for r in reviews:
        is_owner = bool(current_user_id and r.user_id == current_user_id)
        is_verified = r.user_id in verified_user_ids
        review_item = {
            'id': r.id,
            'product_id': r.product_id,
            'user_id': r.user_id,
            'user_name': (r.user.full_name or r.user.username) if r.user else 'Verified Customer',
            'rating': r.rating,
            'comment': r.comment or '',
            'created_at': r.created_at.strftime('%Y-%m-%d') if r.created_at else '',
            'is_verified_buyer': is_verified,
            'is_current_user': is_owner
        }
        reviews_list.append(review_item)
        if is_owner and not user_review_data:
            user_review_data = review_item

    return jsonify({
        'success': True,
        'summary': {
            'average_rating': avg_rating,
            'total_reviews': total_reviews,
            'recommend_percent': recommend_percent,
            'rating_breakdown': breakdown,
        },
        'user_review': user_review_data,
        'reviews': reviews_list
    }), 200


@api_bp.route('/products/<int:product_id>/reviews', methods=['POST'])
def add_product_review(product_id):
    """Add or update a review for a product. Requires authentication."""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required to submit review'}), 401

    product = db.session.query(Product).filter_by(id=product_id, is_active=True).first()
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    data = request.get_json(silent=True) or request.form
    rating = data.get('rating')
    comment = (data.get('comment') or '').strip()[:1000]

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Rating must be an integer between 1 and 5'}), 400

    # Upsert: check if user already wrote a review for this product
    existing_review = db.session.query(Review).filter_by(product_id=product.id, user_id=current_user.id).first()
    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
        review = existing_review
        msg = 'Your review has been updated successfully'
    else:
        review = Review(
            product_id=product.id,
            user_id=current_user.id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        msg = 'Review submitted successfully'

    db.session.commit()

    is_verified = db.session.query(OrderItem.id).join(Order, Order.id == OrderItem.order_id).filter(
        Order.user_id == current_user.id,
        OrderItem.product_id == product.id
    ).first() is not None

    return jsonify({
        'success': True,
        'message': msg,
        'review': {
            'id': review.id,
            'product_id': product.id,
            'rating': review.rating,
            'comment': review.comment,
            'user_name': current_user.full_name or current_user.username,
            'created_at': review.created_at.strftime('%Y-%m-%d') if review.created_at else '',
            'is_verified_buyer': is_verified,
            'is_current_user': True
        }
    }), 201


@api_bp.route('/reviews/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    """Update an existing review. Customer must be the review owner."""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    review = db.session.query(Review).filter_by(id=review_id).first()
    if not review:
        return jsonify({'success': False, 'message': 'Review not found'}), 404

    if review.user_id != current_user.id and getattr(current_user, 'role', '') != 'admin':
        return jsonify({'success': False, 'message': 'Permission denied. You can only edit your own reviews.'}), 403

    data = request.get_json(silent=True) or request.form
    if 'rating' in data:
        try:
            rating = int(data.get('rating'))
            if rating < 1 or rating > 5:
                raise ValueError()
            review.rating = rating
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Rating must be an integer between 1 and 5'}), 400

    if 'comment' in data:
        review.comment = (data.get('comment') or '').strip()[:1000]

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Review updated successfully',
        'review': {
            'id': review.id,
            'product_id': review.product_id,
            'rating': review.rating,
            'comment': review.comment,
            'user_name': current_user.full_name or current_user.username,
            'created_at': review.created_at.strftime('%Y-%m-%d') if review.created_at else '',
            'is_current_user': True
        }
    }), 200


@api_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """Delete a review. Customer must be the review owner or admin."""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    review = db.session.query(Review).filter_by(id=review_id).first()
    if not review:
        return jsonify({'success': False, 'message': 'Review not found'}), 404

    if review.user_id != current_user.id and getattr(current_user, 'role', '') != 'admin':
        return jsonify({'success': False, 'message': 'Permission denied. You can only delete your own reviews.'}), 403

    product_id = review.product_id
    db.session.delete(review)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Review deleted successfully',
        'product_id': product_id
    }), 200


@api_bp.route('/customer/my-reviews', methods=['GET'])
def get_my_reviews():
    """Get all reviews written by the currently logged-in customer."""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    reviews = (
        db.session.query(Review)
        .options(joinedload(Review.product))
        .filter_by(user_id=current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )

    results = []
    for r in reviews:
        results.append({
            'id': r.id,
            'product_id': r.product_id,
            'product_name': r.product.name if r.product else 'Unknown Product',
            'product_image': r.product.image_path if r.product else '',
            'product_price': float(r.product.selling_price) if (r.product and r.product.selling_price) else 0.0,
            'rating': r.rating,
            'comment': r.comment or '',
            'created_at': r.created_at.strftime('%Y-%m-%d') if r.created_at else ''
        })

    return jsonify({
        'success': True,
        'reviews': results
    }), 200

