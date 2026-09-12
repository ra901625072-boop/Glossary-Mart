import pytest
import os

# Set environment variables BEFORE importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'true'
os.environ['SECRET_KEY'] = 'super-secret-test-key-for-pytest-12345'
os.environ['WTF_CSRF_ENABLED'] = 'false'
os.environ['SKIP_DB_CREATE'] = 'false'
os.environ['ADMIN_PASSWORD'] = 'strongadminpass123'
os.environ['ADMIN_USERNAME'] = 'testadmin'

from flask import current_app
from backend import create_app
from database.models import db, User

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost.localdomain'
    })

    yield app

@pytest.fixture(scope='session')
def _db(app):
    """Provide the transactional fixtures with access to the database."""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def session(_db, app):
    """Creates a new database session for a test. Rollback after test."""
    with app.app_context():
        yield _db.session
        
        _db.session.rollback()
        # Clean up all data after each test
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()
        _db.session.remove()

from backend.extensions import limiter

@pytest.fixture(scope='function')
def client(app, session):
    """A test client for the app."""
    limiter.reset()
    return app.test_client()

@pytest.fixture(scope='function')
def admin_user(session):
    """Creates and returns a test admin user."""
    from werkzeug.security import generate_password_hash
    admin = User(
        username='testadmin',
        email='admin@test.com',
        password_hash=generate_password_hash('admin123'),
        role='admin',
        full_name='Test Admin',
        is_verified=True
    )
    session.add(admin)
    session.commit()
    return admin

@pytest.fixture(scope='function')
def customer_user(session):
    """Creates and returns a test customer user."""
    from werkzeug.security import generate_password_hash
    customer = User(
        username='testcust',
        email='cust@test.com',
        password_hash=generate_password_hash('cust123'),
        role='customer',
        full_name='Test Customer',
        is_verified=True
    )
    session.add(customer)
    session.commit()
    return customer
