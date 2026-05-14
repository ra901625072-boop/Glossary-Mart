from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Numeric
from . import db

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
    supplier_name = db.Column(db.String(100))
    image_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint('stock_quantity >= 0', name='ck_product_stock_non_negative'),
    )
    
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
