import io
import pyotp
import pytest
from database.models import db, User
from database.models.product import Category, Product, Sale
from database.models.order import Order, OrderItem
from backend.utils.files import validate_image_file, allowed_file
from backend.services.export_service import sanitize_csv_cell, generate_sales_csv
from backend.services.storage_service import StorageService


def test_2fa_enforcement_on_login(client, session):
    """VULN-01: Verify 2FA enforcement on login routes when 2FA is enabled."""
    from werkzeug.security import generate_password_hash
    secret = pyotp.random_base32()
    user = User(
        username='user2fa',
        email='user2fa@test.com',
        password_hash=generate_password_hash('pass1234'),
        role='customer',
        is_verified=True,
        two_factor_enabled=True,
        two_factor_secret=secret
    )
    session.add(user)
    session.commit()

    # 1. API Login should require 2FA
    res = client.post('/api/auth/login', json={'email': 'user2fa@test.com', 'password': 'pass1234'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['requires_2fa'] is True
    assert data['success'] is True

    # 2. Session should NOT have current_user authenticated
    res_prof = client.get('/api/auth/profile')
    assert res_prof.status_code == 401

    # 3. Invalid 2FA code should be rejected
    res_invalid = client.post('/api/auth/verify-2fa', json={'code': '000000'})
    assert res_invalid.status_code in (400, 401)

    # 4. Valid 2FA code completes login
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()
    res_valid = client.post('/api/auth/verify-2fa', json={'code': valid_code})
    assert res_valid.status_code == 200
    assert res_valid.get_json()['success'] is True

    # 5. User is now authenticated
    res_prof2 = client.get('/api/auth/profile')
    assert res_prof2.status_code == 200


def test_payment_idor_and_bola_prevention(client, session):
    """VULN-02: Verify payment session creation prevents IDOR / BOLA."""
    from werkzeug.security import generate_password_hash
    # Create two customers
    u1 = User(username='u1', email='u1@test.com', password_hash=generate_password_hash('p1'), role='customer', is_verified=True)
    u2 = User(username='u2', email='u2@test.com', password_hash=generate_password_hash('p2'), role='customer', is_verified=True)
    session.add_all([u1, u2])
    session.commit()

    # Create order for u1
    order1 = Order(user_id=u1.id, total_amount=500.0, order_status='Pending', payment_status='Pending', payment_method='CARD')
    session.add(order1)
    session.commit()

    # Login as u2
    client.post('/auth/login', data={'email': 'u2@test.com', 'password': 'p2'})

    # u2 tries to checkout u1's order
    res = client.post(f'/create-checkout-session/{order1.id}')
    assert res.status_code in (400, 403)
    data = res.get_json()
    assert 'error' in data or 'message' in data


def test_payment_tampering_rejection(client, session):
    """VULN-03: Verify payment success handler verifies ownership and order ID."""
    from werkzeug.security import generate_password_hash
    u1 = User(username='upay1', email='upay1@test.com', password_hash=generate_password_hash('pass'), role='customer', is_verified=True)
    u2 = User(username='upay2', email='upay2@test.com', password_hash=generate_password_hash('pass'), role='customer', is_verified=True)
    session.add_all([u1, u2])
    session.commit()

    order = Order(user_id=u1.id, total_amount=999.0, order_status='Pending', payment_status='Pending', payment_method='CARD')
    session.add(order)
    session.commit()

    # Login as u2 (wrong user)
    client.post('/auth/login', data={'email': 'upay2@test.com', 'password': 'pass'})

    # u2 attempts to mark u1's order as paid
    res = client.post(f'/payment/success/{order.id}?session_id=fake_session')
    assert res.status_code in (302, 400, 403)
    session.refresh(order)
    assert order.payment_status == 'Pending'


def test_udhar_credit_restriction(client, session):
    """VULN-09: Udhar payment method restricted to verified customers with limits."""
    from werkzeug.security import generate_password_hash
    from database.models.order import Cart
    u_credit_maxed = User(
        username='ucred',
        email='ucred@test.com',
        password_hash=generate_password_hash('pass'),
        role='customer',
        is_verified=True
    )
    u_credit_maxed.credit = 6000.0
    session.add(u_credit_maxed)
    session.commit()

    cat = Category(name='Udhar Cat', description='Desc')
    session.add(cat)
    session.flush()

    prod = Product(name='Udhar Prod', category_id=cat.id, cost_price=10.0, selling_price=25.0, stock_quantity=10, is_active=True)
    session.add(prod)
    session.flush()

    cart_item = Cart(user_id=u_credit_maxed.id, product_id=prod.id, quantity=1)
    session.add(cart_item)
    session.commit()

    # Login as customer
    client.post('/auth/login', data={'email': 'ucred@test.com', 'password': 'pass'})

    # Try to checkout with udhar
    res = client.post('/checkout', json={
        'payment_method': 'UDHAR',
        'shipping_address': '123 Test Street, Apartment 4B, City Area, State 123456'
    })
    # Must be rejected because credit limit is exceeded (> 5000)
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert 'Store credit (Udhar)' in data['message']


def test_wholesale_data_leakage_redaction(client, session):
    """VULN-06: Sensitive financial metrics redacted from public endpoints."""
    cat = Category(name='Secret Category', description='Desc')
    session.add(cat)
    session.flush()

    prod = Product(
        name='Wholesale Secret Product',
        category_id=cat.id,
        cost_price=120.0,
        selling_price=180.0,
        stock_quantity=50,
        minimum_stock_alert=10,
        supplier_name='Confidential Supplier Corp',
        is_active=True
    )
    session.add(prod)
    session.commit()

    res = client.get('/api/products')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True

    item = next((p for p in data['products'] if p['id'] == prod.id), None)
    assert item is not None
    assert 'cost_price' not in item
    assert 'profit_margin' not in item
    assert 'supplier_name' not in item
    assert 'minimum_stock_alert' not in item


def test_file_upload_rejection_and_uuid_naming(app):
    """VULN-07: Verify non-image files are rejected and safe UUIDs are generated."""
    # 1. Non-image text/script disguised as image
    fake_img = io.BytesIO(b"<?php echo 'malicious code'; ?>")
    fake_img.filename = "payload.php.jpg"

    is_valid, err = validate_image_file(fake_img, {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    assert is_valid is False
    assert "signatures" in err or "Corrupted" in err

    # 2. Genuine 1x1 GIF
    # GIF89a 1x1 transparent gif bytes
    gif_bytes = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    real_img = io.BytesIO(gif_bytes)
    real_img.filename = "avatar.gif"

    is_valid, ext = validate_image_file(real_img, {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    assert is_valid is True
    assert ext == 'gif'

    # Test upload_file produces uuid-based path
    with app.app_context():
        uploaded_path = StorageService.upload_file(real_img)
        assert uploaded_path.startswith("uploads/") or uploaded_path.startswith("https://")
        filename_only = uploaded_path.split('/')[-1]
        basename = filename_only.split('.')[0]
        assert len(basename) == 32  # uuid4 hex length
        StorageService.delete_file(uploaded_path)


def test_csv_formula_injection_sanitization():
    """VULN-11: Verify spreadsheet formula triggers are sanitized with prepended quote."""
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_csv_cell("+cmd|'/C calc'!A0") == "'+cmd|'/C calc'!A0"
    assert sanitize_csv_cell("-5+10") == "'-5+10"
    assert sanitize_csv_cell("\talert") == "'\talert"
    assert sanitize_csv_cell("Normal Product") == "Normal Product"
    assert sanitize_csv_cell(123) == "123"
    assert sanitize_csv_cell(None) == ""


def test_security_headers_and_csp(client):
    """VULN-13: Verify defensive HTTP security headers and refined CSP."""
    res = client.get('/api/health')
    assert res.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert res.headers.get('X-Content-Type-Options') == 'nosniff'
    assert res.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
    csp = res.headers.get('Content-Security-Policy', '')
    assert "frame-ancestors 'self'" in csp
    assert "img-src 'self' data: blob: *" not in csp


def test_cors_domain_isolation(client):
    """VULN-05: Ensure arbitrary third-party Vercel subdomains are not granted CORS access."""
    # Malicious arbitrary vercel subdomain
    res_bad = client.options('/api/health', headers={
        'Origin': 'https://evil-hacker.vercel.app',
        'Access-Control-Request-Method': 'GET'
    })
    allow_origin_bad = res_bad.headers.get('Access-Control-Allow-Origin')
    assert allow_origin_bad != 'https://evil-hacker.vercel.app'

    # Legitimate frontend origin
    res_good = client.options('/api/health', headers={
        'Origin': 'https://glossary-mart.vercel.app',
        'Access-Control-Request-Method': 'GET'
    })
    allow_origin_good = res_good.headers.get('Access-Control-Allow-Origin')
    assert allow_origin_good in ('https://glossary-mart.vercel.app', '*')


def test_rate_limiter_blocks_brute_force(client):
    """VULN-08: Ensure rate limiting restricts rapid authentication attempts."""
    # @limiter.limit("5 per minute") is set on /api/auth/login
    status_codes = []
    for _ in range(8):
        res = client.post('/api/auth/login', json={'email': 'wrong@test.com', 'password': 'bad'})
        status_codes.append(res.status_code)

    assert 429 in status_codes


def test_api_auth_decorator_content_negotiation(client, session):
    """RE-AUDIT-01: Verify auth decorators return 401/403 JSON on API/JSON requests."""
    from werkzeug.security import generate_password_hash

    # 1. Unauthenticated JSON client accessing admin route must receive 401 JSON, NOT a 302 redirect
    res_unauth = client.get('/admin/orders', headers={'Accept': 'application/json'})
    assert res_unauth.status_code == 401
    assert res_unauth.is_json
    assert res_unauth.get_json()['success'] is False
    assert 'Authentication required' in res_unauth.get_json()['message']

    # 2. Authenticated Customer accessing admin route must receive 403 JSON, NOT a 302 redirect
    cust = User(
        username='regular_customer',
        email='cust_negotiate@test.com',
        password_hash=generate_password_hash('cust1234'),
        role='customer',
        is_verified=True
    )
    session.add(cust)
    session.commit()

    client.post('/auth/login', data={'email': 'cust_negotiate@test.com', 'password': 'cust1234'})

    res_forbidden = client.get('/admin/orders', headers={'Accept': 'application/json'})
    assert res_forbidden.status_code == 403
    assert res_forbidden.is_json
    assert res_forbidden.get_json()['success'] is False
    assert 'Administrator privileges required' in res_forbidden.get_json()['message']


def test_cumulative_store_credit_boundary_enforcement(client, session):
    """RE-AUDIT-02: Ensure cumulative order amount cannot push credit balance above ₹5,000."""
    from werkzeug.security import generate_password_hash
    from database.models.order import Cart

    user = User(
        username='udhar_boundary_user',
        email='udhar_bound@test.com',
        password_hash=generate_password_hash('bound123'),
        role='customer',
        credit=4800.0,  # Below ₹5,000 threshold
        is_verified=True
    )
    session.add(user)
    session.flush()

    cat = Category(name='Bound Cat', description='Desc')
    session.add(cat)
    session.flush()

    # Product costs ₹300; 4800 + 300 = 5100 > 5000
    prod = Product(
        name='Boundary Prod',
        category_id=cat.id,
        cost_price=100.0,
        selling_price=300.0,
        stock_quantity=10,
        is_active=True
    )
    session.add(prod)
    session.flush()

    cart_item = Cart(user_id=user.id, product_id=prod.id, quantity=1)
    session.add(cart_item)
    session.commit()

    client.post('/auth/login', data={'email': 'udhar_bound@test.com', 'password': 'bound123'})

    res = client.post('/checkout', json={
        'payment_method': 'UDHAR',
        'shipping_address': '123 Test Street, Apartment 4B, City Area, State 123456'
    })
    # Must be rejected because cumulative credit exceeds ₹5,000
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert 'Store credit (Udhar)' in data['message']


def test_admin_cannot_checkout_online_orders(client, session):
    """RE-AUDIT-03: Ensure administrators cannot checkout online customer orders."""
    from werkzeug.security import generate_password_hash

    admin = User(
        username='checkout_admin',
        email='chk_admin@test.com',
        password_hash=generate_password_hash('adminpass'),
        role='admin',
        is_verified=True
    )
    session.add(admin)
    session.commit()

    client.post('/auth/admin/login', data={'email': 'chk_admin@test.com', 'password': 'adminpass'})

    res = client.post('/api/orders/checkout', json={
        'shipping_address': '123 Admin Office, Headquarters Tower, City 123456',
        'payment_method': 'COD'
    })
    assert res.status_code == 403
    data = res.get_json()
    assert data['success'] is False
    assert 'Only customers' in data['message']


def test_admin_purchase_atomic_inventory_and_audit_log(client, session):
    """RE-AUDIT-04: Ensure admin purchase restock is atomic and creates an ActivityLog."""
    from werkzeug.security import generate_password_hash
    from database.models.inventory import Supplier
    from database.models.user import ActivityLog

    admin = User(
        username='purchase_audit_admin',
        email='purch_admin@test.com',
        password_hash=generate_password_hash('adminpass'),
        role='admin',
        is_verified=True
    )
    session.add(admin)
    session.flush()

    sup = Supplier(name='Organic Vendor Hub', phone='9876543210', email='hub@vendor.com')
    session.add(sup)
    session.flush()

    cat = Category(name='Restock Cat', description='Desc')
    session.add(cat)
    session.flush()

    prod = Product(
        name='Restock Rice 5kg',
        category_id=cat.id,
        cost_price=200.0,
        selling_price=250.0,
        stock_quantity=20,
        is_active=True
    )
    session.add(prod)
    session.commit()

    client.post('/auth/admin/login', data={'email': 'purch_admin@test.com', 'password': 'adminpass'})

    res = client.post('/admin/purchases/add', json={
        'supplier_id': sup.id,
        'product_id': prod.id,
        'quantity': 15,
        'purchase_price': 195.0
    })
    assert res.status_code == 200
    assert res.get_json()['success'] is True

    # Verify stock updated
    session.refresh(prod)
    assert prod.stock_quantity == 35

    # Verify ActivityLog entry was recorded
    log = session.query(ActivityLog).filter_by(
        action='ADD_STOCK',
        entity_type='Product',
        entity_id=prod.id
    ).first()
    assert log is not None
    assert 'Restock Rice' in log.details


def test_admin_clear_credit_audit_log(client, session):
    """RE-AUDIT-05: Ensure credit settlement records an audit trail in ActivityLog."""
    from werkzeug.security import generate_password_hash
    from database.models.user import ActivityLog

    admin = User(
        username='credit_audit_admin',
        email='cred_admin@test.com',
        password_hash=generate_password_hash('adminpass'),
        role='admin',
        is_verified=True
    )
    cust = User(
        username='credit_debtor',
        email='debtor@test.com',
        password_hash=generate_password_hash('debtorpass'),
        role='customer',
        credit=1200.0,
        is_verified=True
    )
    session.add_all([admin, cust])
    session.commit()

    client.post('/auth/admin/login', data={'email': 'cred_admin@test.com', 'password': 'adminpass'})

    res = client.post(f'/admin/customers/{cust.id}/clear_credit', json={
        'amount_paid': 500.0
    })
    assert res.status_code == 200
    assert res.get_json()['success'] is True

    session.refresh(cust)
    assert float(cust.credit) == 700.0

    # Verify ActivityLog entry was recorded
    log = session.query(ActivityLog).filter_by(
        action='CLEAR_CUSTOMER_CREDIT',
        entity_type='User',
        entity_id=cust.id
    ).first()
    assert log is not None
    assert 'Settled ₹500.00 credit' in log.details


def test_api_logout_both_methods(client, session):
    """RE-AUDIT-06: Ensure /api/auth/logout accepts both GET and POST gracefully."""
    from werkzeug.security import generate_password_hash

    user = User(
        username='logout_test_user',
        email='logout_user@test.com',
        password_hash=generate_password_hash('logout123'),
        role='customer',
        is_verified=True
    )
    session.add(user)
    session.commit()

    # Test POST
    client.post('/api/auth/login', json={'email': 'logout_user@test.com', 'password': 'logout123'})
    res_post = client.post('/api/auth/logout')
    assert res_post.status_code == 200
    assert res_post.get_json()['success'] is True

    # Test GET
    client.post('/api/auth/login', json={'email': 'logout_user@test.com', 'password': 'logout123'})
    res_get = client.get('/api/auth/logout')
    assert res_get.status_code == 200
    assert res_get.get_json()['success'] is True

