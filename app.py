import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash

from config import Config
from extensions import limiter
from models import Cart, User, db

# Initialize extensions
csrf = CSRFProtect()
mail = Mail()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/mart.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Jay Goga Mart startup')

    # Initialize extensions with app
    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.customer_login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register Blueprints
    from routes import admin_bp, auth_bp, customer_bp
    from routes.security import security_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(security_bp)

    # Context processor to add cart count to all templates
    @app.context_processor
    def inject_cart_count():
        """Make cart count available in all templates"""
        cart_count = 0
        from flask import session
        from flask_login import current_user
        if current_user.is_authenticated and current_user.role == 'customer':
            cart_count = Cart.query.filter_by(user_id=current_user.id).count()
        elif not current_user.is_authenticated:
            cart_count = len(session.get('cart', {}))
        return {'cart_count': cart_count}

    return app

app = create_app()

def init_db():
    """Initialize database and create default admin user"""
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Add new columns if they do not exist
        from sqlalchemy import text
        try:
            db.session.execute(text("ALTER TABLE products ADD COLUMN minimum_stock_alert INTEGER DEFAULT 10"))
        except:
            pass
        try:
            db.session.execute(text("ALTER TABLE products ADD COLUMN supplier_name VARCHAR(100)"))
        except:
            pass
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"))
        except:
            pass
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN verification_token VARCHAR(100)"))
        except:
            pass
        db.session.commit()
        
        # Set is_verified=True for all existing users (Fix for legacy accounts)
        db.session.execute(text("UPDATE users SET is_verified = 1 WHERE is_verified IS NULL OR is_verified = 0"))
        db.session.commit()
        
        # Seed Categories and Migrate Products
        from models import Category, Product

        # Get unique category strings from existing products
        existing_cat_strings = db.session.query(Product.category).distinct().all()
        existing_cat_strings = [c[0] for c in existing_cat_strings if c[0]]
        
        # Add default categories if empty store
        if not existing_cat_strings:
            existing_cat_strings = ['Vegetables', 'Fruits', 'Dairy', 'Spices', 'Household']
            
        for cat_name in existing_cat_strings:
            if not Category.query.filter_by(name=cat_name).first():
                new_cat = Category(name=cat_name)
                db.session.add(new_cat)
        db.session.commit()
        
        # Migrate products to use category_id
        products_to_migrate = Product.query.filter(Product.category_id == None).all()
        for p in products_to_migrate:
            if p.category:
                cat = Category.query.filter_by(name=p.category).first()
                if cat:
                    p.category_id = cat.id
        db.session.commit()

        # Check if admin user exists
        admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
        if not admin:
            # Create admin user
            admin = User(
                username=app.config['ADMIN_USERNAME'],
                email='admin@mart.com',
                password_hash=generate_password_hash(app.config['ADMIN_PASSWORD']),
                role='admin',
                full_name='Administrator'
            )
            db.session.add(admin)
            db.session.commit()
            app.logger.info(f"Admin user created: {app.config['ADMIN_USERNAME']}")

if __name__ == '__main__':
    init_db()
    print("\n" + "="*50)
    print("Jay Goga Kirana Store Management System")
    print("="*50)
    print(f"Admin Username: {app.config['ADMIN_USERNAME']}")
    print(f"Admin Password: {app.config['ADMIN_PASSWORD']}")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
