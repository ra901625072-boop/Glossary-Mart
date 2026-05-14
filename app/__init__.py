import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from flask import Flask
from .core.config import Config
from .core.extensions import limiter
from .core.middleware import init_middleware
from .core.hooks import init_hooks
from .core.context_processors import init_context_processors
from .models import db, User, Category, Product

# Initialize legacy extensions at module level (to avoid breaking wsgi.py imports if it expects them here)
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
mail = Mail()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    """Application factory"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    app.config.from_object(config_class)

    # Configure Logging
    setup_logging(app)

    # Initialize Extensions
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
        return db.session.get(User, int(user_id))

    # Initialize Core Components
    init_middleware(app)
    init_hooks(app)
    init_context_processors(app)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register Blueprints
    register_blueprints(app)

    # Health Check Route
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200

    return app

def setup_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        # Stream to stdout for production (Render/Docker)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)

        # Rotating File Handler
        if not os.path.exists('logs'):
            try: os.mkdir('logs')
            except: pass
        
        if os.path.exists('logs'):
            file_handler = RotatingFileHandler('logs/mart.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Jay Goga Mart startup')

def register_blueprints(app):
    """Register application blueprints"""
    from .routes import admin_bp, auth_bp, customer_bp
    from .routes.security import security_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(security_bp)

def init_db(app):
    """Initialize database and seed data"""
    with app.app_context():
        if not app.config.get('SKIP_DB_CREATE', False):
            try:
                db.create_all()
                app.logger.info("Database tables verified/created.")
            except Exception as e:
                app.logger.error(f"Database creation failed: {e}")
        
        # Seed Categories and Migrate Products
        seed_data(app)

        # Create Default Admin
        create_admin(app)

def seed_data(app):
    """Seed initial data and migrate legacy product categories"""
    from .models.product import Category, Product
    
    # Ensure default categories exist
    existing_cat_strings = db.session.query(Product.category).distinct().all()
    existing_cat_strings = [c[0] for c in existing_cat_strings if c[0]]
    if not existing_cat_strings:
        existing_cat_strings = ['Vegetables', 'Fruits', 'Dairy', 'Spices', 'Household']
        
    for cat_name in existing_cat_strings:
        if not db.session.query(Category).filter_by(name=cat_name).first():
            db.session.add(Category(name=cat_name))
    db.session.commit()
    
    # Migrate products to use category_id
    products_to_migrate = Product.query.filter(Product.category_id == None).all()
    for p in products_to_migrate:
        if p.category:
            cat = Category.query.filter_by(name=p.category).first()
            if cat: p.category_id = cat.id
    db.session.commit()

def create_admin(app):
    """Create default admin user from config"""
    from werkzeug.security import generate_password_hash
    admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
    if not admin:
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

# Global app instance for WSGI servers
app = create_app()

with app.app_context():
    init_db(app)
