"""Tests for POS Udhar (Store Credit / Khata) billing and Supplier CRUD."""
import pytest
from backend.models import db, User, Product, Category, Supplier, Purchase
from backend.models.product import PosBill, Sale
from backend.models.user import ActivityLog


def test_pos_udhar_checkout_existing_customer(client, admin_user, session):
    """Test POS checkout with payment_mode='Udhar' for an existing customer."""
    # 1. Setup Category and Product
    cat = Category(name='Grocery POS')
    session.add(cat)
    session.flush()

    prod = Product(
        name='Aashirvaad Atta 10kg',
        selling_price=450.0,
        cost_price=380.0,
        stock_quantity=20,
        category_id=cat.id,
        is_active=True
    )
    session.add(prod)

    # 2. Setup Customer with initial credit of 200.0
    cust = User(
        username='khata_ramesh',
        email='ramesh@khata.test',
        full_name='Ramesh Bhai Patel',
        phone='9825012345',
        role='customer',
        credit=200.0,
        is_verified=True
    )
    cust.set_password('pass123')
    session.add(cust)
    session.commit()

    # 3. Authenticate as admin
    client.post('/api/auth/login', json={'username': admin_user.username, 'password': 'admin123'})

    # 4. Perform POS checkout with Udhar
    res = client.post('/api/admin/pos/checkout', json={
        'cart': [{'id': prod.id, 'qty': 2}],
        'payment_mode': 'Udhar',
        'customer_phone': '9825012345',
        'customer_name': 'Ramesh Bhai Patel',
        'discount_amount': 50.0
    })

    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['payment_mode'] == 'Udhar'
    assert data['is_udhar'] is True
    # Subtotal: 450 * 2 = 900. Discount: 50. Net Total: 850.
    assert data['total'] == 850.0
    # Customer credit should be 200 (prior) + 850 (new) = 1050.0
    assert data['customer_credit'] == 1050.0

    # 5. Verify Database updates
    session.refresh(cust)
    assert float(cust.credit) == 1050.0

    bill = session.query(PosBill).filter_by(id=data['bill_id']).first()
    assert bill is not None
    assert bill.payment_method == 'Udhar'
    assert bill.total_amount == 850.0
    assert bill.customer_phone == '9825012345'

    # 6. Verify ActivityLog recorded
    log = session.query(ActivityLog).filter_by(action='POS_UDHAR_SALE', entity_id=cust.id).first()
    assert log is not None
    assert 'Udhar' in log.details


def test_pos_udhar_checkout_new_customer_provisioned(client, admin_user, session):
    """Test POS checkout with Udhar provisions a new customer profile when phone is new."""
    cat = Category(name='Dairy POS')
    session.add(cat)
    session.flush()

    prod = Product(
        name='Amul Butter 500g',
        selling_price=275.0,
        cost_price=240.0,
        stock_quantity=15,
        category_id=cat.id,
        is_active=True
    )
    session.add(prod)
    session.commit()

    client.post('/api/auth/login', json={'username': admin_user.username, 'password': 'admin123'})

    new_phone = '9876599999'
    res = client.post('/api/admin/pos/checkout', json={
        'cart': [{'id': prod.id, 'qty': 1}],
        'payment_mode': 'Udhar (Store Credit)',
        'customer_phone': new_phone,
        'customer_name': 'Kiran Thakor'
    })

    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['is_udhar'] is True
    assert data['total'] == 275.0
    assert data['customer_credit'] == 275.0

    # Verify newly created user
    new_user = session.query(User).filter_by(phone=new_phone).first()
    assert new_user is not None
    assert new_user.full_name == 'Kiran Thakor'
    assert new_user.role == 'customer'
    assert float(new_user.credit) == 275.0


def test_pos_udhar_requires_customer_identifier(client, admin_user, session):
    """Test POS checkout with Udhar is rejected if customer contact info is missing."""
    cat = Category(name='Snacks')
    session.add(cat)
    session.flush()

    prod = Product(
        name='Balaji Wafers',
        selling_price=20.0,
        cost_price=16.0,
        stock_quantity=50,
        category_id=cat.id,
        is_active=True
    )
    session.add(prod)
    session.commit()

    client.post('/api/auth/login', json={'username': admin_user.username, 'password': 'admin123'})

    # Try checking out as anonymous walk-in under Udhar
    res = client.post('/api/admin/pos/checkout', json={
        'cart': [{'id': prod.id, 'qty': 2}],
        'payment_mode': 'Udhar',
        'customer_phone': '',
        'customer_name': 'Walk-in'
    })

    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert 'required' in data['error'].lower()


def test_supplier_crud_operations(client, admin_user, session):
    """Test full Supplier CRUD: Create, Read, Update, Delete via Admin REST API."""
    client.post('/api/auth/login', json={'username': admin_user.username, 'password': 'admin123'})

    # 1. Create Supplier
    add_res = client.post('/api/admin/suppliers', json={
        'name': 'Unjha Spices Mandi Wholesale Co',
        'contact_person': 'Praful Patel',
        'phone': '9825001122',
        'email': 'praful@unjhaspices.com',
        'address': 'Shop 12, APMC Market Yard, Unjha - 384170',
        'gstin': '24AAACU1234F1Z1',
        'bank_details': 'BOB A/C: 123456789, IFSC: BARB0UNJHA'
    })

    assert add_res.status_code == 201
    add_data = add_res.get_json()
    assert add_data['success'] is True
    sup_id = add_data['supplier_id']
    assert sup_id > 0

    # Verify created in DB
    sup = session.get(Supplier, sup_id)
    assert sup is not None
    assert sup.name == 'Unjha Spices Mandi Wholesale Co'
    assert sup.phone == '9825001122'

    # 2. Read Supplier
    get_res = client.get(f'/api/admin/suppliers/{sup_id}')
    assert get_res.status_code == 200
    assert get_res.get_json()['name'] == 'Unjha Spices Mandi Wholesale Co'

    # 3. Update Supplier
    edit_res = client.put(f'/api/admin/suppliers/{sup_id}', json={
        'name': 'Unjha Spices & Seeds Wholesale Hub',
        'phone': '9825009999',
        'contact_person': 'Praful Patel (Managing Director)'
    })

    assert edit_res.status_code == 200
    assert edit_res.get_json()['success'] is True

    session.refresh(sup)
    assert sup.name == 'Unjha Spices & Seeds Wholesale Hub'
    assert sup.phone == '9825009999'
    assert sup.contact_person == 'Praful Patel (Managing Director)'

    # 4. Delete Supplier (safe because no purchases)
    del_res = client.delete(f'/api/admin/suppliers/{sup_id}')
    assert del_res.status_code == 200
    assert del_res.get_json()['success'] is True

    # Verify removed from DB
    assert session.get(Supplier, sup_id) is None


def test_supplier_delete_blocked_when_linked_to_purchases(client, admin_user, session):
    """Test that deleting a supplier with historical purchases is blocked with 409 Conflict."""
    client.post('/api/auth/login', json={'username': admin_user.username, 'password': 'admin123'})

    cat = Category(name='Spices')
    session.add(cat)
    session.flush()

    prod = Product(
        name='Jeera Seeds 500g',
        selling_price=300.0,
        cost_price=240.0,
        stock_quantity=10,
        category_id=cat.id,
        is_active=True
    )
    session.add(prod)

    sup = Supplier(name='Protected FMCG Supplier', phone='9876543210')
    session.add(sup)
    session.flush()

    purchase = Purchase(
        supplier_id=sup.id,
        product_id=prod.id,
        quantity=50,
        purchase_price=240.0,
        total_cost=12000.0,
        invoice_number='INV-PROT-01'
    )
    session.add(purchase)
    session.commit()

    # Attempt delete
    del_res = client.delete(f'/api/admin/suppliers/{sup.id}')
    assert del_res.status_code == 409
    data = del_res.get_json()
    assert data['success'] is False
    assert 'linked to past purchase' in data['message']

    # Supplier still exists in DB
    assert session.get(Supplier, sup.id) is not None
