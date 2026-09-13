import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from database.models import db, User, Product, Category, Sale, Order, OrderItem, Supplier, Purchase
from database.models.expense import Expense
from backend.services.intelligence_service import IntelligenceService


def test_health_score_calculation(app, session):
    """Test Health Score composite index and sub-metrics."""
    with app.app_context():
        # Setup basic product and category
        cat = Category(name='Produce', description='Fresh produce')
        session.add(cat)
        session.commit()

        p1 = Product(name='Fresh Apples 1kg', category_id=cat.id, cost_price=60, selling_price=90, stock_quantity=50, minimum_stock_alert=10)
        p2 = Product(name='Ripe Bananas 1dz', category_id=cat.id, cost_price=30, selling_price=45, stock_quantity=4, minimum_stock_alert=10)
        session.add_all([p1, p2])
        session.commit()

        # Add customer
        cust = User(username='shopper1', email='shop1@test.com', password_hash='hash', role='customer', credit=500)
        session.add(cust)
        session.commit()

        # Add a sale
        sale = Sale(product_id=p1.id, quantity=5, total_price=450, profit=150)
        session.add(sale)
        session.commit()

        res = IntelligenceService.calculate_health_score()
        assert 'overall_score' in res
        assert 1 <= res['overall_score'] <= 100
        assert res['status'] in ['Healthy', 'Moderate', 'At Risk']
        assert 'components' in res
        assert 'sales' in res['components']
        assert 'inventory' in res['components']
        assert 'profit' in res['components']
        assert 'customers' in res['components']
        assert 'credit' in res['components']


def test_ai_insights_and_action_center(app, session):
    """Test automated business insights rule triggers."""
    with app.app_context():
        cat = Category(name='Dairy', description='Milk and curd')
        session.add(cat)
        session.commit()

        # Item running critically low
        p = Product(name='Fresh Milk 1L', category_id=cat.id, cost_price=40, selling_price=55, stock_quantity=2, minimum_stock_alert=15)
        session.add(p)
        session.commit()

        # Add sale to establish burn rate
        sale = Sale(product_id=p.id, quantity=10, total_price=550, profit=150)
        session.add(sale)
        session.commit()

        insights = IntelligenceService.generate_ai_insights()
        assert isinstance(insights, list)

        # Action center alerts
        alerts = IntelligenceService.get_action_center_alerts()
        assert 'critical' in alerts
        assert 'warnings' in alerts
        assert 'opportunities' in alerts


def test_forecast_and_inventory_intelligence(app, session):
    """Test sales demand forecast and dead stock capital analysis."""
    with app.app_context():
        cat = Category(name='Staples', description='Rice and flour')
        session.add(cat)
        session.commit()

        # Active product
        p_active = Product(name='Basmati Rice 5kg', category_id=cat.id, cost_price=300, selling_price=450, stock_quantity=30, minimum_stock_alert=5)
        # Dead product (no sales)
        p_dead = Product(name='Rare Grain 1kg', category_id=cat.id, cost_price=200, selling_price=350, stock_quantity=15, minimum_stock_alert=2)
        session.add_all([p_active, p_dead])
        session.commit()

        # Sales for active product
        s = Sale(product_id=p_active.id, quantity=6, total_price=2700, profit=900)
        session.add(s)
        session.commit()

        forecast = IntelligenceService.forecast_sales_and_demand()
        assert 'tomorrow_sales_forecast' in forecast
        assert 'expected_monthly_revenue' in forecast
        assert 'confidence_score' in forecast
        assert isinstance(forecast['reorder_recommendations'], list)

        inv_intel = IntelligenceService.analyze_inventory_intelligence()
        assert inv_intel['dead_stock_value'] >= 3000.0  # 15 * 200
        assert inv_intel['total_inventory_value'] > 0
        assert 'aging_buckets' in inv_intel


def test_cash_flow_and_bcg_matrix(app, session):
    """Test cash flow ledger and BCG profitability matrix."""
    with app.app_context():
        cat = Category(name='Snacks', description='Crisps and biscuits')
        session.add(cat)
        session.commit()

        p = Product(name='Potato Chips', category_id=cat.id, cost_price=10, selling_price=20, stock_quantity=100, minimum_stock_alert=20)
        session.add(p)
        session.commit()

        # Add Sale (Money In)
        s = Sale(product_id=p.id, quantity=10, total_price=200, profit=100)
        # Add Expense (Money Out)
        e = Expense(category='Electricity', amount=120, payment_mode='UPI', description='Power bill')
        session.add_all([s, e])
        session.commit()

        cf = IntelligenceService.calculate_cash_flow()
        assert 'today' in cf
        assert 'monthly' in cf
        assert cf['today']['money_in'] >= 200.0
        assert cf['today']['money_out'] >= 120.0
        assert cf['today']['net_cash_flow'] == cf['today']['money_in'] - cf['today']['money_out']

        matrix = IntelligenceService.generate_profitability_matrix()
        assert 'counts' in matrix
        assert 'stars' in matrix['counts']
        assert 'review_price' in matrix['counts']
        assert 'promote' in matrix['counts']
        assert 'dead_stock' in matrix['counts']


def test_expenses_endpoints(client, admin_user):
    """Test Expense management REST endpoints."""
    # Login as admin
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)

    # 1. Add expense
    res = client.post('/admin/expenses/add', json={
        'category': 'Rent',
        'amount': 5000.00,
        'payment_mode': 'Bank Transfer',
        'description': 'Shop Pali rent for September',
        'is_recurring': True
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    exp_id = data['expense']['id']

    # 2. List expenses
    list_res = client.get('/admin/expenses')
    assert list_res.status_code == 200
    list_data = list_res.get_json()
    assert list_data['success'] is True
    assert len(list_data['expenses']) >= 1
    assert list_data['summary']['monthly_total'] >= 5000.00

    # 3. Delete expense
    del_res = client.delete(f'/admin/expenses/{exp_id}')
    assert del_res.status_code == 200
    assert del_res.get_json()['success'] is True


def test_intelligence_endpoints(client, admin_user):
    """Test Admin Intelligence API endpoints."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)

    res = client.get('/admin/intelligence')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'health_score' in data
    assert 'ai_insights' in data
    assert 'forecast' in data
    assert 'cash_flow' in data
    assert 'profitability_matrix' in data

    # Test individual sub-endpoints
    res_ac = client.get('/admin/action-center')
    assert res_ac.status_code == 200
    assert 'critical' in res_ac.get_json()

    res_cf = client.get('/admin/cashflow')
    assert res_cf.status_code == 200
    assert 'cash_flow' in res_cf.get_json()

    res_hs = client.get('/admin/health-score')
    assert res_hs.status_code == 200
    assert 'health_score' in res_hs.get_json()


def test_customer_and_category_intelligence(app, session):
    """Test customer RFM intelligence and category contribution analysis."""
    with app.app_context():
        cat1 = Category(name='Bakery', description='Fresh breads')
        cat2 = Category(name='Beverages', description='Juices and drinks')
        session.add_all([cat1, cat2])
        session.commit()

        p1 = Product(name='Whole Wheat Bread', category_id=cat1.id, cost_price=25, selling_price=40, stock_quantity=20, minimum_stock_alert=5)
        p2 = Product(name='Orange Juice 1L', category_id=cat2.id, cost_price=60, selling_price=100, stock_quantity=15, minimum_stock_alert=3)
        session.add_all([p1, p2])
        session.commit()

        # Customer with orders
        cust = User(username='vip_shopper', email='vip@test.com', password_hash='hash', role='customer', credit=250)
        session.add(cust)
        session.commit()

        order = Order(user_id=cust.id, order_status='Delivered', payment_status='Paid', total_amount=140)
        session.add(order)
        session.commit()

        # Sales
        s1 = Sale(product_id=p1.id, quantity=1, total_price=40, profit=15)
        s2 = Sale(product_id=p2.id, quantity=1, total_price=100, profit=40)
        session.add_all([s1, s2])
        session.commit()

        cust_intel = IntelligenceService.analyze_customer_intelligence()
        assert 'retention_rate_pct' in cust_intel
        assert 'total_customers' in cust_intel
        assert cust_intel['total_customers'] >= 1
        assert 'vip_customers' in cust_intel
        assert 'overdue_receivables_amount' in cust_intel
        assert cust_intel['overdue_receivables_amount'] >= 250.0

        cat_intel = IntelligenceService.analyze_category_intelligence()
        assert isinstance(cat_intel, list)
        assert len(cat_intel) >= 2
        cat_names = [c['category_name'] for c in cat_intel]
        assert 'Bakery' in cat_names
        assert 'Beverages' in cat_names
