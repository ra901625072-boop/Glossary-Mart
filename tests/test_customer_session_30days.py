import time
from backend.models import User


def test_customer_login_30day_session(client, customer_user, session):
    """Verify customer login sets permanent session with 30-day expiration."""
    res = client.post('/api/auth/login', json={
        'email_or_username': customer_user.username,
        'password': 'cust123',
        'remember': True
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['user']['role'] == 'customer'
    assert 'expires_at' in data
    # Expiration should be roughly 30 days in the future (+- 10 seconds)
    expected_expiry = int(time.time() + 30 * 86400)
    assert abs(data['expires_at'] - expected_expiry) < 15

    # Check /api/auth/me returns authenticated and remaining session duration
    me_res = client.get('/api/auth/me')
    assert me_res.status_code == 200
    me_data = me_res.get_json()
    assert me_data['authenticated'] is True
    assert me_data['user']['username'] == customer_user.username
    assert 'session_expires_in' in me_data
    assert me_data['session_expires_in'] > 29 * 86400  # at least 29 days remaining


def test_customer_automatic_logout_after_30days(client, customer_user, session):
    """Verify customer is automatically logged out when 30 days have elapsed."""
    login_res = client.post('/api/auth/login', json={
        'email_or_username': customer_user.username,
        'password': 'cust123',
        'remember': True
    })
    assert login_res.status_code == 200

    # Simulate 31 days having passed since login
    with client.session_transaction() as sess:
        sess['login_time'] = time.time() - (31 * 86400)

    # Next call to /api/auth/me should automatically detect 30 days expired and log out
    me_res = client.get('/api/auth/me')
    me_data = me_res.get_json()
    assert me_data['authenticated'] is False
    assert me_data['user'] is None
    assert 'expired' in me_data.get('message', '').lower()

    # Further authenticated calls should fail
    orders_res = client.get('/api/orders')
    assert orders_res.status_code == 401


def test_customer_manual_logout(client, customer_user, session):
    """Verify manual logout clears the customer session immediately."""
    login_res = client.post('/api/auth/login', json={
        'email_or_username': customer_user.username,
        'password': 'cust123'
    })
    assert login_res.status_code == 200

    logout_res = client.post('/api/auth/logout')
    assert logout_res.status_code == 200
    assert logout_res.get_json()['success'] is True

    # User should now be unauthenticated
    me_res = client.get('/api/auth/me')
    assert me_res.get_json()['authenticated'] is False
