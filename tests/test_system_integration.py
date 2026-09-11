"""
Comprehensive End-to-End System Integration Tests
Validates connectivity across Frontend, Backend, Database, and Services.
"""
from decimal import Decimal
import io
import json
import pytest

from database.models import db, User, Product, Category, Sale, Order, OrderItem, Supplier, Purchase, Coupon, Notification
from backend.services.inventory_service import InventoryService
from backend.services.storage_service import StorageService


@pytest.fixture
def test_category(session):
    cat = Category(name='Grocery', description='Essential groceries')
    session.add(cat)
    session.commit()
    return cat


@pytest.fixture
def test_product(session, test_category):
    prod = Product(
        name='Basmati Rice 5kg',
        category_id=test_category.id,
        cost_price=Decimal('350.00'),
        selling_price=Decimal('450.00'),
        stock_quantity=50,
        minimum_stock_alert=10,
        supplier_name='Quality Grains Co.',
        is_active=True
    )
    session.add(prod)
    session.commit()
    return prod


# ==============================================================================
# 1. Admin ERP & Operational Workflows
# ==============================================================================

def test_admin_dashboard_and_analytics(client, admin_user, test_product, session):
    """Test admin authentication, dashboard loading, and stats computation."""
    # 1. Login as admin
    login_resp = client.post('/auth/admin/login', data={
        'email': 'admin@test.com',
        'password': 'admin123',
    }, follow_redirects=True)
    assert login_resp.status_code == 200

    # 2. View Dashboard
    dash_resp = client.get('/admin/dashboard')
    assert dash_resp.status_code == 200
    assert b'Jay Goga' in dash_resp.data or b'Dashboard' in dash_resp.data

    # 3. View Coupons list (tests Coupon.created_at field)
    coupon = Coupon(
        code='SAVE10',
        discount_type='percentage',
        value=Decimal('10.00'),
        usage_limit=50
    )
    session.add(coupon)
    session.commit()

    coupons_resp = client.get('/admin/coupons')
    assert coupons_resp.status_code == 200
    assert b'SAVE10' in coupons_resp.data

    # 4. View Notifications API
    notif_resp = client.get('/admin/api/notifications')
    assert notif_resp.status_code == 200
    notif_data = json.loads(notif_resp.data)
    assert 'unread_count' in notif_data


def test_admin_pos_checkout_and_invoicing(client, admin_user, test_product, session):
    """Test POS checkout API, stock deduction, sale recording, and bill rendering."""
    # Authenticate as admin
    client.post('/auth/admin/login', data={'email': 'admin@test.com', 'password': 'admin123'})

    initial_stock = test_product.stock_quantity

    # 1. Complete a POS checkout transaction
    checkout_payload = {
        'cart': [
            {'id': test_product.id, 'qty': 2}
        ]
    }
    pos_resp = client.post(
        '/admin/api/pos/checkout',
        data=json.dumps(checkout_payload),
        content_type='application/json'
    )
    assert pos_resp.status_code == 200
    res_data = json.loads(pos_resp.data)
    assert res_data['success'] is True
    assert res_data['total'] == 900.00  # 450.00 * 2

    # Verify stock deduction
    session.refresh(test_product)
    assert test_product.stock_quantity == initial_stock - 2

    # 2. Verify Sale record was created
    sale = session.query(Sale).filter_by(product_id=test_product.id).first()
    assert sale is not None
    assert sale.quantity == 2
    assert sale.total_price == Decimal('900.00')

    # 3. Render printable bill
    bill_resp = client.get(f'/admin/sales/bill/{sale.id}')
    assert bill_resp.status_code == 200
    assert b'Basmati Rice 5kg' in bill_resp.data
    assert b'900' in bill_resp.data

    # 4. Export Sales CSV
    csv_resp = client.get('/admin/sales/export?format=csv')
    assert csv_resp.status_code == 200
    assert b'Basmati Rice' in csv_resp.data

    # 5. Export Sales PDF (ReportLab)
    pdf_resp = client.get('/admin/sales/export?format=pdf')
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers.get('Content-Type') == 'application/pdf'


def test_supplier_and_purchase_restocking(client, admin_user, test_product, session):
    """Test adding supplier, recording purchases, and restocking inventory."""
    client.post('/auth/admin/login', data={'email': 'admin@test.com', 'password': 'admin123'})

    # 1. Add Supplier
    supplier = Supplier(
        name='Apex Foods Ltd',
        contact_person='Rajesh Patel',
        phone='9876543210',
        email='apex@foods.com'
    )
    session.add(supplier)
    session.commit()

    # 2. Record Purchase Restock
    initial_stock = test_product.stock_quantity
    restock_qty = 25
    purchase = Purchase(
        supplier_id=supplier.id,
        product_id=test_product.id,
        quantity=restock_qty,
        purchase_price=Decimal('340.00'),
        total_cost=Decimal('8500.00')
    )
    session.add(purchase)

    # Use InventoryService to add stock
    ok, msg = InventoryService.add_stock(test_product.id, restock_qty, triggered_by='purchase')
    assert ok is True
    session.commit()

    session.refresh(test_product)
    assert test_product.stock_quantity == initial_stock + restock_qty


# ==============================================================================
# 2. Customer Storefront & E-Commerce Flow
# ==============================================================================

def test_customer_storefront_browsing_and_cart(client, customer_user, test_product, test_category):
    """Test customer login, browsing, searching, filtering, and cart operations."""
    # Login customer
    client.post('/auth/login', data={'email': 'cust@test.com', 'password': 'cust123'})

    # 1. Browse shop with category filter
    shop_resp = client.get(f'/shop?category={test_category.name}')
    assert shop_resp.status_code == 200
    assert b'Basmati Rice' in shop_resp.data

    # 2. View Product Detail
    detail_resp = client.get(f'/product/{test_product.id}')
    assert detail_resp.status_code == 200
    assert b'Basmati Rice 5kg' in detail_resp.data

    # 3. Add to Cart
    add_resp = client.post(f'/cart/add/{test_product.id}', data={'quantity': 3}, follow_redirects=True)
    assert add_resp.status_code == 200

    # 4. View Cart
    cart_resp = client.get('/cart')
    assert cart_resp.status_code == 200
    assert b'Basmati Rice' in cart_resp.data


def test_customer_checkout_cod_and_udhar(client, customer_user, test_product, session):
    """Test customer checkout with COD and Udhar (store credit) payment methods."""
    client.post('/auth/login', data={'email': 'cust@test.com', 'password': 'cust123'})

    # Add item to cart
    client.post(f'/cart/add/{test_product.id}', data={'quantity': 2}, follow_redirects=True)

    # Checkout with COD
    checkout_resp = client.post('/checkout', data={
        'shipping_address': 'Flat 402, Shivalik Residency, Ahmedabad, Gujarat',
        'payment_method': 'COD'
    }, follow_redirects=True)
    assert checkout_resp.status_code == 200
    assert b'Order' in checkout_resp.data or b'Confirmation' in checkout_resp.data

    # Verify Order in DB
    order = session.query(Order).filter_by(user_id=customer_user.id).order_by(Order.id.desc()).first()
    assert order is not None
    assert order.total_amount == Decimal('900.00')
    assert order.payment_method == 'COD'

    # Now add another item and checkout with UDHAR (Store Credit)
    client.post(f'/cart/add/{test_product.id}', data={'quantity': 1}, follow_redirects=True)
    udhar_resp = client.post('/checkout', data={
        'shipping_address': 'Flat 402, Shivalik Residency, Ahmedabad, Gujarat',
        'payment_method': 'UDHAR'
    }, follow_redirects=True)
    assert udhar_resp.status_code == 200

    session.refresh(customer_user)
    assert customer_user.credit == Decimal('450.00')


def test_admin_customer_credit_settlement(client, admin_user, customer_user, session):
    """Test admin clearing customer Udhar balance."""
    customer_user.credit = Decimal('1200.00')
    session.commit()

    # Login admin
    client.post('/auth/admin/login', data={'email': 'admin@test.com', 'password': 'admin123'})

    # Partial credit settlement (pay 500)
    clear_resp = client.post(f'/admin/customers/{customer_user.id}/clear_credit', data={
        'amount_paid': '500.00'
    }, follow_redirects=True)
    assert clear_resp.status_code == 200

    session.refresh(customer_user)
    assert float(customer_user.credit) == 700.00


# ==============================================================================
# 3. Inventory Locking & Threshold Alerts
# ==============================================================================

def test_inventory_service_oversell_protection_and_alerts(test_product, session):
    """Test atomic stock deduction, oversell prevention, and low-stock notification triggers."""
    test_product.stock_quantity = 5
    test_product.minimum_stock_alert = 10
    session.commit()

    # 1. Attempt to deduct more than available -> should fail safely
    success, msg = InventoryService.deduct_stock(test_product.id, 10, triggered_by='test')
    assert success is False
    assert 'Insufficient stock' in msg

    # 2. Deduct valid quantity that triggers low-stock alert
    success, msg = InventoryService.deduct_stock(test_product.id, 2, triggered_by='test')
    assert success is True
    session.commit()

    # Check alert was generated
    notif = session.query(Notification).filter_by(notif_type='warning').first()
    assert notif is not None
    assert 'Low Stock Alert' in notif.title


# ==============================================================================
# 4. Storage Service Clean Deletion
# ==============================================================================

def test_storage_service_safe_local_deletion(app):
    """Ensure StorageService safely handles local file paths without throwing errors."""
    with app.app_context():
        # Deleting non-existent or empty path should not crash
        StorageService.delete_file('')
        StorageService.delete_file('uploads/non_existent_image_12345.jpg')
