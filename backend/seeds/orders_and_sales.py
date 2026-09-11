"""
Authentic online orders and POS counter sales seed data.
Populates realistic 30-day historical transactions for dashboard charts and metrics.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from database.models import db
from database.models.order import Order, OrderItem
from database.models.product import Product, Sale
from database.models.user import User


def seed_orders_and_sales():
    """Seed authentic customer orders and counter POS sales."""
    now = datetime.now(timezone.utc)
    products = Product.query.all()
    if not products:
        return

    prod_map = {p.name: p for p in products}
    customers = User.query.filter_by(role='customer').all()
    if not customers:
        return
    primary_customer = customers[0]

    # 1. Seed Recent Online Orders
    if Order.query.count() == 0:
        orders_spec = [
            {
                'days_ago': 0.2, # Today
                'status': 'Out for Delivery',
                'pay_method': 'UPI',
                'pay_status': 'Paid',
                'items': [
                    ('Amul Taaza Fresh Toned Milk 1L', 2),
                    ('Fresh Farm Crisp Organic Tomatoes 1kg', 1),
                    ('Tata Tea Premium Desh Ki Chai 250g', 1)
                ]
            },
            {
                'days_ago': 1.5, # Yesterday
                'status': 'Delivered',
                'pay_method': 'COD',
                'pay_status': 'Paid',
                'items': [
                    ('Aashirvaad Superior MP Atta 5kg', 1),
                    ('Fortune Sunlite Refined Sunflower Oil 1L', 1),
                    ('Tata Salt Vacuum Evaporated 1kg', 1)
                ]
            },
            {
                'days_ago': 3.0,
                'status': 'Delivered',
                'pay_method': 'UPI',
                'pay_status': 'Paid',
                'items': [
                    ('Maggi 2-Minute Masala Instant Noodles 280g', 3),
                    ('Cadbury Dairy Milk Silk Chocolate 120g', 2),
                    ('Britannia Good Day Cashew Cookies 100g', 2)
                ]
            },
            {
                'days_ago': 5.0,
                'status': 'Delivered',
                'pay_method': 'UDHAR',
                'pay_status': 'Paid',
                'items': [
                    ('Tata Sampann Unpolished Toor Dal 1kg', 2),
                    ('Surf Excel Easy Wash Detergent Powder 1kg', 1),
                    ('Harpic Power Plus Toilet Cleaner 500ml', 1)
                ]
            },
            {
                'days_ago': 8.0,
                'status': 'Delivered',
                'pay_method': 'UPI',
                'pay_status': 'Paid',
                'items': [
                    ('Amul Pasteurised Salted Butter 500g', 1),
                    ('Ratnagiri Alphonso Mangoes (1 Dozen)', 1),
                    ('Fresh Farm Green Spinach (Palak) 250g', 2)
                ]
            },
            {
                'days_ago': 12.0,
                'status': 'Delivered',
                'pay_method': 'COD',
                'pay_status': 'Paid',
                'items': [
                    ('Aashirvaad Superior MP Atta 5kg', 2),
                    ('Fortune Sunlite Refined Sunflower Oil 1L', 2)
                ]
            }
        ]

        for ospec in orders_spec:
            order_date = now - timedelta(days=ospec['days_ago'])
            items_to_create = []
            order_total = Decimal('0.00')

            for prod_name, qty in ospec['items']:
                prod = prod_map.get(prod_name)
                if prod:
                    subtotal = prod.selling_price * qty
                    profit = (prod.selling_price - prod.cost_price) * qty
                    order_total += subtotal
                    items_to_create.append((prod.id, qty, prod.selling_price, profit))

            if items_to_create:
                order = Order(
                    user_id=primary_customer.id,
                    total_amount=order_total,
                    payment_method=ospec['pay_method'],
                    payment_status=ospec['pay_status'],
                    order_status=ospec['status'],
                    shipping_address=primary_customer.address or 'Shop 4, Market Yard, Pali Road, Mehsana 384260',
                    created_at=order_date
                )
                db.session.add(order)
                db.session.flush()

                for pid, qty, price, profit in items_to_create:
                    item = OrderItem(
                        order_id=order.id,
                        product_id=pid,
                        quantity=qty,
                        price=price,
                        profit=profit
                    )
                    db.session.add(item)
        db.session.commit()

    # 2. Seed In-Store Counter POS Sales (Spanning the past 30 days)
    if Sale.query.count() == 0:
        pos_sales = [
            ('Aashirvaad Superior MP Atta 5kg', 3, 1),
            ('Amul Taaza Fresh Toned Milk 1L', 8, 1),
            ('Tata Salt Vacuum Evaporated 1kg', 5, 2),
            ('Maggi 2-Minute Masala Instant Noodles 280g', 6, 2),
            ('Fortune Sunlite Refined Sunflower Oil 1L', 4, 3),
            ('Cadbury Dairy Milk Silk Chocolate 120g', 5, 4),
            ('Tata Tea Premium Desh Ki Chai 250g', 3, 5),
            ('Britannia Good Day Cashew Cookies 100g', 6, 6),
            ('Surf Excel Easy Wash Detergent Powder 1kg', 3, 7),
            ('Fresh Farm Crisp Organic Tomatoes 1kg', 8, 8),
            ('Tata Sampann Unpolished Toor Dal 1kg', 4, 10),
            ('Amul Pasteurised Salted Butter 500g', 4, 12),
            ('Harpic Power Plus Toilet Cleaner 500ml', 2, 14),
            ('Dabur Red Ayurvedic Toothpaste 300g', 3, 16),
            ('Fresh Farm Green Spinach (Palak) 250g', 5, 18),
            ('Ratnagiri Alphonso Mangoes (1 Dozen)', 2, 22)
        ]

        for prod_name, qty, days_ago in pos_sales:
            prod = prod_map.get(prod_name)
            if prod:
                total_price = prod.selling_price * qty
                profit = (prod.selling_price - prod.cost_price) * qty
                sale = Sale(
                    product_id=prod.id,
                    quantity=qty,
                    total_price=total_price,
                    profit=profit,
                    sale_date=now - timedelta(days=days_ago)
                )
                db.session.add(sale)
        db.session.commit()
