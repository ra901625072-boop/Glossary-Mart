from app import app
from models import db, Product

with app.app_context():
    products = Product.query.filter(Product.name.like('%Advance%')).all()
    for p in products:
        print(f"ID: {p.id}, Name: {p.name}, Image: {p.image_path}")
    if not products:
        print("No product found with 'Advance' in name.")
