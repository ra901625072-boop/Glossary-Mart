from database.models import db
from database.models.product import Category

def seed_categories():
    """Seed authentic grocery categories, products, and reviews"""
    # 1. Ensure 8 Real Categories exist
    real_categories = [
        ('Fruits & Vegetables', 'Fresh farm produce, fruits, leafy greens and organic vegetables'),
        ('Dairy & Breakfast', 'Pure cow milk, butter, ghee, curd, paneer and breakfast spreads'),
        ('Staples & Grains', 'Stone-ground flours, premium basmati rice, lentils and cold-pressed oils'),
        ('Snacks & Biscuits', 'Cookies, healthy roasted snacks, dry fruits and chocolates'),
        ('Beverages', 'Premium teas, artisanal coffees, fruit juices and healthy drinks'),
        ('Personal Care', 'Natural soaps, oral care, shampoos and grooming essentials'),
        ('Household', 'Detergents, surface cleaners, dishwash and kitchen essentials'),
        ('Masala & Spices', 'Pure hand-pounded spices, rock salt, turmeric and whole seeds')
    ]
    
    cat_map = {}
    for cat_name, cat_desc in real_categories:
        cat = Category.query.filter_by(name=cat_name).first()
        if not cat:
            cat = Category(name=cat_name, description=cat_desc)
            db.session.add(cat)
            db.session.flush()
        cat_map[cat_name] = cat.id
    db.session.commit()
    
    return cat_map
