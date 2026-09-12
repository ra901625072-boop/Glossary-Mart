import pytest
from database.models import db
from database.models.product import Category, Product


def test_api_health(client):
    """Test API health endpoint returns healthy status"""
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] in ('healthy', 'online')
    assert data['service'] in ('e-grossary-api', 'jay-goga-mart-api')


def test_api_categories(client, app):
    """Test API categories listing"""
    with app.app_context():
        cat = Category.query.filter_by(name='Test Category').first()
        if not cat:
            cat = Category(name='Test Category', description='Test')
            db.session.add(cat)
            db.session.commit()

    res = client.get('/api/categories')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert any(c['name'] == 'Test Category' for c in data['categories'])


def test_api_products(client, session):
    """Test API products listing and filtering"""
    cat = Category(name='Produce', description='Fresh Produce')
    session.add(cat)
    session.flush()

    prod = Product(
        name='API Test Item',
        category_id=cat.id,
        cost_price=50.0,
        selling_price=80.0,
        stock_quantity=15,
        is_active=True
    )
    session.add(prod)
    session.commit()

    res = client.get('/api/products?search=API Test')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['products']) >= 1
    assert data['products'][0]['name'] == 'API Test Item'


def test_api_cart_operations(client, session):
    """Test guest cart add, get, update, and clear operations"""
    cat = Category(name='Cart Produce', description='Cart items')
    session.add(cat)
    session.flush()

    prod = Product(
        name='Cart Test Item',
        category_id=cat.id,
        cost_price=40.0,
        selling_price=80.0,
        stock_quantity=10,
        is_active=True
    )
    session.add(prod)
    session.commit()
    prod_id = prod.id


    # Add item
    add_res = client.post('/api/cart/add', json={'product_id': prod_id, 'quantity': 2})
    assert add_res.status_code == 200
    assert add_res.get_json()['success'] is True

    # View cart
    cart_res = client.get('/api/cart')
    assert cart_res.status_code == 200
    cart_data = cart_res.get_json()
    assert cart_data['success'] is True
    assert cart_data['item_count'] == 2
    assert cart_data['total'] == 160.0

    # Clear cart
    clear_res = client.post('/api/cart/clear')
    assert clear_res.status_code == 200

    # Verify empty
    cart_empty = client.get('/api/cart')
    assert cart_empty.get_json()['item_count'] == 0


def test_api_auth_lifecycle(client):
    """Test API register, session persistence, and logout"""
    # Register
    reg_res = client.post('/api/auth/register', json={
        'username': 'apitester',
        'email': 'apitester@example.com',
        'password': 'Password123!',
        'full_name': 'API Tester'
    })
    assert reg_res.status_code == 201
    assert reg_res.get_json()['success'] is True

    # Check authenticated
    me_res = client.get('/api/auth/me')
    assert me_res.status_code == 200
    assert me_res.get_json()['authenticated'] is True
    assert me_res.get_json()['user']['username'] == 'apitester'

    # Logout
    out_res = client.post('/api/auth/logout')
    assert out_res.status_code == 200

    # Verify unauthenticated
    me_out = client.get('/api/auth/me')
    assert me_out.get_json()['authenticated'] is False


def test_cors_preflight_vercel_production(client):
    """Verify OPTIONS preflight request from Vercel production frontend is allowed with credentials"""
    origin = 'https://glossary-mart.vercel.app'
    res = client.options('/api/products', headers={
        'Origin': origin,
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type, Authorization'
    })
    assert res.status_code == 200
    assert res.headers.get('Access-Control-Allow-Origin') == origin
    assert res.headers.get('Access-Control-Allow-Credentials') == 'true'


def test_cors_vercel_preview_domain(client):
    """Verify CORS regex allows any Vercel preview or branch deployment domain"""
    origin = 'https://glossary-mart-branch-feature.vercel.app'
    res = client.get('/api/health', headers={'Origin': origin})
    assert res.status_code == 200
    assert res.headers.get('Access-Control-Allow-Origin') == origin
    assert res.headers.get('Access-Control-Allow-Credentials') == 'true'


def test_backend_portal_page_content(client):
    """Verify backend API portal page content at /api-portal"""
    res = client.get('/api-portal')
    assert res.status_code == 200
    content_upper = res.data.upper()
    assert b'E GROSSARY' in content_upper
    assert b'BACKEND' in content_upper
    assert b'/api/health' in res.data
    assert b'/auth/admin/login' in res.data


def test_api_profile_update(client, customer_user, session):
    """Verify updating user profile via PUT /api/auth/profile"""
    # Login first
    client.post('/api/auth/login', json={'username': customer_user.username, 'password': 'cust123'})
    
    # Update profile
    res = client.put('/api/auth/profile', json={
        'full_name': 'Updated Name',
        'phone': '9876543210',
        'address': '456 New Street, City'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['user']['full_name'] == 'Updated Name'
    assert data['user']['phone'] == '9876543210'
    assert data['user']['address'] == '456 New Street, City'


def test_api_product_review(client, customer_user, session):
    """Verify submitting product review via POST /api/products/<id>/reviews"""
    from database.models.product import Category, Product
    cat = Category(name='Organic Fruits')
    session.add(cat)
    session.commit()
    prod = Product(name='Organic Apple', selling_price=10.0, cost_price=6.0, stock_quantity=50, category_id=cat.id)
    session.add(prod)
    session.commit()

    # Login first
    client.post('/api/auth/login', json={'username': customer_user.username, 'password': 'cust123'})

    res = client.post(f'/api/products/{prod.id}/reviews', json={
        'rating': 5,
        'comment': 'Exceptional organic quality!'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert data['review']['rating'] == 5
    assert data['review']['comment'] == 'Exceptional organic quality!'

