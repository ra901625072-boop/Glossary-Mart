"""
Authentic administrator, customer accounts, and product reviews seed data.
"""
from werkzeug.security import generate_password_hash
from database.models import db
from database.models.user import User
from database.models.product import Product, Review


def create_admin(app):
    """Create default admin user from config"""
    admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
    if not admin:
        admin = User(
            username=app.config['ADMIN_USERNAME'],
            email='admin@mart.com',
            password_hash=generate_password_hash(app.config['ADMIN_PASSWORD']),
            role='admin',
            full_name='Administrator — Jay Goga Mart'
        )
        db.session.add(admin)
        db.session.commit()
        app.logger.info(f"Admin user created: {app.config['ADMIN_USERNAME']}")


def create_customer(app):
    """Create verified local customer accounts and genuine product reviews"""
    customers_data = [
        {
            'username': 'customer',
            'email': 'customer@mart.com',
            'password': 'customer123',
            'full_name': 'Priya Patel (Verified Patron)',
            'phone': '+91 98251 22334',
            'address': 'B-12, Radhe Shyam Residency, Pali Road, Mehsana, Gujarat 384002'
        },
        {
            'username': 'rahul_sharma',
            'email': 'rahul.sharma@gmail.com',
            'password': 'customer123',
            'full_name': 'Rahul Sharma',
            'phone': '+91 98765 43210',
            'address': 'Flat 402, Shivam Heights, Station Road, Unjha, Gujarat 384170'
        },
        {
            'username': 'amit_choudhary',
            'email': 'amit.choudhary@yahoo.com',
            'password': 'customer123',
            'full_name': 'Amit Choudhary',
            'phone': '+91 97240 55667',
            'address': 'Near Bus Stand, Market Yard, Pali, Gujarat 384260'
        },
        {
            'username': 'ramesh_bhai',
            'email': 'rameshbhai.patel@gmail.com',
            'password': 'customer123',
            'full_name': 'Ramesh Bhai Patel',
            'phone': '+91 99090 77889',
            'address': 'Shop 8, Main Bazar, Unjha, Mehsana, Gujarat 384170'
        }
    ]

    for cdata in customers_data:
        cust = User.query.filter_by(username=cdata['username']).first()
        if not cust:
            cust = User(
                username=cdata['username'],
                email=cdata['email'],
                password_hash=generate_password_hash(cdata['password']),
                role='customer',
                full_name=cdata['full_name'],
                phone=cdata['phone'],
                address=cdata['address'],
                is_verified=True
            )
            db.session.add(cust)
        else:
            if not cust.is_verified:
                cust.is_verified = True
            if not cust.full_name or cust.full_name == 'Priya S. (Verified Patron)':
                cust.full_name = cdata['full_name']
                cust.phone = cdata['phone']
                cust.address = cdata['address']
    db.session.commit()

    # Seed genuine customer reviews
    if Review.query.count() < 8:
        primary_customer = User.query.filter_by(username='customer').first()
        reviews_data = [
            ('Aashirvaad Superior MP Atta 5kg', 5, "Very fresh chakki atta. Rotis turn out super soft every time!"),
            ('Amul Taaza Fresh Toned Milk 1L', 5, "Daily morning fresh delivery is on time. Amul quality is always reliable."),
            ('Tata Tea Premium Desh Ki Chai 250g', 5, "Strong aroma and great kadak taste. Our family's go-to tea."),
            ('Tata Salt Vacuum Evaporated 1kg', 5, "Desh ka namak, pure and fine grain. Genuine product."),
            ('Fortune Sunlite Refined Sunflower Oil 1L', 4, "Light cooking oil, doesn't absorb too much in deep frying."),
            ('Maggi 2-Minute Masala Instant Noodles 280g', 5, "Instant snack for late evenings. Fresh packaging with long expiry."),
            ('Britannia Good Day Cashew Cookies 100g', 5, "Crispy and full of cashew nuts. Kids love it with evening milk."),
            ('Dabur Red Ayurvedic Toothpaste 300g', 5, "Authentic Ayurvedic formula. Kept teeth and gums healthy for years.")
        ]

        for prod_name, rating, comment in reviews_data:
            prod = Product.query.filter_by(name=prod_name).first()
            if prod:
                existing = Review.query.filter_by(product_id=prod.id, user_id=primary_customer.id).first()
                if not existing:
                    db.session.add(Review(
                        product_id=prod.id,
                        user_id=primary_customer.id,
                        rating=rating,
                        comment=comment
                    ))
        db.session.commit()
