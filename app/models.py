from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model for authentication (Admin and Customer)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='customer')  # 'admin' or 'customer'
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    credit = db.Column(Numeric(10, 2), default=0) # Track unpaid balances (Udhar)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    reset_token = db.Column(db.String(100))
    two_factor_secret = db.Column(db.String(32))
    two_factor_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    cart_items = db.relationship('Cart', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    """Category model for product grouping"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship with products
    products = db.relationship('Product', backref='category_rel', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    """Product model for inventory management"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # Keep for legacy/migration
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), index=True)
    cost_price = db.Column(Numeric(10, 2), nullable=False)
    selling_price = db.Column(Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    minimum_stock_alert = db.Column(db.Integer, default=10)
    supplier_name = db.Column(db.String(100))  # Optional text or link to Supplier model
    image_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship with sales and purchases
    sales = db.relationship('Sale', backref='product', lazy=True, cascade='all, delete-orphan')
    purchases = db.relationship('Purchase', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    @property
    def average_rating(self):
        """Calculate average rating for this product"""
        if not self.reviews:
            return 0
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.selling_price and self.selling_price > 0:
            margin = ((self.selling_price - self.cost_price) / self.selling_price) * 100
            from decimal import Decimal
            return Decimal(str(margin)).quantize(Decimal('0.1'))
        return 0

    def to_dict(self):
        """Convert product to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category_rel.name if self.category_rel else self.category,
            'category_id': self.category_id,
            'cost_price': float(self.cost_price),
            'selling_price': float(self.selling_price),
            'stock_quantity': self.stock_quantity,
            'minimum_stock_alert': self.minimum_stock_alert,
            'supplier_name': self.supplier_name,
            'image_path': self.image_path,
            'profit_margin': float(self.profit_margin),
            'average_rating': float(self.average_rating),
            'reviews_count': len(self.reviews),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Review(db.Model):
    """Product review model"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    product = db.relationship('Product', backref=db.backref('reviews', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    
    def __repr__(self):
        return f'<Review {self.id} - Product {self.product_id}>'


class Sale(db.Model):
    """Sale model for transaction records (Admin sales)"""
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(Numeric(10, 2), nullable=False)
    profit = db.Column(Numeric(10, 2), nullable=False)
    sale_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    def __repr__(self):
        return f'<Sale {self.id} - {self.product.name if self.product else "Unknown"}>'


class Cart(db.Model):
    """Shopping cart model for customer orders"""
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship with product
    product = db.relationship('Product', backref='cart_items')
    
    def __repr__(self):
        return f'<Cart {self.id} - User {self.user_id}>'
    
    @property
    def subtotal(self):
        """Calculate subtotal for this cart item"""
        return self.product.selling_price * self.quantity if self.product else 0
    
    def to_dict(self):
        """Convert cart item to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown',
            'product_price': self.product.selling_price if self.product else 0,
            'product_image': self.product.image_path if self.product else None,
            'quantity': self.quantity,
            'subtotal': self.subtotal,
            'added_at': self.added_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Order(db.Model):
    """Customer order model"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    total_amount = db.Column(Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), default='COD')  # COD, Online
    payment_status = db.Column(db.String(20), default='Pending')  # Pending, Paid
    order_status = db.Column(db.String(20), default='Pending')  # Pending, Processing, Shipped, Delivered, Cancelled
    shipping_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationship with order items
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.id} - User {self.user_id}>'
    
    @property
    def total_profit(self):
        """Calculate total profit from all order items"""
        return sum(item.profit for item in self.order_items)
    
    def to_dict(self):
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': self.total_amount,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'order_status': self.order_status,
            'shipping_address': self.shipping_address,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'items_count': len(self.order_items)
        }


class OrderItem(db.Model):
    """Order item model for individual products in an order"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)  # Selling price at time of order
    profit = db.Column(Numeric(10, 2), nullable=False)  # Calculated profit
    
    # Relationship with product
    product = db.relationship('Product', backref='order_items')
    
    def __repr__(self):
        return f'<OrderItem {self.id} - Order {self.order_id}>'
    
    @property
    def subtotal(self):
        """Calculate subtotal for this order item"""
        return self.price * self.quantity
    
    def to_dict(self):
        """Convert order item to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Deleted Product',
            'quantity': self.quantity,
            'price': self.price,
            'profit': self.profit,
            'subtotal': self.subtotal
        }

class Supplier(db.Model):
    """Supplier model for tracking stock providers"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    purchases = db.relationship('Purchase', backref='supplier', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

class Purchase(db.Model):
    """Purchase model for restocking inventory"""
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchase_price = db.Column(Numeric(10, 2), nullable=False)
    total_cost = db.Column(Numeric(10, 2), nullable=False)
    purchase_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<Purchase {self.id} - Product {self.product_id}>'



class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    product = db.relationship('Product', backref='wishlisted_by')

class Coupon(db.Model):
    __tablename__ = 'coupons'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), default='percentage')
    value = db.Column(Numeric(10, 2), nullable=False)
    min_order_amount = db.Column(Numeric(10, 2), default=0)
    valid_until = db.Column(db.DateTime)
    usage_limit = db.Column(db.Integer, default=100)
    times_used = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
