from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import Numeric
from werkzeug.security import check_password_hash, generate_password_hash
from . import db

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


class ActivityLog(db.Model):
    """Audit log for critical admin actions"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)  # e.g. 'DELETE_PRODUCT', 'UPDATE_ORDER_STATUS'
    entity_type = db.Column(db.String(50))               # e.g. 'Product', 'Order'
    entity_id = db.Column(db.Integer)                    # PK of the affected row
    details = db.Column(db.Text)                         # JSON or human-readable summary
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))

    def __repr__(self):
        return f'<ActivityLog {self.action} on {self.entity_type}#{self.entity_id}>'
