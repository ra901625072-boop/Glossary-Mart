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
