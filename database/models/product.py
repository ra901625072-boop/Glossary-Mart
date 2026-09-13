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
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    """Product model for inventory management"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), index=True)
    cost_price = db.Column(Numeric(10, 2), nullable=False)
    selling_price = db.Column(Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    minimum_stock_alert = db.Column(db.Integer, default=10)
    supplier_name = db.Column(db.String(100))
    hsn_code = db.Column(db.String(20), nullable=True)
    gst_rate = db.Column(Numeric(5, 2), default=5.0)
    image_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint('stock_quantity >= 0', name='ck_product_stock_non_negative'),
    )
    
    # Relationship with sales and purchases
    sales = db.relationship('Sale', backref='product', lazy=True, cascade='all, delete-orphan')
    purchases = db.relationship('Purchase', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

    def to_dict(self, is_admin=False):
        """Convert product to dictionary (redacting wholesale metrics for non-admins)"""
        data = {
            'id': self.id,
            'name': self.name,
            'category': self.category_rel.name if self.category_rel else 'Uncategorized',
            'category_name': self.category_rel.name if self.category_rel else 'Uncategorized',
            'category_id': self.category_id,
            'selling_price': float(self.selling_price),
            'stock_quantity': self.stock_quantity,
            'image_path': self.image_path,
            'average_rating': float(self.average_rating),
            'reviews_count': len(self.reviews),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'hsn_code': self.hsn_code or '1904',
            'gst_rate': float(self.gst_rate) if self.gst_rate is not None else 5.0
        }
        if is_admin:
            data['cost_price'] = float(self.cost_price)
            data['profit_margin'] = float(self.profit_margin)
            data['minimum_stock_alert'] = self.minimum_stock_alert
            data['supplier_name'] = self.supplier_name
        return data


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
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Review {self.id} - Product {self.product_id}>'


class PosBill(db.Model):
    """Point of Sale (POS) Counter Invoice Master Model"""
    __tablename__ = 'pos_bills'

    id = db.Column(db.Integer, primary_key=True)
    bill_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(100), default='Walk-in')
    customer_phone = db.Column(db.String(20))
    subtotal = db.Column(Numeric(10, 2), nullable=False)
    discount_amount = db.Column(Numeric(10, 2), default=0.0)
    tax_amount = db.Column(Numeric(10, 2), default=0.0)
    total_amount = db.Column(Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(30), default='Cash')  # Cash, UPI, Card
    cashier_name = db.Column(db.String(100), default='Administrator')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    sales = db.relationship('Sale', backref='bill_rel', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'bill_number': self.bill_number,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone or '',
            'subtotal': float(self.subtotal) if self.subtotal is not None else 0.0,
            'discount_amount': float(self.discount_amount) if self.discount_amount is not None else 0.0,
            'tax_amount': float(self.tax_amount) if self.tax_amount is not None else 0.0,
            'total_amount': float(self.total_amount) if self.total_amount is not None else 0.0,
            'payment_method': self.payment_method,
            'cashier_name': self.cashier_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'items_count': len(self.sales) if self.sales else 0
        }

    def __repr__(self):
        return f'<PosBill {self.bill_number} - ₹{self.total_amount}>'


class Sale(db.Model):
    """Sale model for transaction records (Admin sales)"""
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('pos_bills.id'), nullable=True, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(Numeric(10, 2), nullable=False)
    profit = db.Column(Numeric(10, 2), nullable=False)
    sale_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Sale {self.id} - {self.product.name if self.product else "Unknown"}>'
