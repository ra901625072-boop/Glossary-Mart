def test_landing_page(client):
    """Test that the landing page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Jay Goga Mart' in response.data

def test_login_page(client):
    """Test that the customer login page loads"""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Login' in response.data or b'Customer' in response.data or b'Email' in response.data

def test_admin_login_page(client):
    """Test that the admin login page loads"""
    response = client.get('/auth/admin/login')
    assert response.status_code == 200
    assert b'Institutional Access' in response.data or b'Login' in response.data

def test_shop_page_redirects_unauthenticated(client):
    """Test that shop page redirects if not logged in"""
    response = client.get('/shop')
    # Should redirect to login
    assert response.status_code == 302
    assert '/auth/login' in response.headers.get('Location', '')

def test_shop_page_authenticated(client, customer_user, app):
    """Test that shop page loads for authenticated customer"""
    with app.test_client() as c:
        # We can bypass login screen for test by setting session directly,
        # but it's cleaner to mock or actually log in. Let's do a real POST.
        response = c.post('/auth/login', data={
            'email': 'cust@test.com',
            'password': 'cust123',
            'csrf_token': 'dummy' # WTF_CSRF_ENABLED is False in test config
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Customer Super-App' in response.data or b'Jay Goga Mart' in response.data
        
        # Now access shop
        shop_response = c.get('/shop')
        assert shop_response.status_code == 200
