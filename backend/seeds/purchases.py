"""
Inventory purchase orders and inward restocking batches seed data.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from database.models import db
from database.models.inventory import Purchase, Supplier
from database.models.product import Product


def seed_purchases(supplier_map):
    """Seed authentic purchase orders and inward stock receipts."""
    if Purchase.query.count() == 0:
        # Match products with appropriate suppliers
        now = datetime.now(timezone.utc)
        purchases_data = [
            # Amul Milk & Butter
            {
                'supplier_name': 'Gujarat Co-operative Milk Marketing Federation (Amul)',
                'product_name': 'Amul Taaza Fresh Toned Milk 1L',
                'quantity': 100,
                'price': Decimal('48.00'),
                'days_ago': 2
            },
            {
                'supplier_name': 'Gujarat Co-operative Milk Marketing Federation (Amul)',
                'product_name': 'Amul Pasteurised Salted Butter 500g',
                'quantity': 50,
                'price': Decimal('125.00'),
                'days_ago': 5
            },
            # ITC Atta
            {
                'supplier_name': 'ITC Limited — Food & Staples Distribution',
                'product_name': 'Aashirvaad Superior MP Atta 5kg',
                'quantity': 80,
                'price': Decimal('240.00'),
                'days_ago': 7
            },
            # Tata Salt & Tea & Dal
            {
                'supplier_name': 'Tata Consumer Products Regional Hub',
                'product_name': 'Tata Salt Vacuum Evaporated 1kg',
                'quantity': 150,
                'price': Decimal('28.00'),
                'days_ago': 10
            },
            {
                'supplier_name': 'Tata Consumer Products Regional Hub',
                'product_name': 'Tata Tea Premium Desh Ki Chai 250g',
                'quantity': 60,
                'price': Decimal('110.00'),
                'days_ago': 12
            },
            {
                'supplier_name': 'Tata Consumer Products Regional Hub',
                'product_name': 'Tata Sampann Unpolished Toor Dal 1kg',
                'quantity': 75,
                'price': Decimal('72.00'),
                'days_ago': 8
            },
            # Adani Wilmar Oil
            {
                'supplier_name': 'Adani Wilmar Limited (Fortune Oils & Foods)',
                'product_name': 'Fortune Sunlite Refined Sunflower Oil 1L',
                'quantity': 60,
                'price': Decimal('165.00'),
                'days_ago': 6
            },
            # Britannia Good Day
            {
                'supplier_name': 'Britannia Industries Sanand Logistics Hub',
                'product_name': 'Britannia Good Day Cashew Cookies 100g',
                'quantity': 120,
                'price': Decimal('32.00'),
                'days_ago': 4
            },
            # Nestle Maggi
            {
                'supplier_name': 'Nestle India Western Distribution Centre',
                'product_name': 'Maggi 2-Minute Masala Instant Noodles 280g',
                'quantity': 120,
                'price': Decimal('34.00'),
                'days_ago': 3
            },
            # HUL Detergent
            {
                'supplier_name': 'Hindustan Unilever Distribution Depot',
                'product_name': 'Surf Excel Easy Wash Detergent Powder 1kg',
                'quantity': 70,
                'price': Decimal('135.00'),
                'days_ago': 9
            }
        ]

        for pdata in purchases_data:
            supplier_id = supplier_map.get(pdata['supplier_name'])
            if not supplier_id:
                sup = Supplier.query.filter_by(name=pdata['supplier_name']).first()
                if sup:
                    supplier_id = sup.id
            
            product = Product.query.filter_by(name=pdata['product_name']).first()
            if supplier_id and product:
                total_cost = pdata['price'] * pdata['quantity']
                purchase = Purchase(
                    supplier_id=supplier_id,
                    product_id=product.id,
                    quantity=pdata['quantity'],
                    purchase_price=pdata['price'],
                    total_cost=total_cost,
                    purchase_date=now - timedelta(days=pdata['days_ago'])
                )
                db.session.add(purchase)
        db.session.commit()
