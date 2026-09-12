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


def test_api_cart_sync(client, session):
    """Test batch syncing offline items into server cart via POST /api/cart/sync"""
    cat = Category(name='Sync Pantry')
    session.add(cat)
    session.flush()

    p1 = Product(name='Synced Item 1', selling_price=50.0, cost_price=30.0, stock_quantity=20, category_id=cat.id)
    p2 = Product(name='Synced Item 2', selling_price=100.0, cost_price=70.0, stock_quantity=15, category_id=cat.id)
    session.add_all([p1, p2])
    session.commit()

    res = client.post('/api/cart/sync', json={
        'items': [
            {'product_id': p1.id, 'quantity': 2},
            {'product_id': p2.id, 'quantity': 1}
        ]
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['cart']['item_count'] == 3
    assert data['cart']['total'] == 200.0


def test_api_checkout_and_invoice_pdf(client, customer_user, session):
    """Test full checkout flow and binary PDF invoice generation via GET /api/orders/<id>/invoice"""
    cat = Category(name='Dairy & Beverages')
    session.add(cat)
    session.flush()

    prod = Product(name='Amul Full Cream Milk 1L', selling_price=64.0, cost_price=55.0, stock_quantity=25, category_id=cat.id)
    session.add(prod)
    session.commit()

    # Login as customer
    login_res = client.post('/api/auth/login', json={'username': customer_user.username, 'password': 'cust123'})
    assert login_res.status_code == 200

    # Checkout with inline items payload
    checkout_res = client.post('/api/orders/checkout', json={
        'items': [{'product_id': prod.id, 'quantity': 2, 'price': 64.0, 'name': prod.name}],
        'payment_method': 'cash_on_delivery',
        'delivery_address': 'Flat 402, Green Avenue, City',
        'phone': '9876543210',
        'notes': 'Please ring bell'
    })
    assert checkout_res.status_code == 201
    order_data = checkout_res.get_json()
    assert order_data['success'] is True
    order_id = order_data['order']['id']
    assert order_data['order']['total_amount'] == 128.0

    # Retrieve downloadable PDF invoice
    invoice_res = client.get(f'/api/orders/{order_id}/invoice')
    assert invoice_res.status_code == 200
    assert invoice_res.headers.get('Content-Type') == 'application/pdf'
    assert invoice_res.data.startswith(b'%PDF')


def test_api_admin_dual_blueprint_endpoints(client, admin_user, session):
    """Verify dual blueprint routing allows /api/admin/* endpoints for decoupled frontends"""
    # Login as admin
    login_res = client.post('/api/auth/login', json={'username': admin_user.username, 'password': 'admin123'})
    assert login_res.status_code == 200

    # Dashboard endpoint via /api/admin
    dash_res = client.get('/api/admin/dashboard')
    assert dash_res.status_code == 200
    dash_data = dash_res.get_json()
    assert dash_data['success'] is True
    assert 'stats' in dash_data

    # Products listing via /api/admin
    prod_res = client.get('/api/admin/products')
    assert prod_res.status_code == 200
    prod_data = prod_res.get_json()
    assert prod_data['success'] is True
    assert 'products' in prod_data


def test_api_admin_pos_checkout(client, admin_user, session):
    """Verify POS direct sale and atomic inventory deduction via /api/admin/pos/checkout"""
    cat = Category(name='POS Category')
    session.add(cat)
    session.flush()

    prod = Product(name='POS Rice 5kg', selling_price=300.0, cost_price=240.0, stock_quantity=10, category_id=cat.id)
    session.add(prod)
    session.commit()

    # Login as admin
    client.post('/api/auth/login', json={'username': admin_user.username, 'password': 'admin123'})

    # Execute POS sale
    pos_res = client.post('/api/admin/pos/checkout', json={
        'items': [{'id': prod.id, 'price': 300.0, 'quantity': 3}],
        'payment_method': 'cash',
        'customer_name': 'Walk-in Customer',
        'customer_phone': '9876500000',
        'discount_applied': 0
    })
    assert pos_res.status_code == 200
    pos_data = pos_res.get_json()
    assert pos_data['success'] is True
    assert pos_data['total'] == 900.0

    # Verify inventory was atomically deducted
    session.refresh(prod)
    assert prod.stock_quantity == 7


def test_api_coupon_validation(client, session):
    """Test coupon validation against live database promotions"""
    from database.models.promotion import Coupon
    # Percentage coupon with minimum spend
    c1 = Coupon(
        code='FESTIVE15',
        discount_type='percentage',
        value=15.0,
        min_order_amount=500.0,
        is_active=True
    )
    # Flat coupon
    c2 = Coupon(
        code='FLAT50',
        discount_type='flat',
        value=50.0,
        min_order_amount=0.0,
        is_active=True
    )
    # Inactive coupon
    c3 = Coupon(
        code='DISABLED20',
        discount_type='percentage',
        value=20.0,
        is_active=False
    )
    session.add_all([c1, c2, c3])
    session.commit()

    # 1. Below minimum spend fails
    res_below = client.post('/api/coupons/validate', json={'code': 'FESTIVE15', 'cart_total': 300.0})
    assert res_below.status_code == 400
    assert res_below.get_json()['success'] is False
    assert 'minimum spend' in res_below.get_json()['message']

    # 2. Above minimum spend succeeds and calculates exact percentage
    res_valid = client.post('/api/coupons/validate', json={'code': 'FESTIVE15', 'cart_total': 1000.0})
    assert res_valid.status_code == 200
    data_valid = res_valid.get_json()
    assert data_valid['success'] is True
    assert data_valid['coupon']['discount_amount'] == 150.0
    assert data_valid['coupon']['final_total'] == 850.0

    # 3. Flat coupon succeeds
    res_flat = client.post('/api/coupons/validate', json={'code': 'FLAT50', 'cart_total': 200.0})
    assert res_flat.status_code == 200
    assert res_flat.get_json()['coupon']['discount_amount'] == 50.0
    assert res_flat.get_json()['coupon']['final_total'] == 150.0

    # 4. Inactive coupon fails
    res_inactive = client.post('/api/coupons/validate', json={'code': 'DISABLED20', 'cart_total': 500.0})
    assert res_inactive.status_code == 400
    assert 'inactive' in res_inactive.get_json()['message']

    # 5. Nonexistent coupon returns 404
    res_invalid = client.post('/api/coupons/validate', json={'code': 'NONEXISTENT'})
    assert res_invalid.status_code == 404
    assert res_invalid.get_json()['success'] is False



