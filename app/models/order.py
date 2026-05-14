from datetime import datetime, timezone
from sqlalchemy import Numeric, UniqueConstraint
from . import db

class Cart(db.Model):
    """Shopping cart model for customer orders"""
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_cart_user_product'),
    )

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
    payment_method = db.Column(db.String(50), default='COD')  # COD, UPI, CARD, UDHAR
    payment_status = db.Column(db.String(20), default='Pending')  # Pending, Paid, Failed, Refunded
    order_status = db.Column(db.String(30), default='Pending')  # Pending, Processing, Packed, Out for Delivery, Delivered, Cancelled, Returned
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


class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    product = db.relationship('Product', backref='wishlisted_by')

    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_wishlist_user_product'),
    )
