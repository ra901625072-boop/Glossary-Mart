import pytest
from database.models.order import Cart
from database.models.product import Product, Category
from backend.services.cart_service import CartService

@pytest.fixture
def product(session):
    category = Category(name='Test Category', description='Test')
    session.add(category)
    session.commit()
    
    prod = Product(
        name='Test Product',
        cost_price=10.0,
        selling_price=15.0,
        stock_quantity=10,
        minimum_stock_alert=2,
        category_id=category.id,
        is_active=True
    )
    session.add(prod)
    session.commit()
    return prod

def test_add_item_guest(app, session, product, monkeypatch):
    """Test adding an item to the cart as a guest (using Flask session object directly)"""
    with app.test_request_context():
        # Mock flask_login.current_user to simulate guest
        class MockAnonymousUser:
            is_authenticated = False
            role = None
            
        import flask_login
        monkeypatch.setattr(flask_login.utils, '_get_user', lambda: MockAnonymousUser())
        
        from flask import session as flask_session
        flask_session['cart'] = {}
        
        success, message = CartService.add_item(product.id, 2)
        
        assert success is True
        assert 'added to cart' in message
        assert str(product.id) in flask_session['cart']
        assert flask_session['cart'][str(product.id)] == 2

def test_add_item_exceeds_stock(app, session, product, monkeypatch):
    """Test adding more items than available in stock"""
    with app.test_request_context():
        class MockAnonymousUser:
            is_authenticated = False
            role = None
            
        import flask_login
        monkeypatch.setattr(flask_login.utils, '_get_user', lambda: MockAnonymousUser())
        
        from flask import session as flask_session
        flask_session['cart'] = {}
        
        # Try to add 15 when only 10 are in stock
        success, message = CartService.add_item(product.id, 15)
        
        assert success is False
        assert 'available' in message
        assert str(product.id) not in flask_session['cart']

def test_add_item_authenticated(app, session, product, customer_user, monkeypatch):
    """Test adding an item to the cart as an authenticated customer"""
    with app.test_request_context():
        # Mock current_user
        import flask_login
        monkeypatch.setattr(flask_login.utils, '_get_user', lambda: customer_user)
        
        success, message = CartService.add_item(product.id, 3)
        
        assert success is True
        
        # Verify it went to the database
        cart_item = session.query(Cart).filter_by(user_id=customer_user.id, product_id=product.id).first()
        assert cart_item is not None
        assert cart_item.quantity == 3
