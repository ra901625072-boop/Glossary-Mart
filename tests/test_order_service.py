import pytest
from database.models.order import Order, OrderItem
from database.models.product import Product, Category
from backend.services.order_service import OrderService

@pytest.fixture
def products(session):
    category = Category(name='Snacks', description='Snacks')
    session.add(category)
    session.commit()
    
    p1 = Product(
        name='Chips',
        cost_price=10.0,
        selling_price=20.0,
        stock_quantity=50,
        minimum_stock_alert=10,
        category_id=category.id,
        is_active=True
    )
    p2 = Product(
        name='Soda',
        cost_price=15.0,
        selling_price=30.0,
        stock_quantity=100,
        minimum_stock_alert=20,
        category_id=category.id,
        is_active=True
    )
    session.add_all([p1, p2])
    session.commit()
    return p1, p2

def test_process_checkout_success(app, session, customer_user, products, monkeypatch):
    """Test successful checkout process"""
    p1, p2 = products
    
    # Create mock cart items
    class MockCartItem:
        def __init__(self, product, quantity):
            self.product_id = product.id
            self.quantity = quantity
            self.subtotal = product.selling_price * quantity
            
    cart_items = [
        MockCartItem(p1, 2), # 2 chips = 40.0
        MockCartItem(p2, 1)  # 1 soda = 30.0
    ]
    
    with app.test_request_context():
        import flask_login
        monkeypatch.setattr(flask_login.utils, '_get_user', lambda: customer_user)
        
        success, order, message = OrderService.process_checkout(
            cart_items=cart_items,
            shipping_address='123 Test Street, Test City',
            payment_method='COD'
        )
        
        assert success is True
        assert order is not None
        assert order.total_amount == 70.0 # 40 + 30
        assert order.payment_method == 'COD'
        assert order.order_status == 'Pending'
        
        # Verify stock was deducted
        db_p1 = session.get(Product, p1.id)
        assert db_p1.stock_quantity == 48 # 50 - 2
        
        db_p2 = session.get(Product, p2.id)
        assert db_p2.stock_quantity == 99 # 100 - 1
        
        # Verify order items
        db_items = session.query(OrderItem).filter_by(order_id=order.id).all()
        assert len(db_items) == 2

def test_process_checkout_insufficient_stock(app, session, customer_user, products, monkeypatch):
    """Test checkout fails when trying to buy more than in stock"""
    p1, p2 = products
    
    # Try to buy 60 chips when only 50 are in stock
    class MockCartItem:
        def __init__(self, product, quantity):
            self.product_id = product.id
            self.quantity = quantity
            self.subtotal = product.selling_price * quantity
            
    cart_items = [MockCartItem(p1, 60)]
    
    with app.test_request_context():
        import flask_login
        monkeypatch.setattr(flask_login.utils, '_get_user', lambda: customer_user)
        
        success, order, message = OrderService.process_checkout(
            cart_items=cart_items,
            shipping_address='123 Test Street',
            payment_method='UPI'
        )
        
        assert success is False
        assert 'Insufficient stock' in message
        
        # Verify stock was NOT deducted
        db_p1 = session.get(Product, p1.id)
        assert db_p1.stock_quantity == 50


def test_process_checkout_netbanking(app, session, customer_user, products, monkeypatch):
    """Test successful checkout with NETBANKING payment method"""
    p1, _ = products
    
    class MockCartItem:
        def __init__(self, product, quantity):
            self.product_id = product.id
            self.quantity = quantity
            self.subtotal = product.selling_price * quantity
            
    cart_items = [MockCartItem(p1, 5)]
    
    with app.test_request_context():
        import flask_login
        monkeypatch.setattr(flask_login.utils, '_get_user', lambda: customer_user)
        
        success, order, message = OrderService.process_checkout(
            cart_items=cart_items,
            shipping_address='789 Commercial Boulevard, Ahmedabad',
            payment_method='NETBANKING'
        )
        
        assert success is True
        assert order is not None
        assert order.payment_method == 'NETBANKING'
        assert order.order_status == 'Pending'
        
        db_p1 = session.get(Product, p1.id)
        assert db_p1.stock_quantity == 45 # 50 - 5


def test_admin_orders_api_and_status_alias(client, admin_user, customer_user, products, session):
    """Test admin orders list includes customer profile and status alias normalization"""
    p1, _ = products
    
    # 1. Create an order for customer_user
    customer_user.phone = '9876543210'
    customer_user.full_name = 'Anita Sharma'
    session.commit()
    
    order = Order(
        user_id=customer_user.id,
        shipping_address='789 Commercial Boulevard, Ahmedabad',
        payment_method='COD',
        order_status='Pending',
        payment_status='Pending',
        total_amount=100.0
    )
    session.add(order)
    session.flush()
    
    order_item = OrderItem(
        order_id=order.id,
        product_id=p1.id,
        quantity=5,
        price=20.0,
        profit=50.0
    )
    session.add(order_item)
    # Deduct initial stock for order
    p1.stock_quantity -= 5
    session.commit()
    assert p1.stock_quantity == 45
    
    # 2. Login as admin
    client.post('/auth/admin/login', data={'email': 'admin@test.com', 'password': 'admin123'})
    
    # 3. GET /admin/orders - verify customer profile in response
    resp = client.get('/admin/orders')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['orders']) >= 1
    ord_summary = next(o for o in data['orders'] if o['id'] == order.id)
    assert ord_summary['customer_name'] == 'Anita Sharma'
    assert ord_summary['customer_phone'] == '9876543210'
    assert ord_summary['customer_email'] == 'cust@test.com'
    
    # 4. GET /admin/orders/<id> - verify single detail
    detail_resp = client.get(f'/admin/orders/{order.id}')
    assert detail_resp.status_code == 200
    detail_data = detail_resp.get_json()
    assert detail_data['customer_name'] == 'Anita Sharma'
    assert detail_data['customer_phone'] == '9876543210'
    
    # 5. Update status using alias 'Confirmed' -> should become 'Processing'
    update_resp = client.post(f'/admin/orders/{order.id}/update-status', json={
        'order_status': 'Confirmed'
    })
    assert update_resp.status_code == 200
    assert update_resp.get_json()['order_status'] == 'Processing'
    session.refresh(order)
    assert order.order_status == 'Processing'
    
    # 6. Update status using alias 'Shipped' -> should become 'Out for Delivery'
    update_resp = client.post(f'/admin/orders/{order.id}/update-status', json={
        'order_status': 'Shipped'
    })
    assert update_resp.status_code == 200
    assert update_resp.get_json()['order_status'] == 'Out for Delivery'
    session.refresh(order)
    assert order.order_status == 'Out for Delivery'
    
    # 7. Test invalid transition: from Out for Delivery directly to Pending should be rejected
    inv_resp = client.post(f'/admin/orders/{order.id}/update-status', json={
        'order_status': 'Pending'
    })
    assert inv_resp.status_code == 400
    assert inv_resp.get_json()['success'] is False
    
    # 8. Cancel order: Out for Delivery -> Cancelled should restore inventory
    cancel_resp = client.post(f'/admin/orders/{order.id}/update-status', json={
        'order_status': 'Cancelled'
    })
    assert cancel_resp.status_code == 200
    session.refresh(p1)
    assert p1.stock_quantity == 50 # Restored from 45 back to 50!


def test_api_checkout_payload_cart_sync(client, customer_user, products, session):
    """Test customer checkout via /api/orders/checkout with items payload sync and stock reduction"""
    p1, _ = products
    initial_stock = p1.stock_quantity
    
    # Login as customer
    client.post('/auth/login', data={'email': 'cust@test.com', 'password': 'cust123'})
    
    checkout_payload = {
        'shipping_address': 'Flat 101, Galaxy Tower, SG Highway, Ahmedabad',
        'payment_method': 'NETBANKING',
        'items': [
            {'product_id': p1.id, 'quantity': 4}
        ]
    }
    
    resp = client.post('/api/orders/checkout', json=checkout_payload)
    assert resp.status_code == 201
    resp_data = resp.get_json()
    assert resp_data['success'] is True
    assert resp_data['order']['payment_method'] == 'NETBANKING'
    
    # Verify stock deducted in DB
    session.refresh(p1)
    assert p1.stock_quantity == initial_stock - 4


def test_api_checkout_out_of_stock_rejected(client, customer_user, products, session):
    """Test customer checkout via /api/orders/checkout rejects out of stock products without wiping cart"""
    p1, p2 = products
    p1.stock_quantity = 0
    session.commit()

    client.post('/auth/login', data={'email': 'cust@test.com', 'password': 'cust123'})

    checkout_payload = {
        'shipping_address': 'Flat 101, Galaxy Tower, SG Highway, Ahmedabad',
        'payment_method': 'COD',
        'items': [
            {'product_id': p1.id, 'quantity': 1}
        ]
    }

    resp = client.post('/api/orders/checkout', json=checkout_payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['success'] is False
    assert 'Out Of Stock' in data['message']
    assert data.get('error_code') == 'OUT_OF_STOCK'


