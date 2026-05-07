import random

from app import create_app
from models import Category, Product, db

CATEGORIES = [
    'Vegetables', 'Fruits', 'Dairy', 'Spices', 'Household',
    'Grains & Flour', 'Oils & Ghee', 'Personal Care', 'Pulses', 'Snacks & Beverages'
]

PRODUCT_TEMPLATES = {
    'Vegetables': ['Potato', 'Onion', 'Tomato', 'Cabbage', 'Carrot', 'Spinach', 'Brinjal', 'Capsicum', 'Cauliflower', 'Green Peas', 'Lady Finger', 'Bottle Gourd'],
    'Fruits': ['Apple', 'Banana', 'Mango', 'Orange', 'Grapes', 'Papaya', 'Watermelon', 'Pomegranate', 'Guava', 'Pineapple', 'Kiwi'],
    'Dairy': ['Milk', 'Butter', 'Cheese', 'Paneer', 'Yogurt', 'Ghee', 'Condensed Milk', 'Fresh Cream', 'Buttermilk'],
    'Spices': ['Turmeric Powder', 'Red Chilli Powder', 'Coriander Powder', 'Cumin Seeds', 'Black Pepper', 'Garam Masala', 'Cardamom', 'Cinnamon', 'Cloves'],
    'Household': ['Dishwash Liquid', 'Detergent Powder', 'Floor Cleaner', 'Toilet Cleaner', 'Garbage Bags', 'Room Freshener', 'Tissue Paper'],
    'Grains & Flour': ['Wheat Flour', 'Rice', 'Maida', 'Besan', 'Suji', 'Poha', 'Dalia', 'Oats', 'Bajra Flour'],
    'Oils & Ghee': ['Mustard Oil', 'Sunflower Oil', 'Groundnut Oil', 'Olive Oil', 'Desi Ghee', 'Coconut Oil'],
    'Personal Care': ['Bathing Soap', 'Shampoo', 'Toothpaste', 'Hair Oil', 'Body Lotion', 'Face Wash', 'Deodorant', 'Hand Wash'],
    'Pulses': ['Toor Dal', 'Chana Dal', 'Moong Dal', 'Urad Dal', 'Rajma', 'Kabuli Chana', 'Masoor Dal', 'Black Chana'],
    'Snacks & Beverages': ['Tea', 'Coffee', 'Biscuits', 'Namkeen', 'Chips', 'Fruit Juice', 'Cold Drink', 'Chocolate', 'Noodles']
}

app = create_app()

def seed_products():
    with app.app_context():
        # Ensure categories exist
        cats = {}
        for cat_name in CATEGORIES:
            cat = Category.query.filter_by(name=cat_name).first()
            if not cat:
                cat = Category(name=cat_name)
                db.session.add(cat)
                db.session.commit()
            cats[cat_name] = cat.id

        # Generate 100 products
        products_added = 0
        total_target = 100
        
        while products_added < total_target:
            cat_name = random.choice(CATEGORIES)
            base_name = random.choice(PRODUCT_TEMPLATES[cat_name])
            
            # Make the name unique if we re-use templates
            modifier = random.choice(['Premium', 'Organic', 'Export Quality', 'Farm Fresh', 'Standard', 'Local', 'Special'])
            qty_modifier = random.choice(['500g', '1kg', '250g', '1L', '500ml', 'Pack of 1', 'Family Pack'])
            
            full_name = f"{modifier} {base_name} {qty_modifier}"
            
            # Check if product already exists to avoid exact duplicates
            if not Product.query.filter_by(name=full_name).first():
                cost_price = round(random.uniform(20.0, 500.0), 2)
                margin = random.uniform(1.1, 1.4) # 10% to 40% margin
                selling_price = round(cost_price * margin, 2)
                stock_quantity = random.randint(10, 150)
                
                new_product = Product(
                    name=full_name,
                    category=cat_name, # Legacy
                    category_id=cats[cat_name],
                    cost_price=cost_price,
                    selling_price=selling_price,
                    stock_quantity=stock_quantity,
                    is_active=True
                )
                db.session.add(new_product)
                products_added += 1
                
                if products_added % 20 == 0:
                    db.session.commit()
                    print(f"Added {products_added} products...")

        db.session.commit()
        print(f"Successfully added {products_added} products to the store!")

if __name__ == '__main__':
    seed_products()
