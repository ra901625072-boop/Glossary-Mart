from decimal import Decimal
from database.models import db
from database.models.product import Product

def seed_products(cat_map):
    """Seed Real FMCG Products if none exist"""
    if Product.query.count() == 0:
        real_products = [
            {
                'name': 'Aashirvaad Superior MP Atta 5kg',
                'category_name': 'Staples & Grains',
                'cost_price': Decimal('240.00'),
                'selling_price': Decimal('279.00'),
                'stock_quantity': 50,
                'minimum_stock_alert': 10,
                'supplier_name': 'ITC Limited',
                'image_path': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Tata Salt Vacuum Evaporated 1kg',
                'category_name': 'Masala & Spices',
                'cost_price': Decimal('28.00'),
                'selling_price': Decimal('36.00'),
                'stock_quantity': 100,
                'minimum_stock_alert': 15,
                'supplier_name': 'Tata Consumer Products',
                'image_path': 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Amul Taaza Fresh Toned Milk 1L',
                'category_name': 'Dairy & Breakfast',
                'cost_price': Decimal('48.00'),
                'selling_price': Decimal('56.00'),
                'stock_quantity': 60,
                'minimum_stock_alert': 12,
                'supplier_name': 'GCMMF Amul Dairy',
                'image_path': 'https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Maggi 2-Minute Masala Instant Noodles 280g',
                'category_name': 'Snacks & Biscuits',
                'cost_price': Decimal('34.00'),
                'selling_price': Decimal('42.00'),
                'stock_quantity': 80,
                'minimum_stock_alert': 15,
                'supplier_name': 'Nestle India',
                'image_path': 'https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Tata Tea Premium Desh Ki Chai 250g',
                'category_name': 'Beverages',
                'cost_price': Decimal('110.00'),
                'selling_price': Decimal('132.00'),
                'stock_quantity': 45,
                'minimum_stock_alert': 10,
                'supplier_name': 'Tata Consumer Products',
                'image_path': 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Cadbury Dairy Milk Silk Chocolate 120g',
                'category_name': 'Snacks & Biscuits',
                'cost_price': Decimal('80.00'),
                'selling_price': Decimal('98.00'),
                'stock_quantity': 75,
                'minimum_stock_alert': 10,
                'supplier_name': 'Mondelez India',
                'image_path': 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Fortune Sunlite Refined Sunflower Oil 1L',
                'category_name': 'Staples & Grains',
                'cost_price': Decimal('165.00'),
                'selling_price': Decimal('199.00'),
                'stock_quantity': 45,
                'minimum_stock_alert': 10,
                'supplier_name': 'Adani Wilmar',
                'image_path': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Amul Pasteurised Salted Butter 500g',
                'category_name': 'Dairy & Breakfast',
                'cost_price': Decimal('125.00'),
                'selling_price': Decimal('145.00'),
                'stock_quantity': 50,
                'minimum_stock_alert': 10,
                'supplier_name': 'GCMMF Amul Dairy',
                'image_path': 'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Britannia Good Day Cashew Cookies 100g',
                'category_name': 'Snacks & Biscuits',
                'cost_price': Decimal('32.00'),
                'selling_price': Decimal('40.00'),
                'stock_quantity': 90,
                'minimum_stock_alert': 15,
                'supplier_name': 'Britannia Industries',
                'image_path': 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Tata Sampann Unpolished Toor Dal 1kg',
                'category_name': 'Staples & Grains',
                'cost_price': Decimal('72.00'),
                'selling_price': Decimal('89.00'),
                'stock_quantity': 60,
                'minimum_stock_alert': 12,
                'supplier_name': 'Tata Consumer Products',
                'image_path': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Surf Excel Easy Wash Detergent Powder 1kg',
                'category_name': 'Household',
                'cost_price': Decimal('135.00'),
                'selling_price': Decimal('165.00'),
                'stock_quantity': 55,
                'minimum_stock_alert': 10,
                'supplier_name': 'Hindustan Unilever',
                'image_path': 'https://images.unsplash.com/photo-1583947215259-38e31be8751f?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Harpic Power Plus Toilet Cleaner 500ml',
                'category_name': 'Household',
                'cost_price': Decimal('78.00'),
                'selling_price': Decimal('99.00'),
                'stock_quantity': 40,
                'minimum_stock_alert': 10,
                'supplier_name': 'Reckitt Benckiser',
                'image_path': 'https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Fresh Farm Crisp Organic Tomatoes 1kg',
                'category_name': 'Fruits & Vegetables',
                'cost_price': Decimal('25.00'),
                'selling_price': Decimal('35.00'),
                'stock_quantity': 50,
                'minimum_stock_alert': 10,
                'supplier_name': 'Gujarat Krishi Mandi',
                'image_path': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Fresh Farm Green Spinach (Palak) 250g',
                'category_name': 'Fruits & Vegetables',
                'cost_price': Decimal('15.00'),
                'selling_price': Decimal('22.00'),
                'stock_quantity': 30,
                'minimum_stock_alert': 5,
                'supplier_name': 'Gujarat Krishi Mandi',
                'image_path': 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Ratnagiri Alphonso Mangoes (1 Dozen)',
                'category_name': 'Fruits & Vegetables',
                'cost_price': Decimal('450.00'),
                'selling_price': Decimal('599.00'),
                'stock_quantity': 25,
                'minimum_stock_alert': 5,
                'supplier_name': 'Konkan Agro Farm',
                'image_path': 'https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&w=400&q=80'
            },
            {
                'name': 'Dabur Red Ayurvedic Toothpaste 300g',
                'category_name': 'Personal Care',
                'cost_price': Decimal('115.00'),
                'selling_price': Decimal('140.00'),
                'stock_quantity': 45,
                'minimum_stock_alert': 8,
                'supplier_name': 'Dabur India',
                'image_path': 'https://images.unsplash.com/photo-1559650656-5d1d42e99e69?auto=format&fit=crop&w=400&q=80'
            }
        ]
        for pdata in real_products:
            p = Product(
                name=pdata['name'],
                category_id=cat_map[pdata['category_name']],
                cost_price=pdata['cost_price'],
                selling_price=pdata['selling_price'],
                stock_quantity=pdata['stock_quantity'],
                minimum_stock_alert=pdata['minimum_stock_alert'],
                supplier_name=pdata['supplier_name'],
                image_path=pdata['image_path'],
                is_active=True
            )
            db.session.add(p)
        db.session.commit()
